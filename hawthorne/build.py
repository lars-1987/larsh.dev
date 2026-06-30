#!/usr/bin/env python3
"""
Hawthorne Property Group: static site builder.

Reads content.json (the single, structured, non-technical-editable source of
truth) and renders site/index.html: one self-contained static file with inline
CSS/JS, no framework, no runtime dependencies. Degrades cleanly with JS off and
respects prefers-reduced-motion.

Same pattern as the Summit and Brighton builds in this repo: content and markup
are kept separate so copy, prices and images are trivially swappable for a CMS.

Usage:  python3 build.py
"""

import json
import html
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT  # built files live at the project root (served at larsh.dev/hawthorne)


def esc(s):
    return html.escape(str(s), quote=True)


# Eyebrows/kicker labels are intentionally off: the headlines carry their own weight.
SHOW_EYEBROWS = False


def eyebrow(text, line=True, center=False, cls=""):
    if not SHOW_EYEBROWS:
        return ""
    classes = "eyebrow" + (" line" if line else "") + ((" " + cls) if cls else "")
    style = ' style="justify-content:center"' if center else ""
    return f'<span class="{classes}"{style}>{esc(text)}</span>'


# --------------------------------------------------------------------------
# CSS
# --------------------------------------------------------------------------
CSS = r"""
:root{
  --bg:#F7F4EF;
  --surface:#F1ECE5;
  --surface-2:#EAE3D8;
  --ink:#252320;
  --muted:#6B665F;
  --faint:#9B948A;
  --charcoal:#1F1D1A;
  --charcoal-2:#29251F;
  --bronze:#B2946C;
  --bronze-hi:#9C7E57;
  --border:#E3DBCF;
  --line-dark:rgba(247,244,239,.16);
  --cream:#F7F4EF;

  --maxw:1280px;
  --read:720px;
  --gut:clamp(20px,5vw,68px);
  --section:clamp(78px,11vw,140px);
  --r:4px;

  --f-display:'Cormorant Garamond',Georgia,'Times New Roman',serif;
  --f-body:'Inter',system-ui,-apple-system,sans-serif;
  --ease:cubic-bezier(.4,.02,.1,1);
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--ink);font-family:var(--f-body);font-size:16px;
  line-height:1.65;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;overflow-x:hidden}
img{display:block;max-width:100%;height:auto}
a{color:inherit;text-decoration:none}
::selection{background:var(--bronze);color:#fff}
.wrap{max-width:var(--maxw);margin:0 auto;padding-inline:var(--gut)}
section{position:relative}
.section-pad{padding-block:var(--section)}

.display{font-family:var(--f-display);font-weight:500;line-height:1.04;letter-spacing:-.005em;color:var(--ink)}
h1.display{font-size:clamp(3rem,7vw,5.6rem)}
h2.display{font-size:clamp(2.4rem,5vw,4rem)}
.eyebrow{font-family:var(--f-body);font-size:.7rem;font-weight:600;letter-spacing:.2em;
  text-transform:uppercase;color:var(--bronze);display:inline-flex;align-items:center;gap:.7em}
.eyebrow.line::before{content:"";width:30px;height:1px;background:var(--bronze)}
.lead{color:var(--muted);font-size:clamp(1.05rem,1.5vw,1.2rem);line-height:1.75;max-width:var(--read)}
.sec-head{margin-bottom:clamp(44px,5.5vw,72px);max-width:780px}
.sec-head.center{margin-inline:auto;text-align:center}
.sec-head.center .lead{margin-inline:auto}
.sec-head h2{margin-bottom:22px}

/* buttons */
.btn{display:inline-flex;align-items:center;gap:.7em;cursor:pointer;font-family:var(--f-body);
  font-weight:600;font-size:.74rem;letter-spacing:.12em;text-transform:uppercase;
  padding:1.15em 2em;border-radius:var(--r);border:1px solid transparent;
  transition:background .3s var(--ease),border-color .3s var(--ease),color .3s var(--ease),transform .3s var(--ease)}
.btn .arw{transition:transform .3s var(--ease)}
.btn:hover .arw{transform:translateX(4px)}
.btn-primary{background:var(--charcoal);color:var(--cream);border-color:var(--charcoal)}
.btn-primary:hover{background:var(--bronze);border-color:var(--bronze)}
.btn-ghost{background:transparent;color:var(--ink);border-color:var(--border)}
.btn-ghost:hover{border-color:var(--ink)}
.btn-block{width:100%;justify-content:center}
.link-arrow{display:inline-flex;align-items:center;gap:.5em;color:var(--bronze);font-family:var(--f-body);
  font-weight:600;font-size:.7rem;letter-spacing:.12em;text-transform:uppercase}
.link-arrow .arw{transition:transform .3s var(--ease)}
.link-arrow:hover .arw{transform:translateX(4px)}

/* header */
.skip{position:absolute;left:-999px;top:0;background:var(--charcoal);color:#fff;padding:10px 16px;z-index:200}
.skip:focus{left:0}
header.nav{position:fixed;inset:0 0 auto 0;z-index:100;color:var(--cream);
  transition:background .4s var(--ease),border-color .4s var(--ease),backdrop-filter .4s var(--ease);
  border-bottom:1px solid transparent}
header.nav.scrolled{background:rgba(247,244,239,.9);backdrop-filter:blur(16px) saturate(1.1);
  border-bottom-color:var(--border);color:var(--ink)}
.nav-inner{display:flex;align-items:center;justify-content:space-between;height:84px;
  max-width:var(--maxw);margin:0 auto;padding-inline:var(--gut)}
.brand{display:flex;flex-direction:column;line-height:1;gap:6px}
.brand .bt{font-family:var(--f-display);font-weight:600;font-size:1.5rem;letter-spacing:.28em;text-transform:uppercase}
.brand .bs{font-family:var(--f-body);font-size:.5rem;letter-spacing:.34em;text-transform:uppercase;opacity:.7}
.nav-links{display:flex;align-items:center;gap:38px}
.nav-links a{font-size:.78rem;letter-spacing:.05em;opacity:.82;transition:opacity .2s;position:relative;padding:5px 0}
.nav-links a::after{content:"";position:absolute;left:0;bottom:-1px;width:0;height:1px;background:var(--bronze);transition:width .3s var(--ease)}
.nav-links a:hover,.nav-links a.active{opacity:1}
.nav-links a:hover::after,.nav-links a.active::after{width:100%}
.nav-cta{display:flex;align-items:center;gap:18px}
.nav-cta .btn-ghost{padding:.85em 1.5em;font-size:.68rem;color:currentColor;border-color:currentColor;opacity:.9}
.nav-cta .btn-ghost:hover{opacity:1;background:rgba(178,148,108,.14)}
.burger{display:none;flex-direction:column;gap:5px;background:none;border:0;cursor:pointer;padding:8px;z-index:120}
.burger span{width:24px;height:1.5px;background:currentColor;transition:.3s var(--ease)}
.menu-open .burger span:nth-child(1){transform:translateY(6.5px) rotate(45deg)}
.menu-open .burger span:nth-child(2){opacity:0}
.menu-open .burger span:nth-child(3){transform:translateY(-6.5px) rotate(-45deg)}

/* hero */
.hero{position:relative;min-height:100svh;display:flex;flex-direction:column;justify-content:flex-end;
  overflow:hidden;isolation:isolate;color:var(--cream)}
.hero-bg{position:absolute;inset:0;z-index:-2}
.hero-bg img{width:100%;height:100%;object-fit:cover;object-position:50% 50%}
.hero-bg::after{content:"";position:absolute;inset:0;background:
  linear-gradient(100deg,rgba(20,18,15,.82) 0%,rgba(24,21,17,.55) 38%,rgba(28,24,19,.12) 70%,rgba(28,24,19,.32) 100%),
  linear-gradient(to top,rgba(18,16,13,.6),transparent 40%)}
.hero-inner{width:100%;max-width:var(--maxw);margin:0 auto;padding-inline:var(--gut);
  padding-top:clamp(120px,18vh,170px);padding-bottom:clamp(34px,6vh,68px);flex:1;display:flex;flex-direction:column;justify-content:center}
.hero h1{max-width:16ch;color:#F4EEE3}
.hero h1 .l2{color:#E8D8C0}
.hero-sub{margin-top:26px;max-width:46ch;color:#E7E0D4;font-size:clamp(1.05rem,1.5vw,1.22rem)}
.hero-actions{margin-top:34px;display:flex;flex-wrap:wrap;gap:14px}
.hero-actions .btn-primary{background:var(--bronze);border-color:var(--bronze);color:#1F1D1A}
.hero-actions .btn-primary:hover{background:#C2A47C;border-color:#C2A47C}
.hero-actions .btn-ghost{color:#F4EEE3;border-color:rgba(244,238,227,.42)}
.hero-actions .btn-ghost:hover{border-color:#F4EEE3;background:rgba(244,238,227,.08)}
.hero-stats{background:var(--charcoal);color:var(--cream)}
.hero-stats .wrap{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;padding-block:30px}
.hstat{display:flex;flex-direction:column;gap:7px;position:relative;padding-left:24px}
.hstat::before{content:"";position:absolute;left:0;top:4px;bottom:4px;width:1px;background:var(--line-dark)}
.hstat .v{font-family:var(--f-display);font-weight:600;font-size:1.7rem;line-height:1;color:#F4EEE3}
.hstat .l{font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;color:#B7AEA0}

/* properties */
.prop-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:clamp(20px,2.4vw,34px)}
.prop{display:flex;flex-direction:column}
.prop-img{position:relative;overflow:hidden;border-radius:var(--r);aspect-ratio:4/3;background:var(--surface)}
.prop-img img{width:100%;height:100%;object-fit:cover;transition:transform .8s var(--ease)}
.prop:hover .prop-img img{transform:scale(1.045)}
.prop-status{position:absolute;top:14px;left:14px;background:rgba(31,29,26,.82);color:var(--cream);
  font-size:.6rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;padding:6px 12px;border-radius:2px;backdrop-filter:blur(4px)}
.prop-body{padding:22px 4px 0}
.prop-top{display:flex;align-items:baseline;justify-content:space-between;gap:16px}
.prop .price{font-family:var(--f-display);font-weight:600;font-size:1.85rem;line-height:1}
.prop .suburb{font-size:.74rem;letter-spacing:.14em;text-transform:uppercase;color:var(--bronze)}
.prop .specs{font-size:.82rem;color:var(--muted);margin-top:8px;letter-spacing:.02em}
.prop .desc{color:var(--muted);font-size:.92rem;margin-top:14px;padding-top:14px;border-top:1px solid var(--border)}

/* approach */
.appr-grid{display:grid;grid-template-columns:1.05fr .95fr;gap:clamp(34px,5vw,76px);align-items:center}
.appr-img{border-radius:var(--r);overflow:hidden;aspect-ratio:4/3;border:1px solid var(--border)}
.appr-img img{width:100%;height:100%;object-fit:cover}
.feat-grid{display:grid;grid-template-columns:1fr 1fr;gap:30px 38px}
.feat .ft{font-family:var(--f-display);font-weight:600;font-size:1.35rem;margin-bottom:10px;display:flex;align-items:center;gap:10px}
.feat .ft::before{content:"";width:18px;height:1px;background:var(--bronze)}
.feat p{color:var(--muted);font-size:.92rem}

/* lifestyle */
.life{background:var(--surface)}
.life-head{max-width:780px;margin-bottom:clamp(40px,5vw,64px)}
.life-imgs{display:grid;grid-template-columns:1.5fr 1fr;gap:clamp(16px,2vw,26px)}
.life-imgs figure{border-radius:var(--r);overflow:hidden;aspect-ratio:3/2;border:1px solid var(--border)}
.life-imgs figure:last-child{aspect-ratio:auto}
.life-imgs img{width:100%;height:100%;object-fit:cover}

/* team */
.team-grid{display:grid;grid-template-columns:.85fr 1.15fr;gap:clamp(36px,5vw,80px);align-items:center}
.team-img{border-radius:var(--r);overflow:hidden;aspect-ratio:5/6;border:1px solid var(--border)}
.team-img img{width:100%;height:100%;object-fit:cover}
.team-copy p{color:var(--muted);margin-bottom:18px;max-width:56ch}
.team-copy p:first-of-type{font-family:var(--f-display);font-size:clamp(1.3rem,2vw,1.65rem);line-height:1.4;color:var(--ink)}
.team-name{margin:26px 0 28px}
.team-name .nm{font-family:var(--f-display);font-weight:600;font-size:1.6rem;line-height:1}
.team-name .rl{font-size:.74rem;letter-spacing:.12em;text-transform:uppercase;color:var(--bronze);margin-top:6px;display:block}
.track{display:flex;gap:clamp(24px,4vw,52px);padding-top:26px;border-top:1px solid var(--border)}
.track .v{font-family:var(--f-display);font-weight:600;font-size:1.9rem;line-height:1}
.track .l{font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-top:6px}

/* process */
.proc{display:grid;grid-template-columns:repeat(4,1fr);gap:0;position:relative}
.proc::before{content:"";position:absolute;top:26px;left:9%;right:9%;height:1px;background:var(--border)}
.step{padding:0 20px;position:relative}
.step-no{width:54px;height:54px;border-radius:50%;background:var(--bg);border:1px solid var(--bronze);
  display:flex;align-items:center;justify-content:center;font-family:var(--f-display);font-weight:600;
  font-size:1.2rem;color:var(--bronze);position:relative;z-index:1;margin-bottom:24px}
.step h3{font-family:var(--f-display);font-weight:600;font-size:1.45rem;margin-bottom:10px}
.step p{color:var(--muted);font-size:.92rem}

/* results */
.res-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;margin-bottom:clamp(44px,5vw,72px)}
.rstat{text-align:center;padding:30px 16px;background:var(--surface);border:1px solid var(--border);border-radius:var(--r)}
.rstat .v{font-family:var(--f-display);font-weight:600;font-size:clamp(2.2rem,4vw,3rem);line-height:1;color:var(--ink)}
.rstat .l{font-size:.74rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-top:10px}
.sale{background:var(--charcoal);color:var(--cream);border-radius:var(--r);overflow:hidden;
  display:grid;grid-template-columns:1fr 1fr}
.sale-img{position:relative;min-height:420px}
.sale-img img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.sale-body{padding:clamp(34px,4vw,60px)}
.sale-label{font-size:.7rem;letter-spacing:.2em;text-transform:uppercase;color:var(--bronze);display:flex;align-items:center;gap:.7em}
.sale-label::before{content:"";width:30px;height:1px;background:var(--bronze)}
.sale h3{font-family:var(--f-display);font-weight:600;font-size:clamp(2rem,3vw,2.6rem);margin:18px 0 6px;color:#F4EEE3}
.sale .addr{color:#C9C1B4;font-size:.95rem;letter-spacing:.02em}
.sale .price{font-family:var(--f-display);font-weight:600;font-size:2.2rem;color:#F4EEE3;margin-top:20px}
.sale .specs{font-size:.8rem;letter-spacing:.04em;color:#B7AEA0;margin-top:6px;text-transform:uppercase}
.sale .desc{color:#CFC8BB;font-size:.94rem;margin-top:20px;padding-top:20px;border-top:1px solid var(--line-dark);max-width:46ch}
.sale-points{display:grid;grid-template-columns:1fr 1fr;gap:20px 26px;margin-top:24px}
.sale-points .pt-t{font-size:.78rem;font-weight:600;letter-spacing:.06em;color:#F0E9DC;margin-bottom:4px}
.sale-points p{font-size:.82rem;color:#ADA597;line-height:1.5}
.sale-quote{margin-top:26px;padding-top:22px;border-top:1px solid var(--line-dark);
  font-family:var(--f-display);font-style:italic;font-size:1.25rem;color:#E4DCCD}
.sale-quote .by{display:block;font-family:var(--f-body);font-style:normal;font-size:.68rem;
  letter-spacing:.14em;text-transform:uppercase;color:var(--bronze);margin-top:12px}

/* testimonials */
.tst-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}
.tst{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:40px 34px;
  display:flex;flex-direction:column;gap:22px}
.tst .qm{font-family:var(--f-display);font-size:3rem;line-height:.4;color:var(--bronze);height:22px}
.tst blockquote{font-family:var(--f-display);font-size:1.45rem;line-height:1.42;color:var(--ink)}
.tst .who{margin-top:auto;font-size:.74rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.tst .who b{color:var(--ink);font-weight:600}

/* faq */
.faq-wrap{max-width:860px;margin-inline:auto}
.faq details{border-top:1px solid var(--border)}
.faq details:last-of-type{border-bottom:1px solid var(--border)}
.faq summary{list-style:none;cursor:pointer;padding:28px 0;display:flex;align-items:center;justify-content:space-between;
  gap:24px;font-family:var(--f-display);font-weight:600;font-size:clamp(1.3rem,2.2vw,1.7rem)}
.faq summary::-webkit-details-marker{display:none}
.faq summary:hover{color:var(--bronze)}
.faq .ic{flex:none;width:18px;height:18px;position:relative}
.faq .ic::before,.faq .ic::after{content:"";position:absolute;background:var(--bronze);transition:transform .3s var(--ease)}
.faq .ic::before{top:8px;left:0;width:18px;height:1.5px}
.faq .ic::after{top:0;left:8px;width:1.5px;height:18px}
.faq details[open] .ic::after{transform:scaleY(0)}
.faq .ans{color:var(--muted);font-size:1rem;line-height:1.75;padding:0 50px 30px 0;max-width:72ch}

/* appraisal */
.appraise{background:var(--surface)}
.appr-form-grid{display:grid;grid-template-columns:1.25fr .9fr;gap:clamp(30px,4vw,60px);align-items:start}
.appr-form{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.field{display:flex;flex-direction:column;gap:8px}
.field.full{grid-column:1/-1}
.field label{font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-weight:600}
.field label .req{color:var(--bronze)}
.field input,.field select,.field textarea{background:var(--bg);border:1px solid var(--border);border-radius:var(--r);
  color:var(--ink);font-family:var(--f-body);font-size:.96rem;padding:14px 16px;transition:border-color .2s,box-shadow .2s;width:100%}
.field textarea{resize:vertical;min-height:110px}
.field input::placeholder,.field textarea::placeholder{color:var(--faint)}
.field input:focus,.field select:focus,.field textarea:focus{outline:none;border-color:var(--bronze);box-shadow:0 0 0 3px rgba(178,148,108,.16)}
.field select{appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath fill='%236B665F' d='M6 8 0 0h12z'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:right 16px center;padding-right:40px}
.appr-form .submit-row{grid-column:1/-1;display:flex;flex-direction:column;gap:14px}
.reassure{font-size:.78rem;color:var(--faint)}
.appr-success{display:none;background:var(--bg);border:1px solid var(--bronze);border-radius:var(--r);padding:42px;text-align:center}
.appr-success.show{display:block}
.appr-success .ic{display:block;width:46px;height:46px;color:var(--bronze);margin:0 auto 18px}
.appr-success h3{font-family:var(--f-display);font-weight:600;font-size:1.8rem;margin-bottom:10px}
.appr-success p{color:var(--muted)}
.info-panel{background:var(--charcoal);color:var(--cream);border-radius:var(--r);padding:clamp(30px,3vw,42px);
  display:flex;flex-direction:column;gap:28px}
.info-block .ih{font-size:.68rem;letter-spacing:.16em;text-transform:uppercase;color:var(--bronze);margin-bottom:12px;font-weight:600}
.info-block p,.info-block a{color:#E7E0D4;font-size:.96rem;line-height:1.7}
.info-block a:hover{color:var(--bronze)}
.hours-row{display:flex;justify-content:space-between;gap:16px;font-size:.92rem;padding:5px 0;color:#E7E0D4}
.hours-row span:first-child{color:#B7AEA0}

/* final cta */
.final{position:relative;overflow:hidden;color:var(--cream);text-align:center;isolation:isolate}
.final-bg{position:absolute;inset:0;z-index:-2}
.final-bg img{width:100%;height:100%;object-fit:cover;object-position:50% 45%}
.final-bg::after{content:"";position:absolute;inset:0;background:rgba(22,19,15,.58)}
.final .wrap{padding-block:clamp(96px,15vw,200px)}
.final h2{color:#F6F1E8;max-width:20ch;margin:0 auto 24px}
.final p{color:#E7E0D4;font-size:1.18rem;margin:0 auto 36px;max-width:46ch}
.final .btn-primary{background:var(--bronze);color:#1F1D1A;border-color:var(--bronze)}
.final .btn-primary:hover{background:#C6A87E;border-color:#C6A87E}

/* footer */
footer{background:var(--charcoal);color:#CFC8BB;padding-block:clamp(58px,7vw,92px)}
.foot-grid{display:grid;grid-template-columns:1.5fr repeat(3,1fr);gap:40px}
.foot-brand .brand{color:#F4EEE3;margin-bottom:20px}
.foot-brand p{color:#A89F90;font-size:.92rem;max-width:36ch}
.foot-col h4{font-size:.68rem;letter-spacing:.16em;text-transform:uppercase;color:var(--bronze);margin-bottom:16px}
.foot-col a,.foot-col p{color:#CFC8BB;font-size:.92rem;line-height:1.95;display:block}
.foot-col a:hover{color:#F4EEE3}
.foot-bottom{display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap;
  margin-top:clamp(40px,5vw,64px);padding-top:26px;border-top:1px solid var(--line-dark);font-size:.74rem;color:#8E8678;letter-spacing:.02em}

/* mobile sticky cta */
.mobile-cta{display:none;position:fixed;left:0;right:0;bottom:0;z-index:90;
  padding:12px var(--gut) calc(12px + env(safe-area-inset-bottom));background:rgba(247,244,239,.93);
  backdrop-filter:blur(14px);border-top:1px solid var(--border);transform:translateY(120%);transition:transform .35s var(--ease)}
.mobile-cta.show{transform:none}

/* reveal */
.reveal{opacity:0;transform:translateY(24px);transition:opacity .8s var(--ease),transform .8s var(--ease)}
.reveal.in{opacity:1;transform:none}

/* responsive */
@media(max-width:960px){
  .prop-grid{grid-template-columns:1fr 1fr}
  .appr-grid,.team-grid,.appr-form-grid{grid-template-columns:1fr;gap:36px}
  .team-img{aspect-ratio:4/3;max-width:520px}
  .sale{grid-template-columns:1fr}
  .sale-img{min-height:300px}
  .tst-grid{grid-template-columns:1fr}
  .proc{grid-template-columns:repeat(2,1fr);gap:44px 0}
  .proc::before{display:none}
  .res-stats{grid-template-columns:repeat(2,1fr)}
  .foot-grid{grid-template-columns:1fr 1fr}
  .life-imgs{grid-template-columns:1fr}
}
@media(max-width:720px){
  .nav-links,.nav-cta .btn{display:none}
  .burger{display:flex}
  .nav-links{position:fixed;inset:84px 0 auto 0;flex-direction:column;gap:0;background:rgba(247,244,239,.98);
    backdrop-filter:blur(16px);border-bottom:1px solid var(--border);padding:8px var(--gut) 24px;
    transform:translateY(-130%);transition:transform .4s var(--ease);pointer-events:none;color:var(--ink)}
  .menu-open .nav-links{transform:none;pointer-events:auto}
  .nav-links a{padding:16px 0;font-size:1rem;border-bottom:1px solid var(--border);width:100%;opacity:1}
  .mobile-cta{display:block}
  .prop-grid{grid-template-columns:1fr}
  .feat-grid{grid-template-columns:1fr}
  .hero-stats .wrap{grid-template-columns:1fr 1fr;gap:18px}
  .res-stats{grid-template-columns:1fr 1fr}
  .sale-points{grid-template-columns:1fr}
  .track{flex-wrap:wrap;gap:22px 32px}
  .foot-grid{grid-template-columns:1fr}
}
@media(max-height:780px) and (min-width:721px){
  .hero h1{font-size:clamp(2.6rem,6vh,4.6rem)}
  .hero-inner{padding-top:clamp(108px,14vh,140px)}
  .hero-sub{margin-top:18px}
  .hero-actions{margin-top:24px}
}
@media(prefers-reduced-motion:reduce){
  *{animation:none!important;scroll-behavior:auto!important}
  .reveal{opacity:1;transform:none;transition:none}
}
"""

JS = r"""
(function(){
  var header=document.querySelector('header.nav');var body=document.body;
  function onScroll(){
    if(window.scrollY>40){header.classList.add('scrolled');}else{header.classList.remove('scrolled');}
    var hero=document.querySelector('.hero');var mc=document.querySelector('.mobile-cta');
    if(hero&&mc){if(window.scrollY>hero.offsetHeight*0.7){mc.classList.add('show');}else{mc.classList.remove('show');}}
  }
  window.addEventListener('scroll',onScroll,{passive:true});onScroll();
  var burger=document.querySelector('.burger');
  if(burger){burger.addEventListener('click',function(){body.classList.toggle('menu-open');
    burger.setAttribute('aria-expanded',body.classList.contains('menu-open'));});}
  document.querySelectorAll('.nav-links a').forEach(function(a){a.addEventListener('click',function(){body.classList.remove('menu-open');});});
  var reduce=window.matchMedia('(prefers-reduced-motion:reduce)').matches;
  if(!reduce&&'IntersectionObserver' in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},
      {threshold:0.1,rootMargin:'0px 0px -7% 0px'});
    document.querySelectorAll('.reveal').forEach(function(el){io.observe(el);});
  }else{document.querySelectorAll('.reveal').forEach(function(el){el.classList.add('in');});}
  var navmap={};document.querySelectorAll('.nav-links a').forEach(function(a){navmap[a.getAttribute('href')]=a;});
  if('IntersectionObserver' in window){
    var so=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){var l=navmap['#'+e.target.id];
      if(l){Object.keys(navmap).forEach(function(k){navmap[k].classList.remove('active');});l.classList.add('active');}}});},
      {rootMargin:'-45% 0px -50% 0px'});
    document.querySelectorAll('section[id]').forEach(function(s){so.observe(s);});
  }
  var form=document.getElementById('appr-form');
  if(form){form.addEventListener('submit',function(ev){ev.preventDefault();if(!form.checkValidity()){form.reportValidity();return;}
    form.style.display='none';var ok=document.getElementById('appr-success');
    if(ok){ok.classList.add('show');ok.scrollIntoView({behavior:reduce?'auto':'smooth',block:'center'});}});}
})();
"""

CHECK = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" '
         'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5 10 17l9-10"/></svg>')
ARW = '<span class="arw" aria-hidden="true">&rarr;</span>'


def render(c):
    b = c["business"]
    nav_links = "".join(f'<a href="{esc(n["href"])}">{esc(n["label"])}</a>' for n in c["nav"])
    brand = f'<span class="bt">{esc(b["name"])}</span><span class="bs">{esc(b["tagline"])}</span>'
    header = f"""
<header class="nav"><div class="nav-inner">
  <a class="brand" href="#top" aria-label="{esc(b['name_full'])} home">{brand}</a>
  <nav class="nav-links" aria-label="Primary">{nav_links}</nav>
  <div class="nav-cta"><a class="btn btn-ghost" href="#appraise">{esc(c['hero']['cta_primary'])}</a>
    <button class="burger" aria-label="Menu" aria-expanded="false"><span></span><span></span><span></span></button></div>
</div></header>"""

    # hero
    h = c["hero"]
    title = f'<span>{esc(h["title_lines"][0])}</span> <span class="l2">{esc(h["title_lines"][1])}</span>'
    stats = "".join(f'<div class="hstat"><span class="v">{esc(s["value"])}</span><span class="l">{esc(s["label"])}</span></div>'
                    for s in h["stats"])
    hero = f"""
<section class="hero" id="top">
  <div class="hero-bg"><picture>
    <source type="image/webp" srcset="assets/hero-960.webp 960w, assets/hero.webp 1536w" sizes="100vw">
    <img src="assets/hero.webp" alt="Luxury Melbourne residence at dusk with city skyline" width="1536" height="1024" fetchpriority="high" decoding="async"></picture></div>
  <div class="hero-inner">
    <h1 class="display">{title}</h1>
    <p class="hero-sub">{esc(h['supporting'])}</p>
    <div class="hero-actions"><a class="btn btn-primary" href="#appraise">{esc(h['cta_primary'])} {ARW}</a>
      <a class="btn btn-ghost" href="#properties">{esc(h['cta_secondary'])}</a></div>
  </div>
  <div class="hero-stats"><div class="wrap">{stats}</div></div>
</section>"""

    # properties
    pr = c["properties"]
    cards = ""
    for it in pr["items"]:
        cards += f"""<article class="prop reveal">
      <div class="prop-img"><span class="prop-status">{esc(it['status'])}</span>
        <img src="assets/{it['image']}-800.webp" srcset="assets/{it['image']}-800.webp 800w, assets/{it['image']}.webp 1280w" sizes="(max-width:720px) 100vw, 33vw" alt="{esc(it['alt'])}" width="1280" height="853" loading="lazy" decoding="async"></div>
      <div class="prop-body">
        <div class="prop-top"><span class="price">{esc(it['price'])}</span><span class="suburb">{esc(it['suburb'])}</span></div>
        <div class="specs">{esc(it['specs'])}</div>
        <p class="desc">{esc(it['body'])}</p>
      </div></article>"""
    properties = f"""
<section class="section-pad" id="properties"><div class="wrap">
  <div class="sec-head reveal"><h2 class="display">{esc(pr['heading'])}</h2><p class="lead">{esc(pr['supporting'])}</p></div>
  <div class="prop-grid">{cards}</div>
</div></section>"""

    # approach
    ap = c["approach"]
    feats = "".join(f'<div class="feat"><div class="ft">{esc(f["title"])}</div><p>{esc(f["body"])}</p></div>' for f in ap["features"])
    approach = f"""
<section class="section-pad" id="approach"><div class="wrap"><div class="appr-grid">
  <div class="appr-img reveal"><img src="assets/{ap['image']}-800.webp" srcset="assets/{ap['image']}-800.webp 800w, assets/{ap['image']}.webp 1280w" sizes="(max-width:960px) 100vw, 50vw" alt="{esc(ap['image_alt'])}" width="1280" height="1024" loading="lazy" decoding="async"></div>
  <div class="reveal"><div class="sec-head" style="margin-bottom:30px"><h2 class="display">{esc(ap['heading'])}</h2><p class="lead">{esc(ap['supporting'])}</p></div>
    <div class="feat-grid">{feats}</div></div>
</div></div></section>"""

    # lifestyle
    lf = c["lifestyle"]
    lf_title = f'{esc(lf["title_lines"][0])}<br><span style="color:var(--bronze)">{esc(lf["title_lines"][1])}</span>'
    lf_imgs = "".join(f'<figure><img src="assets/{im["src"]}-800.webp" srcset="assets/{im["src"]}-800.webp 800w, assets/{im["src"]}.webp 1280w" sizes="(max-width:960px) 100vw, 45vw" alt="{esc(im["alt"])}" width="1280" height="853" loading="lazy" decoding="async"></figure>'
                      for im in lf["images"])
    lifestyle = f"""
<section class="life section-pad" id="lifestyle"><div class="wrap">
  <div class="life-head reveal"><h2 class="display">{lf_title}</h2><p class="lead" style="margin-top:22px">{esc(lf['supporting'])}</p></div>
  <div class="life-imgs reveal">{lf_imgs}</div>
</div></section>"""

    # team
    tm = c["team"]
    paras = "".join(f"<p>{esc(p)}</p>" for p in tm["paragraphs"])
    track = "".join(f'<div><div class="v">{esc(t["value"])}</div><div class="l">{esc(t["label"])}</div></div>' for t in tm["track"])
    team = f"""
<section class="section-pad" id="team"><div class="wrap"><div class="team-grid">
  <div class="team-img reveal"><img src="assets/{tm['image']}-700.webp" srcset="assets/{tm['image']}-700.webp 700w, assets/{tm['image']}.webp 1100w" sizes="(max-width:960px) 100vw, 40vw" alt="{esc(tm['image_alt'])}" width="1100" height="880" loading="lazy" decoding="async"></div>
  <div class="team-copy reveal"><div class="sec-head" style="margin-bottom:26px"><h2 class="display">{esc(tm['heading'])}</h2></div>
    {paras}
    <div class="team-name"><span class="nm">{esc(tm['name'])}</span><span class="rl">{esc(tm['role'])}</span></div>
    <div class="track">{track}</div>
  </div>
</div></div></section>"""

    # process
    pc = c["process"]
    steps = "".join(f'<div class="step reveal" style="transition-delay:{i*90}ms"><div class="step-no">{esc(st["no"])}</div><h3>{esc(st["title"])}</h3><p>{esc(st["body"])}</p></div>'
                    for i, st in enumerate(pc["steps"]))
    process = f"""
<section class="section-pad" id="process" style="background:var(--surface)"><div class="wrap">
  <div class="sec-head center reveal"><h2 class="display">{esc(pc['heading'])}</h2><p class="lead">{esc(pc['supporting'])}</p></div>
  <div class="proc">{steps}</div>
</div></section>"""

    # results
    rs = c["results"]
    rstats = "".join(f'<div class="rstat reveal"><div class="v">{esc(s["value"])}</div><div class="l">{esc(s["label"])}</div></div>' for s in rs["stats"])
    sale = rs["recent_sale"]
    spoints = "".join(f'<div><div class="pt-t">{esc(p["title"])}</div><p>{esc(p["body"])}</p></div>' for p in sale["points"])
    results = f"""
<section class="section-pad" id="results"><div class="wrap">
  <div class="sec-head center reveal"><h2 class="display">{esc(rs['heading'])}</h2><p class="lead">{esc(rs['supporting'])}</p></div>
  <div class="res-stats">{rstats}</div>
  <div class="sale reveal">
    <div class="sale-img"><img src="assets/{sale['image']}.webp" alt="{esc(sale['alt'])}" width="777" height="800" loading="lazy" decoding="async"></div>
    <div class="sale-body">
      <span class="sale-label">{esc(sale['label'])}</span>
      <h3>Sold</h3>
      <div class="addr">{esc(sale['address'])}</div>
      <div class="price">{esc(sale['price'])}</div>
      <div class="specs">{esc(sale['specs'])}</div>
      <p class="desc">{esc(sale['body'])}</p>
      <div class="sale-points">{spoints}</div>
      <p class="sale-quote">&ldquo;{esc(sale['quote'])}&rdquo;<span class="by">{esc(sale['quote_by'])}</span></p>
    </div>
  </div>
</div></section>"""

    # testimonials
    ts = c["testimonials"]
    tcards = "".join(f'<figure class="tst reveal"><div class="qm" aria-hidden="true">&ldquo;</div><blockquote>{esc(t["quote"])}</blockquote><figcaption class="who"><b>{esc(t["name"])}</b>, {esc(t["place"])}</figcaption></figure>'
                     for t in ts["items"])
    testimonials = f"""
<section class="section-pad" id="reviews"><div class="wrap">
  <div class="sec-head center reveal"><h2 class="display">{esc(ts['heading'])}</h2></div>
  <div class="tst-grid">{tcards}</div>
</div></section>"""

    # faq
    fq = c["faq"]
    items = "".join(f'<details{" open" if i==0 else ""}><summary>{esc(it["q"])}<span class="ic" aria-hidden="true"></span></summary><div class="ans">{esc(it["a"])}</div></details>'
                    for i, it in enumerate(fq["items"]))
    faq = f"""
<section class="section-pad" id="faq" style="background:var(--surface)"><div class="wrap">
  <div class="sec-head center reveal"><h2 class="display">{esc(fq['heading'])}</h2></div>
  <div class="faq faq-wrap reveal">{items}</div>
</div></section>"""

    # appraisal
    ap2 = c["appraisal"]
    vopts = "".join(f"<option>{esc(o)}</option>" for o in ap2["value_options"])
    hours_rows = "".join(f'<div class="hours-row"><span>{esc(hr["days"])}</span><span>{esc(hr["time"])}</span></div>' for hr in c["hours"])
    appraise = f"""
<section class="appraise section-pad" id="appraise"><div class="wrap">
  <div class="sec-head reveal" style="max-width:620px"><h2 class="display">{esc(ap2['heading'])}</h2><p class="lead">{esc(ap2['supporting'])}</p></div>
  <div class="appr-form-grid">
    <div class="reveal">
      <form class="appr-form" id="appr-form" novalidate>
        <div class="field"><label for="f-name">Name <span class="req">*</span></label><input id="f-name" name="name" type="text" required placeholder="Your name"></div>
        <div class="field"><label for="f-email">Email <span class="req">*</span></label><input id="f-email" name="email" type="email" required placeholder="you@email.com"></div>
        <div class="field"><label for="f-phone">Phone</label><input id="f-phone" name="phone" type="tel" placeholder="04xx xxx xxx"></div>
        <div class="field"><label for="f-value">Estimated value</label><select id="f-value" name="value">{vopts}</select></div>
        <div class="field full"><label for="f-address">Property address</label><input id="f-address" name="address" type="text" placeholder="Street, suburb"></div>
        <div class="field full"><label for="f-message">Message</label><textarea id="f-message" name="message" placeholder="Tell us a little about your home and your plans…"></textarea></div>
        <div class="submit-row"><button class="btn btn-primary btn-block" type="submit">{esc(ap2['submit'])} {ARW}</button>
          <p class="reassure">{esc(ap2['reassurance'])}</p></div>
      </form>
      <div class="appr-success" id="appr-success" role="status"><span class="ic">{CHECK}</span><h3>Thank you</h3>
        <p>We've received your request and will be in touch shortly to arrange your private appraisal.</p></div>
    </div>
    <aside class="info-panel reveal">
      <div class="info-block"><div class="ih">Office</div><p>{esc(b['street'])}<br>{esc(b['suburb'])}, {esc(b['region'])} {esc(b['postcode'])}</p></div>
      <div class="info-block"><div class="ih">Contact</div><p><a href="tel:{esc(b['phone_link'])}">{esc(b['phone_display'])}</a><br><a href="mailto:{esc(b['email'])}">{esc(b['email'])}</a></p></div>
      <div class="info-block"><div class="ih">Hours</div>{hours_rows}</div>
    </aside>
  </div>
</div></section>"""

    # final cta
    fc = c["final_cta"]
    fc_title = f'{esc(fc["title_lines"][0])}<br>{esc(fc["title_lines"][1])}'
    final = f"""
<section class="final" id="final">
  <div class="final-bg"><picture><source type="image/webp" srcset="assets/{fc['image']}-960.webp 960w, assets/{fc['image']}.webp 1402w" sizes="100vw">
    <img src="assets/{fc['image']}.webp" alt="Melbourne homeowner overlooking the city skyline at sunset" width="1402" height="1122" loading="lazy" decoding="async"></picture></div>
  <div class="wrap reveal"><h2 class="display">{fc_title}</h2><p>{esc(fc['supporting'])}</p>
    <a class="btn btn-primary" href="#appraise">{esc(fc['cta'])} {ARW}</a></div>
</section>"""

    # footer
    ft = c["footer"]
    foot_nav = "".join(f'<a href="{esc(n["href"])}">{esc(n["label"])}</a>' for n in c["nav"])
    foot_hours = "".join(f'<p><span style="color:#A89F90">{esc(hr["days"])}</span><br>{esc(hr["time"])}</p>' for hr in c["hours"])
    footer = f"""
<footer><div class="wrap"><div class="foot-grid">
  <div class="foot-brand"><a class="brand" href="#top">{brand}</a><p>{esc(ft['blurb'])}</p></div>
  <div class="foot-col"><h4>Office</h4><p>{esc(b['street'])}<br>{esc(b['suburb'])}, {esc(b['region'])} {esc(b['postcode'])}</p>
    <a href="tel:{esc(b['phone_link'])}">{esc(b['phone_display'])}</a><a href="mailto:{esc(b['email'])}">{esc(b['email'])}</a></div>
  <div class="foot-col"><h4>Hours</h4>{foot_hours}</div>
  <div class="foot-col"><h4>Explore</h4>{foot_nav}</div>
</div><div class="foot-bottom"><span>&copy; 2026 {esc(b['name_full'])}. {esc(b['suburb'])}, {esc(b['city'])}.</span><span>{esc(ft['legal'])}</span></div>
</div></footer>"""

    mobile_cta = f'<div class="mobile-cta"><a class="btn btn-primary btn-block" href="#appraise">{esc(c["hero"]["cta_primary"])} {ARW}</a></div>'

    # structured data
    ld = {"@context": "https://schema.org", "@type": "RealEstateAgent", "name": b["name_full"],
          "image": b["url"] + "/assets/hero.webp", "url": b["url"], "telephone": b["phone_display"],
          "email": b["email"], "priceRange": "$$$$", "areaServed": "Inner-east Melbourne",
          "address": {"@type": "PostalAddress", "streetAddress": b["street"], "addressLocality": b["suburb"],
                      "addressRegion": "VIC", "postalCode": b["postcode"], "addressCountry": "AU"},
          "openingHoursSpecification": [{"@type": "OpeningHoursSpecification",
                                         "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                                         "opens": "09:00", "closes": "17:30"}]}
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": it["q"], "acceptedAnswer": {"@type": "Answer", "text": it["a"]}} for it in c["faq"]["items"]]}
    jsonld = (f'<script type="application/ld+json">{json.dumps(ld, separators=(",", ":"))}</script>\n'
              f'<script type="application/ld+json">{json.dumps(faq_ld, separators=(",", ":"))}</script>')

    body = (header + hero + properties + approach + lifestyle + team + process
            + results + testimonials + faq + appraise + final + footer + mobile_cta)

    title_tag = f"{b['name_full']}: Luxury Real Estate in {b['suburb']}, {b['city']}"
    desc = ("Boutique residential real estate for Melbourne's inner east. Personal service, "
            "editorial marketing and results above reserve. Book a private appraisal.")

    return f"""<!doctype html>
<!--
  Hawthorne Property Group: fictional brand, built as a design & front-end portfolio piece.
  Single static file: inline CSS/JS, no framework, no runtime dependencies.
  Content is generated from content.json (the CMS-editable source of truth) via build.py.
-->
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title_tag)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="noindex">
<meta name="theme-color" content="#1F1D1A">
<link rel="canonical" href="{esc(b['url'])}/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(b['name_full'])}">
<meta property="og:title" content="{esc(title_tag)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(b['url'])}/">
<meta property="og:image" content="{esc(b['url'])}/assets/hero.webp">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='4' fill='%231F1D1A'/%3E%3Ctext x='16' y='22' font-family='Georgia,serif' font-size='17' fill='%23B2946C' text-anchor='middle'%3EH%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,500&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
{CSS}
</style>
{jsonld}
</head>
<body>
<a class="skip" href="#appraise">Skip to appraisal</a>
{body}
<script>{JS}</script>
</body>
</html>"""


def main():
    content = json.loads((ROOT / "content.json").read_text())
    SITE.mkdir(exist_ok=True)
    out = SITE / "index.html"
    out.write_text(render(content))
    print(f"Built {out}  ({out.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
