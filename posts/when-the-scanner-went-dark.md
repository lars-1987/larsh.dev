---
title: "When the scanner went dark"
subtitle: "A postmortem on Renew's product scanner: three overlapping root causes, one hard build constraint, and why the real fix was to send less, not restore more."
date: "2026-08-24"
tags: ["postmortem", "ios", "architecture", "on-device", "ocr"]
---

**Shipped in v1.0.2 (build 61) on 9 June 2026. Stable ever since: no failures.**

Renew's product scanner does one thing: you photograph a skincare product and it hands back structured data, including the full INCI ingredients list. Then one day it stopped working entirely. Fixing it properly meant rebuilding how the feature worked, not just restoring it, and the replacement came out cheaper, faster, offline-capable, and sending less user data off the device.

What follows is the postmortem: how it broke, why the first two answers were both wrong, and why an outage turned out to be the best excuse to question the design.

## 1. The problem

**Symptom:** the scanner returned nothing. Not slow, not wrong: *no API calls were reaching Gemini at all.*

### Original architecture (what broke)

```diagram
[iPhone] capture up to 4 photos
   → compress on-device
   → base64 encode
   → Supabase Edge Function
   → Gemini vision model (multimodal)
   → structured JSON back
```

Every scan shipped four images to a multimodal model. That's the expensive, fragile way to do it: images cost orders of magnitude more tokens than text, and multimodal endpoints are where rate limits bite first.

### Diagnosis: three overlapping causes, not one

This is the part worth talking through. The first answer was wrong, and so was the second.

| # | Hypothesis | Verdict |
|---|---|---|
| 1 | Rate limiting (`429`) on `gemini-2.0-flash` | Real, but a symptom, not the cause |
| 2 | Model deprecation: the 2.5 family was being retired Jun–Jul 2026 | Real, and would have broken it regardless |
| 3 | **Google had moved to prepaid credits; the balance was depleted** | The actual root cause of the hard stop |

The `429`s looked like classic throttling, which sent me toward retry logic and backoff. That would have been a real fix for a problem I didn't have. The deprecation notice then looked like *the* answer: also true, also not why calls were failing that day. Only the billing change explained a **complete** stop rather than intermittent failure.

**Lesson worth articulating:** three plausible causes were simultaneously true. Stopping at the first correct-looking one would have produced a fix that didn't fix anything.

## 2. Options considered

Restoring the old path would have left every original weakness in place. So the question became: *does this feature need to send images to a paid API at all?*

| Option | Verdict |
|---|---|
| **A.** Restore as-is on a new key/model | Rejected: same cost profile, same fragility, same single point of failure |
| **B.** On-device OCR, then send **text** to Gemini | **Chosen** |
| **C.** Fully on-device (OCR + parsing, no LLM) | Rejected: OCR output is noisy and unordered; interpreting it into INCI names is exactly what an LLM is good at |

Option B splits the job along its natural seam: **reading pixels is a solved on-device problem; interpreting messy text is not.**

### Detour: ML Kit, and a hard constraint

First attempt at on-device OCR was **Google ML Kit**. It failed on a non-obvious constraint: no `arm64` simulator slice, so the app wouldn't build on the iOS Simulator at all.

That constraint was non-negotiable: development and testing happen on the simulator daily. A library that only works on physical devices imposes a permanent tax on every future change.

**Decision:** abandon ML Kit, use **Apple Vision** instead. It's a system framework, so there's no dependency to break, no architecture gaps, no cost, and it improves with every iOS release.

## 3. The solution

```diagram
[iPhone] capture up to 4 photos
   → Apple Vision OCR on-device (free, offline)
   → concatenate raw text
   → Supabase Edge Function
   → Gemini text-only model
   → structured JSON back
```

### Why this is better than what it replaced

- **Cost:** text prompts are a fraction of multimodal cost. Images never leave the device.
- **Speed:** no upload of four compressed images per scan.
- **Privacy:** photos stay on the phone; only extracted text is transmitted.
- **Resilience:** the expensive, rate-limited step now handles a fraction of the payload.
- **Offline capability:** the OCR half works with no connection.

## 4. Scope

**Added**

- `modules/text-recognizer/`: a local Expo native module wrapping Apple Vision
  - `ios/TextRecognizerModule.swift`: `VNRecognizeTextRequest`, `.accurate`, language correction on
  - `index.ts`: `recognizeText(uri): Promise<string>`
- `OCR_PROMPT` and a `mode: "ocr"` branch in the edge function
- Retry-on-`429`/`503` with exponential backoff
- Empty-OCR guard in the capture flow

**Changed**

- `supabase/functions/gemini-extract/index.ts`: model → `gemini-3.1-flash-lite`
- `src/screens/product/PhotoCaptureScreen.js`: OCR before the network call
- `src/services/gemini.js`: added `extractFromText()`

**Retained (deliberately)**

- The `photo` (vision) mode still exists in the edge function as a fallback path
- The `url` mode was hardened separately with server-side fetching

## 5. Implementation notes

### On-device OCR, per photo, failure-tolerant

```js
const ocrResults = await Promise.all(
  orderedUris.map((uri) => recognizeText(uri).catch(() => ''))
);
```

Each photo is OCR'd in parallel, and **a single failure can't kill the scan**: a bad photo yields `''` and the others still contribute. Photos are ordered deliberately (front first for brand and name, then the ingredients panel) so the text arrives in a sequence the model can reason about.

### Don't dead-end the user

```js
if (combinedText.replace(/\s/g, '').length < 15) {
  navigation.replace('ReviewProduct', {
    scrapedData: { photo_uris: photoUris, confidence: 'low' },
  });
  return;
}
```

If OCR finds essentially nothing (glare, blur, a matte black bottle), the app does **not** show an error. It forwards to the review screen with the photos attached so the user can type the details in. The failure mode is a manual-entry form, not a dead end.

This also avoids burning an API call on text that couldn't possibly parse.

### Retry only what's worth retrying

```js
const retryable = geminiResponse.status === 429 || geminiResponse.status === 503;
// backoff: 0.8s → 1.6s → 3.2s, max 3 retries
```

Only transient statuses retry. A `400` fails immediately rather than three times.

### Prompt engineering: tell the model the input is broken

The OCR prompt explicitly primes the model on the shape of its input:

> *"It will be noisy: words may be split, mis-recognised, out of order, or include stray characters. Use your knowledge of skincare products to interpret it."*

That single instruction is what makes the architecture viable: Vision's raw output is genuinely messy, and the model needs licence to interpret rather than transcribe. It's paired with a hard constraint in the same prompt:

> *"Do not guess or hallucinate ingredients."*

Interpret the noise, don't invent the content.

**K-beauty handling** (a large share of the catalogue): translate brand and product names to their established English names (이니스프리 → Innisfree), always prefer the Latin INCI names when both are printed, and **downgrade confidence** when only local-language ingredient names exist and translation was required.

## 6. Confidence reporting

Gemini returns a self-assessed `confidence: "high" | "medium" | "low"` on every extraction, and it drives real behaviour rather than being decorative.

**The model is instructed when to lower it:** the prompt names the specific condition (ingredients translated from a non-INCI local-language list) rather than leaving "confidence" to vibes.

**It surfaces to the user** on the review screen as a source badge:

```js
text: `Extracted from your photo${confidence === 'high' ? ' · High confidence' : ''}`
```

High and medium are stated explicitly; **low makes no claim at all** rather than advertising a weak result.

**It's persisted:** every product records `data_source` (`gemini_ocr` / `gemini_photo` / `gemini_url` / `catalogue` / `manual`), which makes extraction quality auditable after the fact and is what allowed the outcome analysis below.

**The design principle:** the user always lands on an editable review screen before anything is saved. The AI never writes directly to the database; it pre-fills a form. Confidence tells the user *how hard to check it*.

## 7. Outcome

**It has not failed since.** Shipped 9 June 2026; no Gemini outages in the roughly 11 weeks to 24 August, across a growing user base.

Catalogue entries created per month (every user contributes, regardless of tier):

| Month | Entries | With ingredients |
|---|---|---|
| Jun 2026 | 65 | 45 |
| Jul 2026 | 17 | 13 |
| Aug 2026 | 54 | 40 |

By `data_source` (**synced users only**: free-tier products stay on-device and never reach the server, so these understate real usage):

| Source | Products | Last seen |
|---|---|---|
| `gemini_url` | 61 | 4 Aug 2026 |
| `gemini_photo` (old vision path) | 41 | **21 May 2026** |
| `gemini_ocr` (new path) | 10 | 22 Aug 2026 |

The vision path stops dead in May and the OCR path takes over: the migration is visible in the data.

### Second-order benefit

Because extractions populate a **shared product catalogue**, each product's API cost is paid **once across the entire user base, ever**. A returning user re-adding 37 products later cost zero additional API calls; they all resolved from the catalogue.

## 8. Takeaways

1. **The first correct-looking answer was wrong, twice.** Three plausible causes were all simultaneously true, and only one explained the actual symptom. Distinguishing "this is real" from "this is *why*" was the whole diagnosis.
2. **An outage is a licence to question the design.** Restoring the old path was the fast fix. Asking *why are we sending images to a paid API at all* produced something cheaper, faster, more private and more resilient.
3. **Constraints eliminate options fast.** "It must build on the simulator" killed ML Kit in one test and pointed directly at a better dependency: a system framework that can't break.
4. **Design for the AI being wrong.** Empty-OCR routes to manual entry; individual photo failures degrade instead of aborting; nothing saves without human review; confidence is reported rather than assumed.
5. **Split the problem where the technologies are actually good.** OCR is a solved on-device problem. Interpreting noisy text into structured INCI data isn't. The fix was putting each half where it belonged.
