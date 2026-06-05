---
title: "The Bug That Only Existed in Spanish"
subtitle: "How browser auto-translation white-screened my app — and why I spent the first hour blaming an innocent PNG"
date: "2026-06-02"
tags: ["debugging", "react", "nextjs", "war-story"]
---

Every so often you get a bug that's a perfect little detective story: a misleading first clue, a suspect who turns out to be innocent, and a culprit who was hiding in plain sight the whole time. This is one of those. It also ends with me feeling slightly stupid, which I'm told is the sign of a good one.

## The crime scene

MetaStrip is the privacy tool I build and run — it strips metadata out of your files entirely in the browser, nothing ever uploaded. I have PostHog session recordings turned on so I can watch how real people actually use it, which is equal parts useful and humbling.

One afternoon I'm scrubbing through recordings and I catch this: a user drops a PNG in, hits "execute," and the **entire app vanishes** — replaced by the generic, deeply unhelpful:

> *Error de la aplicación: se ha producido una excepción del lado del cliente.*

If your Spanish is rusty: "Application error: a client-side exception has occurred." That's the stock message Next.js shows when an unhandled error escapes to the top of the tree and there's nothing to catch it. The whole page just... dies.

A user hit execute on a PNG and the app exploded. Cool. Cool cool cool.

## Suspect #1: the PNG processor (innocent)

The obvious suspect was my PNG metadata parser. I hand-rolled it — walk the PNG chunks, find the metadata ones (`tEXt`, `iTXt`, `zTXt`, `eXIf`, `tIME`), drop them, recompute the rest. Plenty of room for a malformed file to throw something nasty.

So I did the responsible thing and built a little fuzzing harness. Thirteen deliberately broken PNGs — truncated mid-chunk, a `tEXt` chunk with no null separator, a length field claiming the chunk was 2GB, an empty buffer, signature-and-nothing-else — fired through the *real* processor:

```ts
const cases: [string, Uint8Array][] = [
  ["minimal valid",        build(ihdr, idat, iend)],
  ["tEXt no null",         build(ihdr, chunk("tEXt", te("noNullByteHere")), idat, iend)],
  ["iTXt compressed-flag", build(ihdr, chunk("iTXt", weirdCompressedBytes), idat, iend)],
  ["truncated mid-chunk",  build(ihdr, idat).slice(0, -3)],
  ["huge length field",    pngWithBogus2GBChunkLength()],
  ["empty buffer",         new Uint8Array(0)],
  // …13 in total
];

for (const [name, bytes] of cases) {
  const file = new File([bytes], "t.png", { type: "image/png" });
  try {
    const r = await processPng(file, DEFAULT_STRIP_OPTIONS);
    console.log(`✅ ${name.padEnd(24)} found=${r.report.fieldsFound.length} ${r.error ?? ""}`);
  } catch (e) {
    console.log(`💥 ${name.padEnd(24)} THREW: ${(e as Error).message}`);
  }
}
```

I was hunting for `💥`. I got a column of `✅`. Every malformed input was handled gracefully. And — crucially — the processing call was *already wrapped in a try/catch*, so even if one had thrown, the worst case was a tidy "couldn't process this file" message, not a full-app detonation:

```ts
try {
  const result = await processFile(entry.file, options);
  // …show the cleaned file
} catch {
  // graceful per-file error — never a white screen
  setStatus(entry.id, "error", "Processing failed");
}
```

So the PNG was innocent. I'd spent an hour interrogating the wrong suspect while the real one sat quietly in the corner.

## The clue I'd been ignoring the whole time

The error message was in **Spanish**.

I'd clocked that immediately and immediately filed it under "user is in a Spanish-speaking country, neat" and moved on. Classic. The single most important clue in the entire case, and I treated it like flavour text.

Here's what I'd missed: Next.js doesn't ship a Spanish error page. My app is in English. The *only* way that error message renders in Spanish is if **the browser was translating the page in real time.** The user had Google Translate (or Chrome/Safari's built-in translation) running.

And that, it turns out, is the whole bug.

## Suspect #2: Google Translate (guilty)

Here's the thing about browser auto-translation that I knew abstractly but had never been bitten by: **it mutates your DOM out from under you.** To translate a page, the browser walks your text nodes, wraps them in `<font>` tags, and swaps the text in place — directly, on the live DOM.

This is what one of my terminal lines looks like before the translator gets to it:

```html
<!-- what React rendered, and what it thinks is still there -->
<span>stripping gps…</span>
```

And this is what Google Translate quietly turns it into:

```html
<!-- the text node React was tracking is now buried inside a <font> wrapper -->
<font style="vertical-align: inherit;">
  <font style="vertical-align: inherit;">quitando gps…</font>
</font>
```

React, meanwhile, is a control freak (affectionately). It keeps its own virtual copy of the DOM and assumes the real one matches. When state changes and it needs to update or remove that text node, it reaches for the exact node it remembers — a plain text node that is no longer a direct child of anything React recognises:

```ts
// roughly what React's commit phase does
parent.removeChild(theTextNodeIRemember);
//                  ^ the translator moved this inside a <font>,
//                    so it isn't a child of `parent` anymore
```

And the browser does the only thing it can:

```text
NotFoundError: Failed to execute 'removeChild' on 'Node':
The node to be removed is not a child of this node.
```

Unhandled. Straight to the top. White screen. In Spanish. (It's a famous React footgun — there's a [GitHub issue from 2016](https://github.com/facebook/react/issues/11538) with a small village's worth of people who've hit it. I'd just never been the one holding the bag.)

## Why *my* app, why *that* moment

The reason it fired right after "execute on a PNG" is the most satisfying part, because the PNG really was a total red herring.

MetaStrip's UI is a fake terminal, and the bit that runs after you hit execute is **aggressively animated**. A log of lines appears one by one on `setTimeout`. Status text flips from a spinner dot to "removed (3 fields)" to "clean." Per-field details stagger in. There's a clock ticking in the status bar. It is, in other words, a machine for rapidly creating, swapping, and destroying text nodes:

```tsx
// every one of these is a fresh text node for the translator to wrap
// and for React to later try to swap — i.e. a fresh chance to explode
{showResult
  ? <span className="text-success">removed ({n} fields)</span>
  : <span className="animate-pulse">●</span>}
```

A static marketing page might never trip it. My animated terminal trips it almost on purpose. The file type was irrelevant — any file would've done it. PNG just happened to be what the user dragged in.

## The fix: prevention *and* a parachute

I fixed it in two layers, because the bug taught me two separate lessons.

**Layer one — stop the translator touching the volatile bits.** The terminal is a live React surface; the translator has no business rewriting its nodes. Two attributes opt it out:

```tsx
// translate="no" (HTML standard) + notranslate (Google's class)
<div className="w-full max-w-5xl mx-auto notranslate" translate="no">
  <TerminalWindow>{/* the animated, node-churning terminal */}</TerminalWindow>
</div>
```

Now Google Translate skips the terminal entirely and leaves React's churning nodes alone. The blog, the FAQ, the marketing copy — all the actual *prose* a non-English speaker would want translated — stays fully translatable. Only the technical terminal UI ("stripping gps…", file names, a ticking clock) opts out, which, honestly, you didn't want machine-translated anyway.

**Layer two — admit the real defect was deeper.** Here's the uncomfortable bit: a single stray throw *anywhere* in my app could white-screen the whole thing, because I had **no error boundary at all.** Not one. The translation crash didn't create that vulnerability — it just walked through a door I'd left wide open.

So I added one. The interesting part is that it doesn't just catch — it recognises the specific failure mode and *recovers*:

```tsx
export class ErrorBoundary extends Component<Props, State> {
  state = { hasError: false, reloading: false };

  static getDerivedStateFromError(error: unknown) {
    // a stale JS chunk after a deploy? quietly reload instead of erroring
    return { hasError: true, reloading: isChunkLoadError(error) };
  }

  componentDidCatch(error: unknown) {
    if (isChunkLoadError(error)) reloadForStaleChunk(); // one-shot, loop-guarded
  }

  render() {
    if (!this.state.hasError) return this.props.children;
    if (this.state.reloading) return <Updating />;
    return <FriendlyFallback onReload={() => location.reload()} />;
  }
}
```

That, plus a Next.js `global-error.tsx` as the last line of defence so even an escapee shows something friendlier than raw Spanish-stack-trace energy. Prevention so the known bug can't fire, and a parachute so the *next* unknown one doesn't take the whole plane down.

## What I'd put on the whiteboard afterwards

- **The error message is data, not decoration.** That message was in Spanish for exactly one reason, and that reason *was the bug.* I looked straight at the answer and called it flavour text. Read the whole clue, including the parts that seem incidental.
- **Reproduce before you theorise.** Fuzzing the PNG processor "wasted" an hour, but it bought certainty: I *proved* the parser was innocent instead of guessing. Ruling a suspect out is real progress, even when it feels like a dead end.
- **"It crashes" and "it crashes the entire app" are different bugs.** The translation throw was bad. The fact that any throw could take down the whole page was *worse*, and it was my fault, and it had been lurking since day one. The visible bug was a gift — it made me find the invisible one.
- **Your weird UI choices have weird failure modes.** I built a heavily-animated fake terminal because it's fun. Fun has a bill, and sometimes it arrives as a DOM-reconciliation crash that only manifests in another language.

The bug is fixed. The app no longer cares whether you read it in English, Spanish, Portuguese, or anything else. And I now treat every unexpectedly-translated error message as a prime suspect rather than a fun fact.

Anyway. Back to building. There are more red herrings out there, and statistically, most of them are also my fault.
