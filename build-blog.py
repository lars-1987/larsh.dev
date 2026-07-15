#!/usr/bin/env python3
"""
build-blog.py — static blog generator for larsh.dev.

Reads posts/*.md (YAML-ish front matter + markdown body), syntax-highlights code
with a Catppuccin Mocha Pygments theme, wraps each block in a terminal window,
builds an "On this page" TOC, and writes self-contained static HTML to blog/.

Zero runtime dependencies ship to the site — this is a one-shot local tool, like
build-og.py. Run:  python3 build-blog.py
"""
import os, re, html, json
import markdown

SITE = "https://larsh.dev"
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.style import Style
from pygments.token import (Keyword, Name, Comment, String, Error, Number,
                            Operator, Generic, Punctuation, Text, Whitespace, Literal)

ROOT = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(ROOT, "posts")
# Staged redesign: emit into redesign/blog/ with noindex. At go-live, set
# REDESIGN=False (output to blog/) and the noindex tag drops. Site-root files
# are referenced as ../ (works from redesign/blog/ AND from blog/ post-promotion);
# vendor/assets stay absolute.
REDESIGN = False
OUT_DIR = os.path.join(ROOT, "redesign", "blog") if REDESIGN else os.path.join(ROOT, "blog")

# ── Catppuccin Mocha palette ────────────────────────────────────────────────
M = dict(base="#1e1e2e", mantle="#181825", crust="#11111b", text="#cdd6f4",
         subtext="#a6adc8", overlay="#6c7086", overlay2="#9399b2",
         red="#f38ba8", peach="#fab387", yellow="#f9e2af", green="#a6e3a1",
         teal="#94e2d5", sky="#89dceb", blue="#89b4fa", mauve="#cba6f7",
         pink="#f5c2e7", flamingo="#f2cdcd")

class MochaStyle(Style):
    background_color = M["base"]
    styles = {
        Text:                  M["text"],
        Whitespace:            M["text"],
        Error:                 M["red"],
        Comment:               f"italic {M['overlay']}",
        Comment.Preproc:       M["pink"],
        Keyword:               M["mauve"],
        Keyword.Constant:      M["peach"],
        Keyword.Declaration:   M["mauve"],
        Keyword.Namespace:     M["mauve"],
        Keyword.Type:          M["yellow"],
        Operator:              M["sky"],
        Operator.Word:         M["mauve"],
        Punctuation:           M["overlay2"],
        Name:                  M["text"],
        Name.Attribute:        M["blue"],
        Name.Builtin:          M["red"],
        Name.Builtin.Pseudo:   M["red"],
        Name.Class:            M["yellow"],
        Name.Constant:         M["peach"],
        Name.Decorator:        M["yellow"],
        Name.Function:         M["blue"],
        Name.Function.Magic:   M["blue"],
        Name.Namespace:        M["yellow"],
        Name.Tag:              M["mauve"],
        Name.Variable:         M["text"],
        Name.Variable.Instance: M["red"],
        Name.Other:            M["text"],
        Literal:               M["text"],
        String:                M["green"],
        String.Escape:         M["pink"],
        String.Interpol:       M["pink"],
        String.Regex:          M["peach"],
        Number:                M["peach"],
        Generic.Deleted:       M["red"],
        Generic.Inserted:      M["green"],
        Generic.Emph:          "italic",
        Generic.Strong:        "bold",
        Generic.Heading:       M["blue"],
    }

FMT = HtmlFormatter(style=MochaStyle, nowrap=True)
CODE_CSS = HtmlFormatter(style=MochaStyle).get_style_defs('.term__code')

LANG_LABEL = {"ts": "typescript", "tsx": "tsx", "js": "javascript", "jsx": "jsx",
              "html": "html", "css": "css", "bash": "bash", "sh": "shell",
              "text": "log", "json": "json", "swift": "swift", "py": "python"}

# ── helpers ─────────────────────────────────────────────────────────────────
def parse_front_matter(raw):
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', raw, re.S)
    if not m:
        return {}, raw
    meta, body = {}, raw[m.end():]
    for line in m.group(1).splitlines():
        if ':' not in line:
            continue
        k, v = line.split(':', 1)
        k, v = k.strip(), v.strip()
        if v.startswith('[') and v.endswith(']'):
            meta[k] = [t.strip().strip('"\'') for t in v[1:-1].split(',') if t.strip()]
        else:
            meta[k] = v.strip('"\'')
    return meta, body

def slugify(s):
    s = re.sub(r'[^\w\s-]', '', s.lower()).strip()
    return re.sub(r'[\s_]+', '-', s)

def terminal(lang, code):
    code = code.rstrip('\n')
    try:
        lexer = get_lexer_by_name(lang) if lang else guess_lexer(code)
    except Exception:
        lexer = get_lexer_by_name('text')
    hl = highlight(code, lexer, FMT)
    label = LANG_LABEL.get(lang, lang or 'code')
    return (
        '<div class="term">'
        '<div class="term__bar" aria-hidden="true">'
        '<span class="term__dots"><i></i><i></i><i></i></span>'
        f'<span class="term__lang">{html.escape(label)}</span>'
        '</div>'
        f'<pre class="term__code"><code>{hl}</code></pre>'
        '</div>'
    )

def figures(content):
    # turn image-only paragraphs into captioned <figure>s; a paragraph holding two
    # images becomes a side-by-side pair (used for the "cause and effect" shots).
    def repl(m):
        imgs = re.findall(r'<img[^>]*>', m.group(1))
        def cap(img):
            a = re.search(r'alt="([^"]*)"', img)
            return f'<figcaption>{a.group(1)}</figcaption>' if a and a.group(1) else ''
        cells = ''.join(f'<figure class="fig">{img}{cap(img)}</figure>' for img in imgs)
        return f'<div class="figpair">{cells}</div>' if len(imgs) > 1 else cells
    return re.sub(r'<p>((?:\s*<img[^>]*>\s*)+)</p>', repl, content)

def render_post_html(meta, body):
    # 1. pull fenced code blocks out before markdown sees them
    blocks = []
    def stash(m):
        blocks.append((m.group(1).strip(), m.group(2)))
        return f"\n\nXCODEBLOCKX{len(blocks)-1}X\n\n"
    body_nc = re.sub(r'```(\w*)\n(.*?)```', stash, body, flags=re.S)

    md = markdown.Markdown(extensions=['extra', 'toc', 'sane_lists'],
                           extension_configs={'toc': {'toc_depth': '2-2'}})
    content = md.convert(body_nc)

    # 2. re-insert highlighted terminals
    for i, (lang, code) in enumerate(blocks):
        term = terminal(lang, code)
        content = content.replace(f'<p>XCODEBLOCKX{i}X</p>', term)
        content = content.replace(f'XCODEBLOCKX{i}X', term)

    # 3. promote image paragraphs to captioned figures
    content = figures(content)

    # 4. wrap tables in a scroll container so wide comparisons never crush
    content = re.sub(r'(<table>.*?</table>)',
                     r'<div class="prose__table">\1</div>', content, flags=re.S)

    toc_items = [t for t in md.toc_tokens if t['level'] == 2]
    words = len(re.findall(r'\w+', re.sub(r'```.*?```', '', body, flags=re.S)))
    read = max(1, round(words / 200))
    return content, toc_items, read

# ── templates ───────────────────────────────────────────────────────────────
BLOG_CSS = """
/* blog — layers on top of site.css (paper/ink tokens, nav, footer, grain) */
.blog{padding-top:150px}
.back{display:inline-flex;align-items:center;gap:.5em;font-family:'Martian Mono',monospace;
  font-size:12px;letter-spacing:.06em;color:var(--mut);transition:color .25s var(--ease),translate .25s var(--ease)}
.back:hover{color:var(--ink);translate:-3px 0}

/* index */
.blog-head{max-width:760px;margin-bottom:56px}
.blog-head h1{font-weight:600;font-size:clamp(38px,7vw,80px);letter-spacing:-.025em;line-height:.98}
.blog-head .intro{color:var(--mut);font-size:clamp(16px,1.6vw,19px);line-height:1.5;margin-top:24px;max-width:600px}
.posts{list-style:none}
.prow{display:grid;grid-template-columns:190px 1fr auto;gap:32px;align-items:baseline;
  padding:30px 0;border-top:1px solid var(--hair)}
.posts li:last-child .prow{border-bottom:1px solid var(--hair)}
.prow .pm{font-family:'Martian Mono',monospace;font-size:11px;letter-spacing:.05em;color:var(--mut);line-height:1.9}
.prow .pt{font-weight:600;font-size:clamp(21px,2.3vw,30px);letter-spacing:-.015em;line-height:1.15}
.prow .ps{color:var(--mut);font-size:16px;line-height:1.5;margin-top:8px;max-width:60ch}
.prow .parr{align-self:center;font-size:16px;color:var(--ink)}
.prow .parr i{display:inline-block;font-style:normal;transition:translate .3s var(--ease)}
.prow:hover .parr i{translate:4px 0}
.prow:hover .pt{text-decoration:underline;text-underline-offset:4px}

/* post header */
.post-head{max-width:820px;padding-top:20px}
.post-meta{display:flex;flex-wrap:wrap;gap:14px;align-items:center;margin:28px 0 26px;
  font-family:'Martian Mono',monospace;font-size:11px;letter-spacing:.06em;color:var(--mut)}
.post-cat{color:var(--ink)}
.post-head h1{font-weight:600;font-size:clamp(34px,5.5vw,68px);letter-spacing:-.03em;line-height:1.02}
.post-sub{color:var(--mut);font-size:clamp(17px,1.8vw,21px);line-height:1.45;margin-top:22px;max-width:62ch}
.post-tags{display:flex;flex-wrap:wrap;gap:8px;margin-top:26px}
.post-tags span{font-family:'Martian Mono',monospace;font-size:10px;letter-spacing:.06em;color:var(--mut);
  border:1px solid var(--hair);padding:6px 11px;border-radius:999px}
.post-body{display:grid;grid-template-columns:200px 1fr;gap:64px;align-items:start;
  margin-top:60px;padding-bottom:56px}

/* TOC */
.toc{position:sticky;top:110px;align-self:start}
.toc__label{font-family:'Martian Mono',monospace;font-size:10px;letter-spacing:.1em;color:var(--mut);margin-bottom:16px}
.toc__list{list-style:none;display:flex;flex-direction:column;gap:2px}
.toc__list a{display:block;padding:6px 0 6px 14px;font-size:14px;color:var(--mut);
  border-left:1.5px solid var(--hair);transition:color .2s,border-color .2s}
.toc__list a:hover{color:var(--ink)}
.toc__list a.active{color:var(--ink);border-left-color:var(--ink);font-weight:500}

/* prose */
.prose{min-width:0;max-width:720px}
.prose>*{margin-bottom:26px}
.prose>*:last-child{margin-bottom:0}
.prose h2{font-weight:600;font-size:clamp(26px,3vw,36px);letter-spacing:-.02em;line-height:1.1;
  margin-top:56px;scroll-margin-top:100px}
.prose h2:first-child{margin-top:0}
.prose h3{font-weight:600;font-size:clamp(20px,2.2vw,24px);letter-spacing:-.01em;margin-top:36px}
.prose p{font-size:clamp(16px,1.55vw,18px);line-height:1.7;color:rgba(17,17,17,.82)}
.prose a{color:var(--ink);text-decoration:underline;text-underline-offset:3px;text-decoration-thickness:1px}
.prose a:hover{text-decoration-thickness:2px}
.prose strong{font-weight:600;color:var(--ink)}
.prose em{font-style:italic}
.prose ul,.prose ol{padding-left:1.3em;font-size:clamp(16px,1.55vw,18px);line-height:1.7;color:rgba(17,17,17,.82)}
.prose li{margin-bottom:.5em}
.prose li::marker{color:var(--mut)}
.prose blockquote{border-left:3px solid var(--ink);padding:2px 0 2px 24px;color:var(--mut);font-style:italic}
.prose blockquote p{color:var(--mut)}
.prose hr{border:0;border-top:1px solid var(--hair);margin:44px 0}
.prose :not(.term__code) > code{font-family:'Martian Mono',monospace;font-size:.84em;
  background:rgba(17,17,17,.06);color:var(--ink);padding:2px 6px;border-radius:5px;white-space:nowrap}

/* figures */
.prose .fig{margin:36px 0}
.prose .fig img{width:100%;height:auto;border-radius:14px;border:1px solid var(--hair)}
.prose figcaption{margin-top:12px;font-size:14px;color:var(--mut);font-style:italic;text-align:center}
.prose .figpair{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:36px 0}
@media(max-width:620px){.prose .figpair{grid-template-columns:1fr}}

/* tables */
.prose__table{overflow-x:auto;margin:36px 0;border:1px solid var(--hair);border-radius:12px}
.prose table{width:100%;min-width:640px;border-collapse:collapse;font-size:15px;line-height:1.5}
.prose thead th{text-align:left;font-weight:600;color:var(--ink);background:rgba(17,17,17,.04);
  padding:12px 14px;border-bottom:1px solid var(--hair)}
.prose tbody td{padding:11px 14px;color:rgba(17,17,17,.82);border-bottom:1px solid var(--hair)}
.prose tbody tr:last-child td{border-bottom:0}
.prose th:first-child,.prose td:first-child{color:var(--ink);font-weight:600;white-space:nowrap}

/* terminal code block (Catppuccin Mocha — kept, reads as a dark card on paper) */
.term{border-radius:14px;overflow:hidden;background:#1e1e2e;border:1px solid #11111b;
  box-shadow:0 30px 60px -30px rgba(17,17,17,.5);margin:36px 0}
.term__bar{display:flex;align-items:center;gap:.7em;padding:.7em .95em;background:#181825;border-bottom:1px solid #11111b}
.term__dots{display:inline-flex;gap:.45em}
.term__dots i{width:11px;height:11px;border-radius:50%;background:#45475a}
.term__dots i:nth-child(1){background:#f38ba8}
.term__dots i:nth-child(2){background:#f9e2af}
.term__dots i:nth-child(3){background:#a6e3a1}
.term__lang{font-family:'Martian Mono',monospace;font-size:11px;letter-spacing:.06em;color:#6c7086;margin-left:auto}
.term__code{margin:0;padding:1.1em 1.2em;overflow-x:auto;font-family:'Martian Mono',monospace;
  font-size:13px;line-height:1.7;color:#cdd6f4;tab-size:2}
.term__code code{font-family:inherit;background:none;padding:0;color:inherit;white-space:pre}
__CODE_CSS__

/* post foot */
.post-foot{display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap;
  padding:40px 0 60px;border-top:1px solid var(--hair)}
.post-foot .meta{font-family:'Martian Mono',monospace;font-size:11px;letter-spacing:.06em;color:var(--mut)}
.post-foot .meta a{color:var(--ink)}

@media (max-width:820px){
  .blog{padding-top:130px}
  .post-body{grid-template-columns:1fr;gap:0}
  .toc{display:none}
  .prow{grid-template-columns:1fr;gap:6px;padding:26px 0}
  .prow .pm{order:-1}
  .prow .parr{display:none}
}
@media (max-width:560px){ .blog{padding-top:112px} }
""".replace("__CODE_CSS__", CODE_CSS)

# nav + footer: same chrome as the redesign content pages (site.js drives them)
NAV_HTML = """  <header class="nav" id="nav">
    <div class="navpill" id="navpill">
      <div class="navrow">
        <a class="brand" href="../index.html">larsh.dev</a>
        <button class="navbtn" id="navbtn" aria-expanded="false" aria-label="Menu"><span class="ic"><i></i><i></i><i></i></span></button>
      </div>
      <nav class="menu" aria-label="Site">
        <a class="mlink" href="../work.html"><span class="n mono">01</span><span class="t">Work</span><span class="a">&rarr;</span></a>
        <a class="mlink" href="../index.html#sites"><span class="n mono">02</span><span class="t">Sites</span><span class="a">&rarr;</span></a>
        <a class="mlink" href="../index.html#services"><span class="n mono">03</span><span class="t">Services</span><span class="a">&rarr;</span></a>
        <a class="mlink" href="index.html"><span class="n mono">04</span><span class="t">Blog</span><span class="a">&rarr;</span></a>
        <a class="mlink" href="../index.html#contact"><span class="n mono">05</span><span class="t">Contact</span><span class="a">&rarr;</span></a>
      </nav>
      <div class="mfoot">
        <div class="socials">
          <a class="js-mail" data-u="larsh.dev" data-d="proton.me" href="#" aria-label="Email"><svg class="stroke" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m2 7 10 6 10-6"/></svg></a>
          <a href="https://x.com/larsitodev" target="_blank" rel="noopener noreferrer" aria-label="X"><svg viewBox="0 0 24 24"><path d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z"/></svg></a>
          <a href="https://github.com/lars-1987" target="_blank" rel="noopener noreferrer" aria-label="GitHub"><svg viewBox="0 0 24 24"><path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/></svg></a>
        </div>
        <span class="clock mono" id="clock">MELB --:--</span>
      </div>
    </div>
  </header>"""

FOOTER_HTML = """<footer class="foot" aria-label="Footer">
  <div class="footcard">
    <div class="footrow">
      <nav class="fbtns" aria-label="Footer links">
        <a class="fbtn" href="../work.html"><span class="t">Work</span><span class="a">&rarr;</span></a>
        <a class="fbtn" href="../index.html#services"><span class="t">Services</span><span class="a">&rarr;</span></a>
        <a class="fbtn" href="index.html"><span class="t">Blog</span><span class="a">&rarr;</span></a>
        <a class="fbtn" href="/resume/"><span class="t">R&eacute;sum&eacute;</span><span class="a">&rarr;</span></a>
      </nav>
      <span class="fstatus mono">&#9679; OPEN TO NEW PROJECTS &middot; MELBOURNE</span>
    </div>
    <span class="wordmark" aria-hidden="true">LARSH.DEV</span>
    <div class="fmeta mono">
      <span>&copy; LARS HOLMSTR&Ouml;M &middot; <a href="/privacy/">PRIVACY</a></span>
      <span>BUILT BY HAND. COOKIELESS. RESPECTS DO NOT TRACK.</span>
    </div>
  </div>
</footer>"""

NOINDEX = '<meta name="robots" content="noindex, nofollow" />' if REDESIGN else ''

def page(title, desc, body_html, extra_script="", head_extra=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
{NOINDEX}
<meta name="theme-color" content="#FAF7F3" />
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}" />
<meta name="author" content="Lars Holmström" />
{head_extra}
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
<link rel="stylesheet" href="/vendor/fonts.css" />
<link rel="stylesheet" href="../site.css?v=2" />
<style>{BLOG_CSS}</style>
</head>
<body>
{FOOTER_HTML}
<div class="page" id="page">
  <div class="pagebg" aria-hidden="true"></div>
  <div class="grain" aria-hidden="true"></div>
{NAV_HTML}
{body_html}
</div>
<div class="endspace" aria-hidden="true"></div>
<div class="toast mono" id="toast" role="status"></div>
<script src="/vendor/lenis.min.js"></script>
<script src="../site.js?v=2"></script>
{extra_script}
<script src="/analytics.js"></script>
</body>
</html>
"""

POST_SCRIPT = """<script>
(function(){
  if(window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var links = {};
  document.querySelectorAll('.toc__list a').forEach(function(a){
    links[a.getAttribute('href').slice(1)] = a;
  });
  var visible = {};
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(e){ visible[e.target.id] = e.isIntersecting; });
    var ids = Object.keys(links);
    var active = ids.filter(function(id){ return visible[id]; })[0] || null;
    ids.forEach(function(id){ links[id] && links[id].classList.toggle('active', id===active); });
  }, {rootMargin:'-10% 0px -75% 0px', threshold:0});
  document.querySelectorAll('.prose h2[id]').forEach(function(h){ io.observe(h); });
})();
</script>"""

# ── build ───────────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    posts = []
    for fn in sorted(os.listdir(POSTS_DIR)):
        if not fn.endswith('.md'):
            continue
        raw = open(os.path.join(POSTS_DIR, fn)).read()
        meta, body = parse_front_matter(raw)
        slug = slugify(meta.get('title', fn[:-3]))
        content, toc_items, read = render_post_html(meta, body)

        toc_html = ''.join(
            f'<li><a href="#{t["id"]}">{html.escape(t["name"])}</a></li>' for t in toc_items)
        tags = meta.get('tags', [])
        tag_html = ''.join(f'<span>{html.escape(t)}</span>' for t in tags)
        cat = (tags[0] if tags else 'notes').upper()
        date = meta.get('date', '')

        body_html = f"""<div class="wrap blog">
  <a class="back" href="index.html" data-r="left">&larr; All notes</a>
  <header class="post-head" data-r>
    <div class="post-meta"><span class="post-cat">{html.escape(cat)}</span><span>{html.escape(date)}</span><span>{read} MIN READ</span></div>
    <h1>{html.escape(meta.get('title',''))}</h1>
    <p class="post-sub">{html.escape(meta.get('subtitle',''))}</p>
    <div class="post-tags">{tag_html}</div>
  </header>
  <div class="post-body">
    <aside class="toc"><p class="toc__label">On this page</p><ul class="toc__list">{toc_html}</ul></aside>
    <article class="prose">{content}</article>
  </div>
  <footer class="post-foot">
    <a class="back" href="index.html">&larr; All notes</a>
    <span class="meta">&copy; {date[:4]} LARS HOLMSTR&Ouml;M &middot; <a href="/privacy/">PRIVACY</a></span>
  </footer>
</div>"""
        title = meta.get('title', '')
        sub = meta.get('subtitle', '')
        url = f"{SITE}/blog/{slug}.html"
        ld = {"@context": "https://schema.org", "@type": "BlogPosting",
              "headline": title, "description": sub,
              "datePublished": date, "dateModified": date,
              "author": {"@type": "Person", "name": "Lars Holmström", "url": SITE + "/"},
              "publisher": {"@type": "Person", "name": "Lars Holmström"},
              "url": url, "mainEntityOfPage": url, "image": SITE + "/og.png",
              "keywords": ", ".join(tags)}
        head_extra = f'''<link rel="canonical" href="{url}" />
<meta property="og:type" content="article" />
<meta property="og:title" content="{html.escape(title)}" />
<meta property="og:description" content="{html.escape(sub)}" />
<meta property="og:url" content="{url}" />
<meta property="og:site_name" content="Lars Holmström" />
<meta property="og:image" content="{SITE}/og.png" />
<meta property="article:published_time" content="{date}" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:creator" content="@larsitodev" />
<meta name="twitter:image" content="{SITE}/og.png" />
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'''
        out = os.path.join(OUT_DIR, slug + '.html')
        open(out, 'w').write(page(title + ' — Lars Holmström', sub, body_html, POST_SCRIPT, head_extra))
        posts.append(dict(slug=slug, meta=meta, read=read, date=date, tags=tags))
        print('wrote', out)

    # blog index (newest first)
    posts.sort(key=lambda p: p['date'], reverse=True)
    rows = ''
    for p in posts:
        tags = ' · '.join(html.escape(t).upper() for t in p['tags'][:3])
        rows += f"""<li><a class="prow" href="{p['slug']}.html" data-r="left">
      <div class="pm">{html.escape(p['date'])}<br>{p['read']} MIN &middot; {tags}</div>
      <div><div class="pt">{html.escape(p['meta'].get('title',''))}</div>
      <p class="ps">{html.escape(p['meta'].get('subtitle',''))}</p></div>
      <span class="parr" aria-hidden="true"><i>&rarr;</i></span>
    </a></li>"""
    index_body = f"""<div class="wrap blog">
  <a class="back" href="../index.html" data-r="left">&larr; Back to larsh.dev</a>
  <header class="blog-head" data-r>
    <h1>Writing &amp; war stories.</h1>
    <p class="intro">How the things on the front page actually got built &mdash; and the bugs that fought back. Optional reading.</p>
  </header>
  <ul class="posts">{rows}</ul>
</div>"""
    idx_desc = 'Engineering write-ups and debugging war stories by Lars Holmström — how the privacy-first tools on larsh.dev actually got built.'
    blog_ld = {"@context": "https://schema.org", "@type": "Blog",
               "name": "Notes — Lars Holmström", "description": idx_desc,
               "url": f"{SITE}/blog/",
               "author": {"@type": "Person", "name": "Lars Holmström", "url": SITE + "/"},
               "blogPost": [{"@type": "BlogPosting", "headline": p['meta'].get('title', ''),
                             "url": f"{SITE}/blog/{p['slug']}.html", "datePublished": p['date']}
                            for p in posts]}
    idx_head = f'''<link rel="canonical" href="{SITE}/blog/" />
<meta property="og:type" content="website" />
<meta property="og:title" content="Notes — Lars Holmström" />
<meta property="og:description" content="{html.escape(idx_desc)}" />
<meta property="og:url" content="{SITE}/blog/" />
<meta property="og:image" content="{SITE}/og.png" />
<meta name="twitter:card" content="summary_large_image" />
<script type="application/ld+json">{json.dumps(blog_ld, ensure_ascii=False)}</script>'''
    open(os.path.join(OUT_DIR, 'index.html'), 'w').write(
        page('Notes — Lars Holmström', idx_desc, index_body, "", idx_head))
    print('wrote', os.path.join(OUT_DIR, 'index.html'))

    # sitemap.xml at the project root — skip while staging so we don't touch the
    # live sitemap (the redesign is noindex until promoted to root).
    if REDESIGN:
        print('REDESIGN: skipped sitemap.xml (staged build)')
        return
    urls = [(SITE + '/', None, '1.0'),
            (SITE + '/work.html', None, '0.9'),
            (SITE + '/blog/', None, '0.8'),
            (SITE + '/resume/', None, '0.7'),
            (SITE + '/web-design-melbourne/', None, '0.7'),
            (SITE + '/summit/', None, '0.6'),
            (SITE + '/brighton/', None, '0.6'),
            (SITE + '/hawthorne/', None, '0.6'),
            (SITE + '/atelier/', None, '0.6')]
    urls += [(f"{SITE}/blog/{p['slug']}.html", p['date'], '0.7') for p in posts]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod, prio in urls:
        sm.append('  <url>')
        sm.append(f'    <loc>{loc}</loc>')
        if lastmod:
            sm.append(f'    <lastmod>{lastmod}</lastmod>')
        sm.append(f'    <priority>{prio}</priority>')
        sm.append('  </url>')
    sm.append('</urlset>\n')
    open(os.path.join(ROOT, 'sitemap.xml'), 'w').write('\n'.join(sm))
    print('wrote', os.path.join(ROOT, 'sitemap.xml'))

if __name__ == '__main__':
    main()
