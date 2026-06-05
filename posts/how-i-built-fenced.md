---
title: I built a whole tool to avoid formatting code blocks
subtitle: A short story about solving a thirty-second problem with an afternoon of work.
date: 2026-06-06
tags: [side projects, typescript, tools]
---

I write this blog in Markdown, like a reasonable person. In Markdown, a code block is three backticks, the code, and three more backticks. It looks great in my editor. It is, briefly, perfect.

Then I publish it, and the rendered code looks like a ransom note.

## The thirty-second problem

The clean little fenced block my editor gave me for free does not survive the trip to HTML. So every post, I would start fiddling. A bit of CSS here. A syntax highlighter there. A terminal window wrapper, because I think they look nice and nobody can stop me. Every post, the same fiddling, to hand-reproduce the thing Markdown had already handed me at the top of the file.

This is the part of the story where a sensible person writes one CSS snippet, saves it somewhere, and moves on with their life.

I built a tool instead.

## The afternoon

The honest origin is that I already had a Python script doing this for the blog. It used Pygments, a Catppuccin theme I mapped by hand, and a little terminal wrapper. It worked. It was also 380 lines and lived on my laptop.

```python
# build-blog.py, the ancestor. it worked, and nobody else could ever use it.
def terminal(lang, code):
    hl = highlight(code, lexer_for(lang), formatter)
    return f'<div class="term">{hl}</div>'
```

So I did the responsible thing and rewrote it as a web app in an afternoon, to solve a problem that, generously, cost me thirty seconds a post.

```bash
npm create vite@latest fenced -- --template vanilla-ts
npm i markdown-it shiki
# congratulations, you have now spent more time than you will ever save
```

The whole idea fits in a function. Markdown comes in, every code block gets handed to a real syntax highlighter, and the result gets wrapped in some chrome. That is it. That is the product.

```ts
// the entire concept, more or less
function fence(code: string, lang: string) {
  const html = highlight(code, lang); // shiki does the genuinely hard part
  return `<div class="fenced">${html}</div>`;
}
```

## What it actually does

It is called fenced, and it lives at [fenced.dev](https://fenced.dev). You paste Markdown, it gives you back self-contained HTML where every code block is decorated and, importantly, still real, selectable text. Not a screenshot. I have strong and tedious opinions about code screenshots, the short version being that you cannot copy from them, they ignore dark mode, and they die on a phone.

It runs entirely in your browser. Nothing is uploaded, because there is no server to upload to. Every block comes out one of three ways: a terminal window, a clean themed card, or plain. Pick a theme, copy the HTML, or download one portable file. The highlighting is Shiki, so the themes are real, including all four Catppuccin flavours, which is the only opinion in this paragraph I will defend.

## Was it worth it

No.

Was it worth the afternoon, plus the three further afternoons I then spent on a theme picker, a privacy policy, an OpenGraph image, and a cookieless analytics setup I will check exactly once? Also no.

But it is done, it is free, and I no longer format code blocks by hand.

This post was written in Markdown and run through fenced. The code blocks above decorated themselves. Yes, I noticed the recursion too.
