# larsh.dev

A single-file personal landing page. One `index.html`, no framework, no build step, no JS dependencies.

Live at **[larsh.dev](https://larsh.dev)**.

## Stack

Vanilla HTML, CSS, and JS — all inline in `index.html`. Bricolage Grotesque + Geist via Google Fonts. Phosphor icons inlined as an SVG sprite. Hosted on GitHub Pages with a custom domain.

## Why one file

- **Reviewable.** View-source on the live site is the whole thing.
- **Fast.** No bundler, no hydration, no third-party JS.
- **Honest.** Nothing to misrepresent — the page is what shipped.

## Layout

```
index.html      the page (HTML, CSS, JS all inline)
assets/         portrait + project screenshots
favicon.svg     site icon
og.png          link-preview card (1200×630)
build-og.py     one-shot script to regenerate og.png
CNAME           custom domain for GitHub Pages
```

## Accessibility & motion

Everything degrades cleanly with JS disabled. `prefers-reduced-motion` is honoured throughout — all transforms and transitions are disabled when set. Keyboard-navigable with a visible focus ring, semantic landmarks, WCAG AA contrast against the dark background.

## Contact

[larsh.dev@proton.me](mailto:larsh.dev@proton.me) · [@larsitodev](https://x.com/larsitodev)
