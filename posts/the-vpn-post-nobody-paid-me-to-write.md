---
title: "The VPN Post Nobody Paid Me to Write"
subtitle: "No affiliate links, no 'top pick' that mysteriously pays the highest commission. Just what these things actually do, what they don't, and whether you need one."
date: "2026-06-09"
tags: ["privacy", "vpn", "security", "opinion"]
---

Try to research VPNs for five minutes and you'll notice something. Every article has a winner. The winner has a discount code. The discount code is an affiliate link. And the "winner" is, with suspicious regularity, whichever provider pays the reviewer the most per signup.

I have a security background and a privacy tool of my own to run, so people ask me which VPN to get. This post is my answer, and the only thing I get paid for writing it is the warm feeling of not having an affiliate dashboard. Nobody sponsored this. There are no links to click that make me money. If I recommend something it's because I'd use it, and if I tell you to skip something it's because I would.

Fair warning: my actual conclusion is that most people asking "which VPN should I buy" are asking the wrong question. We'll get there.

## What a VPN actually is

A VPN (virtual private network) does one genuinely useful thing: it takes all the traffic leaving your device, encrypts it, and routes it through a server somewhere else before it heads out to the wider internet. Two consequences follow from that.

First, whoever is between you and that server (the cafe wifi, the airport network, your ISP) sees encrypted noise going to one address instead of a readable list of everywhere you went. Second, the website on the other end sees the VPN server's IP and location, not yours.

That's it. That's the whole magic trick. Everything else a VPN company sells you is either a consequence of those two things or marketing built on top of them.

## Does it actually make you "private"? Or is it just a fancy location spoofer?

Here's the part the ads are cagey about. A VPN doesn't make you anonymous. It moves your trust.

Without a VPN, your ISP can see the domains you connect to. With a VPN, your ISP can't, but your VPN provider now can. You haven't deleted the watcher, you've swapped your ISP for a company in (hopefully) a friendlier country whose entire business model is promising not to look. Whether that's an upgrade depends entirely on whether you trust that company more than your ISP. Sometimes you genuinely do. But it's a trust transfer, not a cloak of invisibility.

And for a huge slice of real-world use, the honest description of a VPN is "a really good location spoofer." Want to watch the UK Netflix catalogue from Melbourne? A VPN is exactly the right tool. Want to look like you're in the US so a website stops geo-blocking you? Perfect. That use case is legitimate and common and there's nothing embarrassing about it being the main reason most people actually want one. It's just not the same thing as "now I am a ghost," which is what the marketing implies.

## What a VPN does not do

Quicker to list, and more useful, because this is where the marketing does the most lying by omission.

- **It does not make you anonymous.** You logged into your Google account, your email, your bank. They know exactly who you are. The IP address was never the thing identifying you.
- **It does not stop tracking.** Cookies, browser fingerprinting, your logged-in accounts, ad networks. None of that cares what your IP is. A VPN does nothing about the surveillance that actually follows you around.
- **It does not protect you from malware or phishing.** Some bundle a blocklist-based ad/tracker blocker, which is fine, but the VPN part isn't what's helping there.
- **It does not make HTTPS more secure.** Your connection to any half-decent website is already encrypted. The padlock was doing that job before you installed anything.
- **It does not hide your activity from a site you're logged into.** Obvious when said out loud, routinely forgotten in practice.

If you take one thing from this section: a VPN protects the *transport* of your data between you and the VPN server. It does almost nothing about who you are once your traffic arrives somewhere.

## VPNs to avoid, and why

**"Free" VPNs.** Running a global server network costs real money. If you aren't paying, the product is you, and the way a free VPN monetises you is the exact opposite of what you installed it for. The category has a long, well-documented history of logging and selling traffic, injecting ads, and in several cases shipping outright spyware. A free VPN is a stranger offering to carry all your mail for you, for free, forever, out of kindness. Decline.

There is exactly one safe flavour of free: a reputable paid provider's limited free tier, where the free users are subsidised by paying ones rather than being the revenue. Proton's free tier is the standout example. That's a real company with a real audited business, not a "free VPN."

**Anyone vague about logging.** "We respect your privacy" is not a no-logs policy. The thing that matters is whether the claim has been *independently audited*, and ideally whether it's ever been tested by an actual court order or server seizure. Marketing copy is free to write. Audits cost money and reputation, which is the point.

**Providers who hide who owns them.** This is the big one, and it's the thing affiliate roundups will never tell you, because the people who own the VPNs frequently also own the review sites. More on that in a second.

## The actual reviews

I've focused on the things that age badly and that the ad-driven articles gloss over: who owns them, what jurisdiction they answer to, whether the no-logs claim has been audited or court-tested, and the catch. Specifics below are current as of June 2026. VPN companies get acquired and change policies constantly, so if you're reading this a year from now, re-verify before trusting any single line.

### Mullvad: the one I'd actually recommend to a privacy nerd

Swedish, owned by its founders through a company called Amagicom, and almost aggressively uninterested in growth-hacking you. No email to sign up: you get a random account number. You can literally mail them cash in an envelope. Flat 5 euro a month, no "save 84% with our 3-year plan" countdown-timer nonsense.

Audited repeatedly by Cure53 and Assured, with reports published publicly. And it has the rarest credential of all: in 2024 Swedish police raided their Gothenburg office looking for user data and left with nothing, because there was nothing to take. That's the no-logs claim tested in the real world, not in a press release.

The catch: it's bad at streaming (services block its IPs), the server network is smaller than the giants, and the whole experience assumes you know why you're there. This is a privacy tool, not a Netflix unblocker.

### Proton VPN: the one I'd recommend to almost everyone else

From the Proton Mail people, based in Switzerland, which sits outside the major intelligence-sharing alliances and has genuinely strong privacy law. The clients are fully open source, so you don't have to take the audit's word for it, you can read the code. No-logs policy audited every year since 2022 by Securitum, plus a SOC 2 report, all published.

There's a usable free tier (the good kind, subsidised by paying users) which makes it the easy answer for "I just want something trustworthy for cafe wifi without thinking about it." It streams well, the apps are pleasant, and the privacy story is the most *verifiable* of any mainstream provider because of the open source angle.

The catch: one to keep an eye on rather than a dealbreaker. There's a proposed Swiss surveillance-law change (VUPF) floating around in 2026 that could, depending how it lands, erode the jurisdiction advantage. Proton has said it would move infrastructure rather than comply with privacy-eroding rules. Worth watching, not worth panicking over today.

### NordVPN: the competent giant

Panama-based (no mandatory data retention there), owned by Nord Security. Genuinely fast, enormous server network, streams everything, slick apps. No-logs policy audited repeatedly, most recently a fifth audit by Deloitte. RAM-only servers, so a seized machine has nothing on its disk to surrender.

Two pieces of nuance the ads skip. One: back in early 2026 there was a breach claim doing the rounds; Nord's account is that it involved an isolated third-party proof-of-concept environment, not production, and no real customer data. Take that as you will, but it wasn't the catastrophe some headlines implied. Two, more interestingly: an October 2024 transparency disclosure showed that under a binding Panamanian warrant, Nord handed over payment data and confirmation that an account existed. No traffic logs, because they don't keep those, but it's a useful reminder that "no activity logs" is not the same as "they have literally nothing on you."

The catch: not open source, so the no-logs claim rests on audits and trust rather than readable code. And it shares a corporate parent with Surfshark, which both products were notably quiet about (see below).

### Surfshark: Nord's cheaper sibling, and yes, they're siblings

Cheap, unlimited devices on one account, decent speeds, audited no-logs policy (twice, 2022 and 2023, a shorter track record than Nord's). Based in the Netherlands, which is a Nine Eyes member, though Dutch law doesn't mandate VPN data retention.

The thing worth knowing: Surfshark and NordVPN completed a merger in 2022 and share corporate ownership, investors, and senior leadership. For a while both kept marketing themselves as independent head-to-head competitors, which is a fun trick to pull on the people comparing them. If you're picking "Nord vs Surfshark" thinking you're choosing between rivals, you're choosing between two products from the same company. Fine if you know; less fine when you don't.

### ExpressVPN: fast, polished, and owned by a company you should know about

British Virgin Islands jurisdiction, RAM-only servers (their "TrustedServer" branding), PwC-audited, fast and beginner-friendly. As a *product* it's genuinely good and the audit practices are credible.

The asterisk is ownership. ExpressVPN is owned by Kape Technologies. Kape was previously called Crossrider, a name with a documented history in the browser-adware world before it rebranded and pivoted to privacy tools. That pivot may be entirely sincere. But here's the part that matters for *this* post specifically: Kape also owns CyberGhost, Private Internet Access, and ZenMate, **and it owns the review sites vpnMentor and WizCase.** So some of the glowing VPN roundups recommending ExpressVPN are published by the company that owns ExpressVPN. That's the affiliate-conflict problem in its purest form, and it's exactly why I wrote this.

### Private Internet Access (PIA): the court-tested workhorse

US-based, which sounds like a dealbreaker (Five Eyes, no friendly jurisdiction) until you look at the record. PIA has been subpoenaed in multiple US federal cases and each time produced nothing, because there was nothing logged. That's about as strong a real-world no-logs proof as exists, sitting in public court records. Open-source apps, audited, unlimited devices, excellent for torrenting, very cheap.

The catch: same as Express, it's owned by Kape, so the same ownership-concentration caveat applies. And US jurisdiction means that while there's nothing to hand over today, you're trusting that the no-logs architecture stays that way under a government that can compel a lot. The court history is reassuring; the jurisdiction is still the jurisdiction.

## The breakdown

| Provider | Jurisdiction | Owner | Audited no-logs | Court / raid tested | Open source | Best at | The catch |
|---|---|---|---|---|---|---|---|
| **Mullvad** | Sweden | Founder-owned (Amagicom) | Yes, repeatedly | Yes (2024 raid, nothing taken) | Partially | Anonymity, principle | Poor streaming, small network |
| **Proton VPN** | Switzerland | Proton AG | Yes, yearly since 2022 | No, but open source | Yes, fully | Trustworthy all-rounder, free tier | Swiss law change to watch |
| **NordVPN** | Panama | Nord Security | Yes, 5x (Deloitte) | Partially (gave payment data under warrant) | No | Speed, streaming | Not open source, Surfshark sibling |
| **Surfshark** | Netherlands | Nord Security | Yes, 2x | No | No | Price, unlimited devices | Same owner as Nord |
| **ExpressVPN** | BVI | Kape Technologies | Yes (PwC) | No | No | Speed, ease of use | Kape also owns review sites |
| **PIA** | USA | Kape Technologies | Yes | Yes (multiple US cases) | Yes | Torrenting, value, proof | US jurisdiction, Kape-owned |

A note on that table: "court/raid tested" is the column the marketing can't manufacture. An audit is a company paying someone to check their homework. A raid that comes up empty is the homework surviving a pop quiz nobody studied for. Mullvad and PIA are the two that have actually been through it.

## So which one should you get? Probably none of them.

Here's the part that won't get me any affiliate commissions.

Most people don't need a VPN. The marketing has convinced a generation that browsing without one is like leaving your front door open, and that's just not how the threat model works for a normal person in 2026. Your traffic to almost every site is already encrypted by HTTPS. Your ISP knowing which domains you visit is a real privacy cost, but a VPN fixes that by handing the same information to a VPN company instead, and the rest of the surveillance economy (your accounts, cookies, fingerprinting, the apps on your phone) doesn't care about your IP at all.

There are three good reasons to actually have one:

1. **You're regularly on untrusted networks.** Cafe wifi, airport wifi, hotel networks, conferences. Encrypting your transport on a network full of strangers is the original, legitimate use case and it's a good one.
2. **You want to watch things from another region.** Netflix in another country, sport that's geo-blocked, a service that won't serve your location. Totally valid. Just buy the location spoofer and skip the privacy theatre.
3. **You genuinely trust the VPN provider more than your ISP with the record of where you go.** For some people, in some countries, with some ISPs, this is unambiguously true. If that's you, it's a real reason. Just be honest that it's a trust transfer, not magic.

If one of those is you, here's my actual no-commission advice: **Proton VPN** if you want trustworthy-and-easy and like that you can read the source, **Mullvad** if you care about privacy as a principle and will mail an envelope of cash to prove it, **PIA or Nord** if you mostly want speed and streaming and the court record or audit trail is enough for you. If none of those three reasons describes you, save your money. The best VPN for most people is understanding why they probably don't need one.

Anyway. That's the post with no link to click. Strange feeling. I might go install an affiliate dashboard just to feel something.
