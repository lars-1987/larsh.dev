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
OUT_DIR = os.path.join(ROOT, "blog")

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

    toc_items = [t for t in md.toc_tokens if t['level'] == 2]
    words = len(re.findall(r'\w+', re.sub(r'```.*?```', '', body, flags=re.S)))
    read = max(1, round(words / 200))
    return content, toc_items, read

# ── templates ───────────────────────────────────────────────────────────────
HEAD_CSS = """
:root{
  --bg:#EAEDE0;--bg-warm:#F2F4EC;--bg-elevated:#E1E6D4;--bg-subtle:#D6DCC8;
  --sage:#BFD0B3;--sage-mid:#7F9C86;--fg:#2F3E35;--muted:#566459;--muted-strong:#3b4a40;
  --border:rgba(47,62,53,.16);--border-strong:rgba(47,62,53,.30);
  --accent:#46624f;--accent-dim:rgba(127,156,134,.18);
  --shadow-sm:0 10px 24px -14px rgba(47,62,53,.30);
  --shadow-lg:0 40px 80px -34px rgba(47,62,53,.40);
  --fs-sm:.9rem;--fs-base:1rem;--fs-md:1.18rem;--fs-lg:1.55rem;--fs-2xl:clamp(2rem,5vw,3.4rem);
  --sp-1:.5rem;--sp-2:1rem;--sp-3:1.5rem;--sp-4:2rem;--sp-5:3rem;--sp-6:4rem;--sp-7:6rem;
  --ease:cubic-bezier(.16,1,.3,1);--ease-spring:cubic-bezier(.34,1.56,.64,1);
  --radius:14px;--maxw:1080px;
  --font:"Geist",ui-sans-serif,system-ui,-apple-system,sans-serif;
  --mono:"Geist Mono",ui-monospace,"SFMono-Regular",monospace;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth;scroll-padding-top:2rem;-webkit-text-size-adjust:100%}
body{background:var(--bg);color:var(--fg);font-family:var(--font);font-size:var(--fs-base);
  line-height:1.65;-webkit-font-smoothing:antialiased;overflow-x:hidden}
body::before{content:"";position:fixed;inset:0;z-index:0;pointer-events:none;background:
  radial-gradient(1200px 620px at 78% -12%,rgba(127,156,134,.18),transparent 60%),
  radial-gradient(1000px 520px at -5% 102%,rgba(191,208,179,.42),transparent 55%)}
a{color:inherit;text-decoration:none}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:4px}
.wrap{max-width:var(--maxw);margin:0 auto;padding:0 var(--sp-4);position:relative;z-index:1}
.mono{font-family:var(--mono)}

/* back link */
.back{display:inline-flex;align-items:center;gap:.5em;margin-top:var(--sp-5);
  font-family:var(--mono);font-size:var(--fs-sm);color:var(--muted);
  padding:.5em .9em;border-radius:10px;background:var(--bg-elevated);
  transition:background .25s var(--ease),transform .25s var(--ease-spring),color .25s var(--ease)}
.back:hover{color:var(--fg);transform:translateX(-3px)}

/* post header */
.post__head{padding:var(--sp-6) 0 var(--sp-5);max-width:820px}
.post__meta{display:flex;align-items:center;gap:var(--sp-2);flex-wrap:wrap;margin-bottom:var(--sp-3);
  font-family:var(--mono);font-size:var(--fs-sm);color:var(--muted)}
.post__cat{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);
  background:var(--accent-dim);padding:.3em .7em;border-radius:6px}
.post__title{font-weight:700;font-size:var(--fs-2xl);letter-spacing:-.035em;line-height:1.05}
.post__sub{color:var(--muted-strong);font-size:var(--fs-md);margin-top:var(--sp-3);max-width:60ch}
.post__tags{display:flex;gap:.5em;flex-wrap:wrap;margin-top:var(--sp-3)}
.post__tags span{font-family:var(--mono);font-size:.72rem;color:var(--muted);
  background:var(--bg-elevated);padding:.35em .7em;border-radius:6px}

/* layout */
.post__body{display:grid;grid-template-columns:200px 1fr;gap:var(--sp-6);align-items:start;
  padding-bottom:var(--sp-7)}
.toc{position:sticky;top:var(--sp-4);align-self:start}
.toc__label{font-family:var(--mono);font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--muted);margin-bottom:var(--sp-2)}
.toc__list{list-style:none;display:flex;flex-direction:column}
.toc__list a{display:block;padding:.4em 0 .4em var(--sp-2);font-size:var(--fs-sm);color:var(--muted);
  border-left:2px solid var(--border);transition:color .2s var(--ease),border-color .2s var(--ease)}
.toc__list a:hover{color:var(--fg)}
.toc__list a.active{color:var(--fg);border-left-color:var(--accent);font-weight:500}

/* prose */
.prose{max-width:70ch;min-width:0}
.prose>p,.prose>ul,.prose>ol,.prose>blockquote,.prose .term{margin-bottom:var(--sp-3)}
.prose h2{font-size:var(--fs-lg);font-weight:700;letter-spacing:-.02em;
  margin:var(--sp-6) 0 var(--sp-3);scroll-margin-top:1.5rem}
.prose h2:first-child{margin-top:0}
.prose p{color:var(--muted-strong)}
.prose a{color:var(--accent);text-decoration:underline;text-underline-offset:3px;
  text-decoration-color:var(--sage-mid)}
.prose a:hover{text-decoration-thickness:2px}
.prose strong{color:var(--fg);font-weight:600}
.prose em{font-style:italic}
.prose ul,.prose ol{padding-left:1.3em;color:var(--muted-strong)}
.prose li{margin-bottom:.5em}
.prose li::marker{color:var(--sage-mid)}
.prose blockquote{border-left:3px solid var(--accent);padding:.2em 0 .2em var(--sp-3);
  color:var(--muted);font-style:italic}
.prose blockquote p{color:var(--muted)}
/* inline code */
.prose :not(.term__code) > code{font-family:var(--mono);font-size:.86em;
  background:var(--bg-elevated);color:var(--accent);padding:.15em .4em;border-radius:6px;
  white-space:nowrap}

/* terminal code block */
.term{border-radius:14px;overflow:hidden;background:#1e1e2e;border:1px solid #11111b;
  box-shadow:var(--shadow-lg)}
.term__bar{display:flex;align-items:center;gap:.7em;padding:.65em .9em;background:#181825;
  border-bottom:1px solid #11111b}
.term__dots{display:inline-flex;gap:.45em}
.term__dots i{width:11px;height:11px;border-radius:50%;background:#45475a}
.term__dots i:nth-child(1){background:#f38ba8}
.term__dots i:nth-child(2){background:#f9e2af}
.term__dots i:nth-child(3){background:#a6e3a1}
.term__lang{font-family:var(--mono);font-size:.72rem;letter-spacing:.06em;color:#6c7086;margin-left:auto}
.term__code{margin:0;padding:1.1em 1.2em;overflow-x:auto;font-family:var(--mono);
  font-size:.84rem;line-height:1.7;color:#cdd6f4;tab-size:2}
.term__code code{font-family:inherit;background:none;padding:0;color:inherit;white-space:pre}
__CODE_CSS__

/* post footer */
.post__foot{border-top:1px solid var(--border);padding:var(--sp-5) 0 var(--sp-7);
  display:flex;justify-content:space-between;align-items:center;gap:var(--sp-3);flex-wrap:wrap;
  font-size:var(--fs-sm);color:var(--muted)}
.post__foot a{color:var(--accent)}

/* blog index */
.blog-head{padding:var(--sp-6) 0 var(--sp-5);max-width:680px}
.blog-eyebrow{font-family:var(--mono);font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--accent);margin-bottom:var(--sp-2)}
.blog-title{font-weight:700;font-size:var(--fs-2xl);letter-spacing:-.035em;line-height:1.05}
.blog-intro{color:var(--muted-strong);font-size:var(--fs-md);margin-top:var(--sp-3)}
.posts{list-style:none;max-width:820px;padding-bottom:var(--sp-7)}
.posts li{border-top:1px solid var(--border)}
.post-row{display:block;padding:var(--sp-4) var(--sp-2);border-radius:14px;
  transition:background .3s var(--ease),transform .3s var(--ease-spring)}
.post-row:hover{background:var(--bg-elevated);transform:translateX(4px)}
.post-row__meta{font-family:var(--mono);font-size:.78rem;color:var(--muted);
  display:flex;gap:var(--sp-2);flex-wrap:wrap;margin-bottom:.5em}
.post-row__title{font-size:var(--fs-lg);font-weight:700;letter-spacing:-.02em;line-height:1.15}
.post-row__sub{color:var(--muted);font-size:var(--fs-sm);margin-top:.5em;max-width:62ch}

@media (max-width:820px){
  .post__body{grid-template-columns:1fr;gap:var(--sp-4)}
  .toc{display:none}
}
@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *,*::before,*::after{transition:none!important;animation:none!important}
}
""".replace("__CODE_CSS__", CODE_CSS)

def page(title, desc, body_html, extra_script="", head_extra=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}" />
<meta name="author" content="Lars Holmström" />
{head_extra}
<link rel="icon" type="image/svg+xml" href="../favicon.svg" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet" />
<style>{HEAD_CSS}</style>
</head>
<body>
{body_html}
{extra_script}
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

        body_html = f"""<div class="wrap">
  <a class="back" href="index.html">&larr; All notes</a>
  <header class="post__head">
    <div class="post__meta"><span class="post__cat">{html.escape(cat)}</span> {html.escape(date)} &middot; {read} min read</div>
    <h1 class="post__title">{html.escape(meta.get('title',''))}</h1>
    <p class="post__sub">{html.escape(meta.get('subtitle',''))}</p>
    <div class="post__tags">{tag_html}</div>
  </header>
  <div class="post__body">
    <aside class="toc"><p class="toc__label">On this page</p><ul class="toc__list">{toc_html}</ul></aside>
    <article class="prose">{content}</article>
  </div>
  <footer class="post__foot">
    <a class="back" href="index.html">&larr; All notes</a>
    <span>&copy; <span>{date[:4]}</span> Lars Holmstr&ouml;m &middot; <a href="../">larsh.dev</a></span>
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
        tags = ' &middot; '.join(html.escape(t) for t in p['tags'][:3])
        rows += f"""<li><a class="post-row" href="{p['slug']}.html">
      <div class="post-row__meta"><span>{html.escape(p['date'])}</span><span>{p['read']} min</span><span>{tags}</span></div>
      <div class="post-row__title">{html.escape(p['meta'].get('title',''))}</div>
      <p class="post-row__sub">{html.escape(p['meta'].get('subtitle',''))}</p>
    </a></li>"""
    index_body = f"""<div class="wrap">
  <a class="back" href="../">&larr; Back to larsh.dev</a>
  <header class="blog-head">
    <p class="blog-eyebrow">Notes</p>
    <h1 class="blog-title">Writing &amp; war stories.</h1>
    <p class="blog-intro">How the things on the front page actually got built — and the bugs that fought back. Optional reading.</p>
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

    # sitemap.xml at the project root
    urls = [(SITE + '/', None, '1.0'), (SITE + '/blog/', None, '0.8')]
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
