#!/usr/bin/env python3
"""
Atelier Architecture: static site builder.

A digital exhibition for a residential architecture practice. Reads content.json
and renders site/index.html: one self-contained static file with inline CSS/JS,
no framework, no runtime dependencies.

The brief calls for "motion as architecture" (GSAP / ScrollTrigger / Lenis). To keep
this a fast, self-contained static POC, the same structural motion (mask reveals,
parallax, a draggable momentum gallery, scroll-driven typography) is implemented in
dependency-free vanilla JS. It degrades cleanly with JS off and respects
prefers-reduced-motion.

Same content/markup split as the other builds in this repo, so copy and imagery are
trivially swappable for a CMS later.

Usage:  python3 build.py
"""

import json
import html
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT  # built files live at the project root (served at larsh.dev/atelier)


def esc(s):
    return html.escape(str(s), quote=True)


CSS = r"""
:root{
  --bg:#EFEAE1;
  --bg-2:#F4F1E9;
  --bg-3:#E7E0D3;
  --ink:#2A2520;
  --muted:#766D61;
  --faint:#A69D8F;
  --espresso:#352822;
  --rosewood:#7B5448;
  --line:rgba(42,37,32,.16);
  --line-soft:rgba(42,37,32,.10);

  --maxw:1320px;
  --gut:clamp(22px,5vw,72px);
  --section:clamp(96px,15vw,210px);

  --f-serif:'Fraunces',Georgia,'Times New Roman',serif;
  --f-sans:'Inter Tight',system-ui,-apple-system,sans-serif;
  --ease:cubic-bezier(.33,0,.12,1);
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
/* lenis smooth scroll */
html.lenis,html.lenis body{height:auto}
.lenis.lenis-smooth{scroll-behavior:auto!important}
.lenis.lenis-smooth [data-lenis-prevent]{overscroll-behavior:contain}
.lenis.lenis-stopped{overflow:hidden}
body{background:var(--bg);color:var(--ink);font-family:var(--f-sans);font-size:16px;
  line-height:1.6;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;overflow-x:hidden}
img{display:block;max-width:100%;height:auto}
a{color:inherit;text-decoration:none}
::selection{background:var(--rosewood);color:#F4F1E9}
.wrap{max-width:var(--maxw);margin:0 auto;padding-inline:var(--gut)}
.wrap-wide{max-width:1560px;margin:0 auto;padding-inline:var(--gut)}
section{position:relative}

.serif{font-family:var(--f-serif);font-weight:340;font-optical-sizing:auto;letter-spacing:-.01em;line-height:1.04}
.label{font-family:var(--f-sans);font-size:.7rem;font-weight:500;letter-spacing:.2em;text-transform:uppercase;color:var(--muted)}
.label .dot{color:var(--rosewood)}
.lead{font-family:var(--f-serif);font-weight:340;font-size:clamp(1.4rem,2.6vw,2.1rem);line-height:1.32;color:var(--ink);max-width:24ch}
.body-copy{color:var(--muted);font-size:1rem;line-height:1.75;max-width:62ch}

/* reveal primitives */
.r-fade{opacity:0;transform:translateY(22px);transition:opacity 1s var(--ease),transform 1s var(--ease)}
.r-fade.in{opacity:1;transform:none}
.r-mask{clip-path:inset(100% 0 0 0);transition:clip-path 1.2s var(--ease)}
.r-mask.in{clip-path:inset(0 0 0 0)}
[data-delay="1"]{transition-delay:.12s}[data-delay="2"]{transition-delay:.24s}
[data-delay="3"]{transition-delay:.36s}[data-delay="4"]{transition-delay:.48s}

/* parallax */
.px{overflow:hidden}
.px img{width:100%;height:116%;object-fit:cover;will-change:transform}

/* header */
.skip{position:absolute;left:-999px;top:0;background:var(--ink);color:#fff;padding:10px 16px;z-index:200}
.skip:focus{left:0}
header.nav{position:fixed;inset:0 0 auto 0;z-index:100;color:var(--ink);
  transition:background .5s var(--ease),border-color .5s var(--ease),backdrop-filter .5s var(--ease);
  border-bottom:1px solid transparent}
header.nav.scrolled{background:rgba(239,234,225,.8);backdrop-filter:blur(14px) saturate(1.05);border-bottom-color:var(--line-soft)}
.nav-inner{display:flex;align-items:center;justify-content:space-between;height:78px;max-width:1560px;margin:0 auto;padding-inline:var(--gut)}
.brand{display:flex;align-items:baseline;gap:11px;line-height:1}
.brand .bt{font-family:var(--f-serif);font-weight:380;font-size:1.4rem;letter-spacing:.16em;text-transform:uppercase}
.brand .bs{font-size:.52rem;letter-spacing:.34em;text-transform:uppercase;color:var(--muted)}
.nav-links{display:flex;align-items:center;gap:34px}
.nav-links a{font-size:.76rem;letter-spacing:.06em;color:var(--muted);transition:color .25s;position:relative;padding:5px 0}
.nav-links a::after{content:"";position:absolute;left:0;bottom:0;width:0;height:1px;background:var(--rosewood);transition:width .35s var(--ease)}
.nav-links a:hover,.nav-links a.active{color:var(--ink)}
.nav-links a:hover::after,.nav-links a.active::after{width:100%}
.burger{display:none;flex-direction:column;gap:5px;background:none;border:0;cursor:pointer;padding:8px;z-index:120}
.burger span{width:24px;height:1.4px;background:currentColor;transition:.3s var(--ease)}
.menu-open .burger span:nth-child(1){transform:translateY(6.4px) rotate(45deg)}
.menu-open .burger span:nth-child(2){opacity:0}
.menu-open .burger span:nth-child(3){transform:translateY(-6.4px) rotate(-45deg)}

/* hero: full bleed */
.hero{position:relative;height:100svh;min-height:560px;overflow:hidden;isolation:isolate}
.hero-bg{position:absolute;inset:0;z-index:-2;overflow:hidden}
.hero-bg img{width:100%;height:100%;object-fit:cover;object-position:50% 46%;transform:scale(1.07);transition:transform 2s var(--ease)}
body.loaded .hero-bg img{transform:scale(1)}
.hero-bg::after{content:"";position:absolute;inset:0;background:
  linear-gradient(to top,rgba(244,241,233,.82),rgba(244,241,233,.16) 32%,transparent 52%),
  linear-gradient(to bottom,rgba(244,241,233,.5),transparent 18%)}
.hero-inner{position:relative;z-index:1;height:100%;max-width:1560px;margin:0 auto;
  padding:clamp(96px,14vh,140px) var(--gut) clamp(34px,5vh,58px);display:flex;flex-direction:column;justify-content:flex-end}
.hero-word{font-family:var(--f-serif);font-weight:300;font-optical-sizing:auto;color:var(--espresso);
  font-size:clamp(3.4rem,12vw,10rem);line-height:.84;letter-spacing:.015em;text-transform:uppercase}
.hero-foot{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;margin-top:clamp(18px,3vh,38px)}
.hero-statement{font-family:var(--f-serif);font-weight:340;font-size:clamp(1.15rem,1.9vw,1.6rem);line-height:1.3;max-width:24ch;color:var(--ink)}
.hero-meta{display:flex;flex-direction:column;gap:5px;text-align:right;flex:none}
.scroll-cue{position:absolute;left:50%;bottom:20px;transform:translateX(-50%);z-index:1;display:flex;flex-direction:column;
  align-items:center;gap:9px;font-size:.58rem;letter-spacing:.26em;text-transform:uppercase;color:var(--faint)}
.scroll-cue .ln{width:1px;height:30px;background:linear-gradient(var(--faint),transparent);animation:cue 2.6s var(--ease) infinite}
@keyframes cue{0%,100%{transform:scaleY(.35);opacity:.4;transform-origin:top}50%{transform:scaleY(1);opacity:1;transform-origin:top}}

/* work: full-bleed project showcase */
.work-index{padding:clamp(70px,10vw,150px) 0 clamp(40px,5vw,72px);text-align:center}
.work-index .label{justify-content:center}
.work-index .years{font-family:var(--f-serif);font-size:clamp(1.2rem,2vw,1.6rem);color:var(--muted);margin-top:14px}
.projects{display:flex;flex-direction:column}
.project{position:relative;height:100svh;min-height:560px;overflow:hidden;isolation:isolate}
.project-bg{position:absolute;inset:0;z-index:-2;overflow:hidden}
.project-bg img{width:100%;height:118%;object-fit:cover;will-change:transform}
.project::after{content:"";position:absolute;inset:0;background:linear-gradient(to top,rgba(20,16,12,.62),rgba(20,16,12,.06) 38%,transparent 58%)}
.project-cap{position:absolute;left:0;right:0;bottom:0;z-index:1;padding-bottom:clamp(40px,6vh,76px)}
.project-cap .pwrap{max-width:1560px;margin:0 auto;padding-inline:var(--gut);display:flex;align-items:flex-end;justify-content:space-between;gap:24px}
.project-cap .pno{font-family:var(--f-serif);font-size:1rem;color:rgba(244,238,227,.65);display:block;margin-bottom:14px}
.project-cap .pname{font-family:var(--f-serif);font-weight:320;font-size:clamp(2.6rem,6vw,5rem);line-height:.96;color:#F4EEE3}
.project-cap .pmeta{display:flex;flex-direction:column;gap:7px;text-align:right;flex:none;
  font-size:.64rem;letter-spacing:.2em;text-transform:uppercase;color:rgba(244,238,227,.82)}

/* philosophy */
.philo{background:var(--bg-3)}
.philo .wrap{padding-block:var(--section)}
.philo-lines{max-width:min(92vw,720px)}
.philo-lines .l1{font-family:var(--f-serif);font-weight:330;font-size:clamp(2.4rem,6vw,5rem);line-height:1.04;margin-bottom:clamp(34px,5vw,60px);max-width:15ch}
.philo-lines .lx{font-family:var(--f-serif);font-weight:350;font-size:clamp(1.3rem,2.4vw,1.9rem);line-height:1.45;color:var(--muted);max-width:42ch;margin-bottom:26px}
.philo-lines .lx:last-child{margin-bottom:0;color:var(--ink)}

/* gallery: pinned horizontal scroll (scroll vertically to pan sideways) */
.gallery{position:relative}
.gallery-sticky{overflow:hidden;display:flex;flex-direction:column;justify-content:center}
.gallery.pinned .gallery-sticky{position:sticky;top:0;height:100svh}
.gallery:not(.pinned) .gallery-sticky{padding-block:var(--section)}
.gallery-head{display:flex;justify-content:space-between;align-items:baseline;gap:24px;padding-inline:var(--gut);
  font-size:.66rem;letter-spacing:.2em;text-transform:uppercase;color:var(--muted)}
.gallery:not(.pinned) .gallery-head{margin-bottom:clamp(34px,4vw,56px)}
.gallery.pinned .gallery-head{position:absolute;top:clamp(86px,12vh,126px);left:0;right:0;z-index:2}
.gal-count{font-variant-numeric:tabular-nums;color:var(--faint)}
.gal-track{display:flex;gap:clamp(18px,2.2vw,38px);padding-inline:var(--gut);align-items:center;will-change:transform}
.gallery:not(.pinned) .gal-track{overflow-x:auto;scrollbar-width:none}
.gallery:not(.pinned) .gal-track::-webkit-scrollbar{display:none}
.gal-item{flex:0 0 auto}
.gallery:not(.pinned) .gal-item{width:clamp(260px,52vw,440px)}
.gal-item figure{position:relative;overflow:hidden;aspect-ratio:4/5;background:var(--bg-3)}
.gallery.pinned .gal-item figure{height:clamp(320px,56vh,560px);width:auto}
.gallery:not(.pinned) .gal-item figure{width:100%}
.gal-item img{width:100%;height:100%;object-fit:cover;pointer-events:none}
.gal-item figcaption{margin-top:16px;font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.gal-item .cn{color:var(--rosewood);margin-right:8px}
.gal-progress{display:none}
.gallery.pinned .gal-progress{display:block;position:absolute;bottom:clamp(40px,7vh,72px);left:var(--gut);right:var(--gut);height:1px;background:var(--line);z-index:2}
.gal-progress span{display:block;height:100%;background:var(--rosewood);transform-origin:left;transform:scaleX(0)}

/* materiality */
.matter{background:var(--bg-2)}
.matter-grid{display:grid;grid-template-columns:1fr 1fr;gap:clamp(36px,6vw,90px);align-items:center}
.matter-list{list-style:none;margin-top:clamp(30px,4vw,48px);border-top:1px solid var(--line)}
.matter-list li{font-family:var(--f-serif);font-weight:330;font-size:clamp(1.8rem,3.2vw,2.7rem);line-height:1;
  padding:clamp(14px,1.6vw,22px) 0;border-bottom:1px solid var(--line);color:var(--ink);
  display:flex;align-items:baseline;gap:18px;transition:color .3s var(--ease),padding-left .35s var(--ease)}
.matter-list li:hover{color:var(--rosewood);padding-left:12px}
.matter-list li .mn{font-family:var(--f-sans);font-size:.62rem;letter-spacing:.12em;color:var(--faint);font-weight:500}
.matter-media{display:flex;flex-direction:column;gap:clamp(16px,2vw,26px)}
.matter-media figure{overflow:hidden;aspect-ratio:4/3}
.matter-media img{width:100%;height:114%;object-fit:cover;will-change:transform}

/* transition */
.transition{position:relative;height:clamp(440px,72vh,820px);overflow:hidden;display:flex;align-items:center;justify-content:center}
.transition img{position:absolute;inset:0;width:100%;height:122%;object-fit:cover;top:-11%;will-change:transform}
.transition::after{content:"";position:absolute;inset:0;background:rgba(28,22,18,.34)}
.transition .tw{position:relative;z-index:1;font-family:var(--f-serif);font-weight:330;font-size:clamp(2.6rem,8vw,7rem);
  color:#EFEAE1;letter-spacing:.04em;text-transform:uppercase}

/* studio */
.studio-grid{display:grid;grid-template-columns:.92fr 1.08fr;gap:clamp(36px,6vw,90px);align-items:center}
.studio-img{overflow:hidden;aspect-ratio:4/3}
.studio-img img{width:100%;height:114%;object-fit:cover;will-change:transform}
.studio-copy .heading{font-family:var(--f-serif);font-weight:330;font-size:clamp(2rem,3.6vw,3rem);line-height:1.08;margin:22px 0 30px;max-width:18ch}
.studio-copy p{color:var(--muted);font-size:1.02rem;line-height:1.75;margin-bottom:20px;max-width:52ch}
.studio-sign{margin-top:34px;padding-top:24px;border-top:1px solid var(--line);display:flex;flex-direction:column;gap:5px}
.studio-sign .nm{font-family:var(--f-serif);font-size:1.5rem}
.studio-sign .rl{font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;color:var(--rosewood)}

/* journal */
.journal{background:var(--bg-2)}
.journal-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:clamp(22px,3vw,44px);margin-top:clamp(40px,5vw,64px)}
.entry-media{overflow:hidden;aspect-ratio:4/5;margin-bottom:20px}
.entry-media img{width:100%;height:108%;object-fit:cover;transition:transform 1.1s var(--ease)}
.entry:hover .entry-media img{transform:scale(1.04)}
.entry-meta{display:flex;gap:14px;font-size:.64rem;letter-spacing:.14em;text-transform:uppercase;color:var(--faint);margin-bottom:12px}
.entry-meta .cn{color:var(--rosewood)}
.entry h3{font-family:var(--f-serif);font-weight:340;font-size:clamp(1.5rem,2.4vw,1.9rem);line-height:1.1}

/* contact */
.contact-grid{display:grid;grid-template-columns:.9fr 1.1fr;gap:clamp(40px,6vw,96px);align-items:start}
.contact-copy h2{font-family:var(--f-serif);font-weight:330;font-size:clamp(2.4rem,4.6vw,3.6rem);line-height:1.04;margin-bottom:28px}
.contact-copy .body-copy{margin-bottom:36px}
.contact-detail{display:flex;flex-direction:column;gap:18px;padding-top:28px;border-top:1px solid var(--line)}
.contact-detail .cd{display:flex;flex-direction:column;gap:5px}
.contact-detail .ck{font-size:.62rem;letter-spacing:.16em;text-transform:uppercase;color:var(--faint)}
.contact-detail a,.contact-detail p{font-size:.98rem;color:var(--ink)}
.contact-detail a:hover{color:var(--rosewood)}
.cform{display:grid;grid-template-columns:1fr 1fr;gap:26px 24px}
.field{display:flex;flex-direction:column;gap:9px}
.field.full{grid-column:1/-1}
.field label{font-size:.64rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:500}
.field input,.field select,.field textarea{background:transparent;border:0;border-bottom:1px solid var(--line);
  color:var(--ink);font-family:var(--f-sans);font-size:1rem;padding:10px 0;transition:border-color .3s}
.field textarea{resize:vertical;min-height:70px}
.field input::placeholder,.field textarea::placeholder{color:var(--faint)}
.field input:focus,.field select:focus,.field textarea:focus{outline:none;border-bottom-color:var(--rosewood)}
.field select{appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='11' height='7' viewBox='0 0 11 7'%3E%3Cpath fill='%237B5448' d='M5.5 7 0 0h11z'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 2px center}
.cform .submit-row{grid-column:1/-1;margin-top:10px}
.btn-line{display:inline-flex;align-items:center;gap:.8em;cursor:pointer;background:none;border:0;
  font-family:var(--f-sans);font-weight:500;font-size:.78rem;letter-spacing:.14em;text-transform:uppercase;
  color:var(--ink);padding-bottom:8px;border-bottom:1px solid var(--ink);transition:gap .3s var(--ease),color .3s}
.btn-line:hover{gap:1.3em;color:var(--rosewood);border-bottom-color:var(--rosewood)}
.cform-success{display:none}
.cform-success.show{display:block}
.cform-success p{font-family:var(--f-serif);font-size:clamp(1.5rem,2.6vw,2rem);line-height:1.3;color:var(--ink);max-width:24ch}

/* closing */
.closing{position:relative;min-height:90svh;display:flex;align-items:center;justify-content:center;overflow:hidden;
  border-bottom-left-radius:clamp(18px,2.6vw,40px);border-bottom-right-radius:clamp(18px,2.6vw,40px)}
.closing img{position:absolute;inset:0;width:100%;height:112%;object-fit:cover;top:-6%;will-change:transform}
.closing::after{content:"";position:absolute;inset:0;background:linear-gradient(transparent,rgba(24,19,15,.5))}
.closing .cw{position:relative;z-index:1;font-family:var(--f-serif);font-weight:330;font-size:clamp(2.4rem,6vw,5.2rem);
  color:#F1ECE2;text-align:center;letter-spacing:.01em;padding-inline:var(--gut)}

/* reveal footer: the page lifts away as a card to uncover the footer beneath */
.page{position:relative;z-index:2;background:var(--bg);
  border-bottom-left-radius:clamp(18px,2.6vw,40px);border-bottom-right-radius:clamp(18px,2.6vw,40px);
  box-shadow:0 -1px 0 var(--line),0 40px 90px rgba(31,27,22,.26)}
.reveal-footer{position:fixed;left:0;right:0;bottom:0;z-index:1;background:var(--bg-2);color:var(--ink);
  padding:clamp(64px,8vh,104px) 0 clamp(6px,1.4vh,20px);
  display:flex;flex-direction:column;gap:clamp(34px,5vh,56px);overflow:hidden}
.rf-top{max-width:1560px;margin:0 auto;width:100%;padding-inline:var(--gut);display:grid;grid-template-columns:1.6fr 1fr 1fr;gap:clamp(30px,5vw,72px)}
.rf-brand .bt{font-family:var(--f-serif);font-weight:380;font-size:1.5rem;letter-spacing:.16em;text-transform:uppercase}
.rf-brand p{margin-top:16px;color:var(--muted);font-size:.92rem;line-height:1.7;max-width:30ch}
.rf-brand a.email{display:inline-block;margin-top:22px;font-family:var(--f-serif);font-size:clamp(1.2rem,1.8vw,1.6rem);
  color:var(--ink);border-bottom:1px solid var(--line);padding-bottom:3px;transition:color .3s,border-color .3s}
.rf-brand a.email:hover{color:var(--rosewood);border-color:var(--rosewood)}
.rf-col h4{font-size:.62rem;letter-spacing:.18em;text-transform:uppercase;color:var(--faint);margin-bottom:16px}
.rf-col a,.rf-col p{display:block;font-size:.92rem;line-height:2;color:var(--ink)}
.rf-col a{transition:color .25s}
.rf-col a:hover{color:var(--rosewood)}
.rf-meta{max-width:1560px;margin:0 auto;width:100%;padding-inline:var(--gut);
  display:flex;justify-content:space-between;align-items:flex-end;gap:18px;flex-wrap:wrap;
  font-size:.66rem;letter-spacing:.06em;color:var(--faint)}
.rf-meta .totop{display:inline-flex;align-items:center;gap:8px;color:var(--muted);letter-spacing:.16em;text-transform:uppercase;transition:color .3s}
.rf-meta .totop:hover{color:var(--rosewood)}
.rf-giant{width:100%;font-family:var(--f-serif);font-weight:300;font-optical-sizing:auto;color:var(--espresso);opacity:.82;
  font-size:clamp(4.5rem,24vw,30rem);line-height:.7;letter-spacing:.005em;text-transform:uppercase;
  text-align:center;white-space:nowrap}

/* responsive */
@media(max-width:900px){
  .matter-grid,.studio-grid,.contact-grid{grid-template-columns:1fr;gap:40px}
  .journal-grid{grid-template-columns:1fr}
  .cform{grid-template-columns:1fr}
  .project-cap .pwrap{flex-direction:column;align-items:flex-start;gap:14px}
  .project-cap .pmeta{flex-direction:row;gap:18px;text-align:left}
  .hero-foot{flex-direction:column;align-items:flex-start;gap:16px}
  .hero-meta{text-align:left}
  .rf-top{grid-template-columns:1fr 1fr;gap:30px 40px}
  .rf-brand{grid-column:1/-1}
  .reveal-footer{padding-top:clamp(72px,11vh,120px)}
}
@media(max-width:720px){
  .nav-links{position:fixed;inset:78px 0 auto 0;flex-direction:column;gap:0;background:rgba(244,241,233,.98);
    backdrop-filter:blur(16px);border-bottom:1px solid var(--line);padding:8px var(--gut) 24px;
    transform:translateY(-130%);transition:transform .45s var(--ease);pointer-events:none}
  .menu-open .nav-links{transform:none;pointer-events:auto}
  .nav-links a{padding:16px 0;font-size:1rem;border-bottom:1px solid var(--line-soft);width:100%;color:var(--ink)}
  .burger{display:flex}
  .gallery:not(.pinned) .gal-item{width:80vw}
  .journal-grid{grid-template-columns:1fr}
  .scroll-cue{display:none}
}
@media(prefers-reduced-motion:reduce){
  *{animation:none!important;scroll-behavior:auto!important}
  .r-fade,.r-mask{opacity:1!important;transform:none!important;clip-path:none!important;transition:none!important}
  .px img,.project-media img,.matter-media img,.studio-img img,.transition img,.closing img{height:100%!important;transform:none!important;top:0!important}
  .scroll-cue{display:none}
}
"""

JS = r"""
(function(){
  var body=document.body,header=document.querySelector('header.nav');
  var reduce=window.matchMedia('(prefers-reduced-motion:reduce)').matches;

  // lenis: soft inertial scroll. Native scroll if reduced-motion or the lib is unavailable.
  var lenis=null;
  if(!reduce && window.Lenis){
    lenis=new Lenis({lerp:0.085,wheelMultiplier:1,smoothWheel:true});
    (function lraf(t){lenis.raf(t);requestAnimationFrame(lraf);})();
  }

  function onScroll(){ if(window.scrollY>30){header.classList.add('scrolled');}else{header.classList.remove('scrolled');} }
  window.addEventListener('scroll',onScroll,{passive:true});onScroll();

  var burger=document.querySelector('.burger');
  if(burger){burger.addEventListener('click',function(){body.classList.toggle('menu-open');
    burger.setAttribute('aria-expanded',body.classList.contains('menu-open'));});}
  // in-page anchors scroll smoothly through lenis (falls back to native)
  document.querySelectorAll('a[href^="#"]').forEach(function(a){
    a.addEventListener('click',function(e){
      body.classList.remove('menu-open');
      var href=a.getAttribute('href');if(href.length<2)return;
      var el=document.querySelector(href);
      if(el&&lenis){e.preventDefault();lenis.scrollTo(el,{offset:0,duration:1.4});}
    });
  });

  // reveals: scroll-driven via getBoundingClientRect (robust with clip-path masks,
  // which collapse the box and break IntersectionObserver)
  var revealEls=[].slice.call(document.querySelectorAll('.r-fade,.r-mask'));
  function reveal(){
    if(reduce){revealEls.forEach(function(el){el.classList.add('in');});revealEls.length=0;return;}
    var vh=window.innerHeight;
    for(var i=revealEls.length-1;i>=0;i--){
      if(revealEls[i].getBoundingClientRect().top < vh*0.9){revealEls[i].classList.add('in');revealEls.splice(i,1);}
    }
  }

  // hero on load
  requestAnimationFrame(function(){requestAnimationFrame(function(){body.classList.add('loaded');
    document.querySelectorAll('.hero .r-mask,.hero .r-fade').forEach(function(el){el.classList.add('in');});reveal();});});

  // active nav
  var navmap={};document.querySelectorAll('.nav-links a').forEach(function(a){navmap[a.getAttribute('href')]=a;});
  if('IntersectionObserver' in window){
    var so=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){var l=navmap['#'+e.target.id];
      if(l){Object.keys(navmap).forEach(function(k){navmap[k].classList.remove('active');});l.classList.add('active');}}});},
      {rootMargin:'-45% 0px -50% 0px'});
    document.querySelectorAll('section[id]').forEach(function(s){so.observe(s);});
  }

  function clamp(a,v,b){return v<a?a:v>b?b:v;}

  // pinned horizontal gallery: vertical scroll pans the frames sideways (desktop only;
  // touch keeps a natural swipe). The section grows tall enough to hold the horizontal travel.
  var gallery=document.querySelector('.gallery'),gtrack=document.querySelector('.gal-track'),
      gprog=document.querySelector('.gal-progress span'),gcount=document.querySelector('.gal-count'),
      gN=document.querySelectorAll('.gal-item').length,gDist=0;
  function sizeGallery(){
    if(!gallery||!gtrack)return;
    if(reduce||window.innerWidth<=900){gallery.classList.remove('pinned');gallery.style.height='';gtrack.style.transform='';return;}
    gallery.classList.add('pinned');gtrack.style.transform='';
    gDist=Math.max(0,gtrack.scrollWidth-window.innerWidth);
    gallery.style.height=(window.innerHeight+gDist)+'px';
  }

  // parallax + gallery pan + reveal, on one throttled scroll loop
  var pxEls=reduce?[]:[].slice.call(document.querySelectorAll('[data-px]'));
  var ticking=false;
  function frame(){
    var vh=window.innerHeight;
    if(!reduce){
      pxEls.forEach(function(el){
        var r=el.getBoundingClientRect();
        if(r.bottom<-100||r.top>vh+100)return;
        var prog=(r.top+r.height/2-vh/2)/vh;
        var amt=parseFloat(el.getAttribute('data-px'))||8;
        el.style.transform='translate3d(0,'+(prog*amt*-1).toFixed(2)+'%,0)';
      });
      if(gallery&&gtrack&&gallery.classList.contains('pinned')){
        var sc=gallery.offsetHeight-vh;
        var gp=sc>0?clamp(0,(-gallery.getBoundingClientRect().top)/sc,1):0;
        gtrack.style.transform='translate3d('+(-gp*gDist).toFixed(2)+'px,0,0)';
        if(gprog)gprog.style.transform='scaleX('+gp.toFixed(4)+')';
        if(gcount)gcount.textContent=(''+clamp(1,Math.floor(gp*gN)+1,gN)).padStart(2,'0')+' / '+(''+gN).padStart(2,'0');
      }
    }
    reveal();
    ticking=false;
  }
  window.addEventListener('scroll',function(){if(!ticking){ticking=true;requestAnimationFrame(frame);}},{passive:true});
  window.addEventListener('resize',function(){if(!ticking){ticking=true;requestAnimationFrame(frame);}});
  sizeGallery();frame();

  // reveal footer: reserve scroll space equal to the fixed footer's height so the page
  // (a card with rounded base) lifts away to uncover it
  var page=document.querySelector('.page'),rfoot=document.querySelector('.reveal-footer'),giant=document.querySelector('.rf-giant');
  function fitGiant(){
    if(!giant)return;
    giant.style.fontSize='200px';
    var w=giant.scrollWidth;
    if(w>0)giant.style.fontSize=(200*window.innerWidth/w).toFixed(2)+'px';
  }
  function sizeFooter(){
    fitGiant();
    sizeGallery();
    if(!page||!rfoot)return;
    page.style.marginBottom=rfoot.offsetHeight+'px';
    if(lenis)lenis.resize();
  }
  sizeFooter();
  window.addEventListener('resize',sizeFooter);
  if(document.fonts&&document.fonts.ready){document.fonts.ready.then(sizeFooter);}
  window.addEventListener('load',sizeFooter);

  // contact form
  var form=document.getElementById('cform');
  if(form){form.addEventListener('submit',function(ev){ev.preventDefault();if(!form.checkValidity()){form.reportValidity();return;}
    form.style.display='none';var ok=document.getElementById('cform-success');if(ok){ok.classList.add('show');}});}
})();
"""


def render(c):
    s = c["studio"]
    nav_links = "".join(f'<a href="{esc(n["href"])}">{esc(n["label"])}</a>' for n in c["nav"])
    brand = f'<span class="bt">{esc(s["name"])}</span><span class="bs">{esc(s["tagline"])}</span>'
    header = f"""
<header class="nav"><div class="nav-inner">
  <a class="brand" href="#top" aria-label="{esc(s['name_full'])}">{brand}</a>
  <nav class="nav-links" aria-label="Primary">{nav_links}</nav>
  <button class="burger" aria-label="Menu" aria-expanded="false"><span></span><span></span><span></span></button>
</div></header>"""

    # hero: full bleed
    h = c["hero"]
    hero = f"""
<section class="hero" id="top">
  <div class="hero-bg"><picture>
    <source type="image/webp" srcset="assets/{h['image']}-960.webp 960w, assets/{h['image']}.webp 1536w" sizes="100vw">
    <img src="assets/{h['image']}.webp" alt="{esc(h['image_alt'])}" fetchpriority="high" decoding="async"></picture></div>
  <div class="hero-inner">
    <h1 class="hero-word r-fade">{esc(h['wordmark'])}</h1>
    <div class="hero-foot">
      <p class="hero-statement r-fade" data-delay="1">{esc(h['statement'])}</p>
      <div class="hero-meta r-fade" data-delay="2"><span class="label">{esc(h['meta_left'])}</span><span class="label">{esc(h['meta_right'])}</span></div>
    </div>
  </div>
  <div class="scroll-cue"><span>{esc(h['scroll'])}</span><span class="ln"></span></div>
</section>"""

    # work: full-bleed project showcase
    w = c["work"]
    projects = ""
    for p in w["projects"]:
        projects += f"""<article class="project">
      <div class="project-bg"><picture>
        <source type="image/webp" srcset="assets/{p['image']}-960.webp 960w, assets/{p['image']}.webp 1536w" sizes="100vw">
        <img src="assets/{p['image']}.webp" alt="{esc(p['alt'])}" data-px="5" loading="lazy" decoding="async"></picture></div>
      <div class="project-cap"><div class="pwrap">
        <div class="r-fade"><span class="pno">{esc(p['no'])}</span><h3 class="pname">{esc(p['name'])}</h3></div>
        <div class="pmeta r-fade" data-delay="1"><span>{esc(p['location'])}</span><span>{esc(p['year'])}</span></div>
      </div></div>
    </article>"""
    work = f"""
<section id="work">
  <div class="wrap work-index r-fade"><span class="label"><span class="dot">/</span> {esc(w['index'])}</span><div class="years">{esc(w['years'])}</div></div>
  <div class="projects">{projects}</div>
</section>"""

    # philosophy
    ph = c["philosophy"]
    plines = (f'<p class="l1">{esc(ph["lines"][0])}</p>'
              + "".join(f'<p class="lx r-fade" data-delay="{i+1}">{esc(l)}</p>' for i, l in enumerate(ph["lines"][1:])))
    philosophy = f"""
<section class="philo" id="philosophy"><div class="wrap"><div class="philo-lines r-fade">{plines}</div></div></section>"""

    # gallery
    g = c["gallery"]
    items = ""
    for i, im in enumerate(g["images"]):
        items += (f'<div class="gal-item"><figure><img src="assets/{im["src"]}-960.webp" alt="{esc(im["caption"])}" loading="lazy" decoding="async"></figure>'
                  f'<figcaption><span class="cn">{i+1:02d}</span>{esc(im["caption"])}</figcaption></div>')
    gallery = f"""
<section class="gallery" id="gallery">
  <div class="gallery-sticky">
    <div class="gallery-head"><span class="label"><span class="dot">/</span> {esc(g['label'])}</span><span class="gal-count">01 / {len(g['images']):02d}</span></div>
    <div class="gal-track">{items}</div>
    <div class="gal-progress"><span></span></div>
  </div>
</section>"""

    # materiality
    m = c["materiality"]
    mlist = "".join(f'<li><span class="mn">{i+1:02d}</span>{esc(mat)}</li>' for i, mat in enumerate(m["materials"]))
    mmedia = "".join(f'<figure class="px"><img src="assets/{im["src"]}-800.webp" alt="{esc(im["alt"])}" data-px="7" loading="lazy" decoding="async"></figure>' for im in m["images"])
    materiality = f"""
<section class="matter section" id="materiality" style="padding-block:var(--section)"><div class="wrap"><div class="matter-grid">
  <div class="r-fade"><span class="label"><span class="dot">/</span> Materiality</span>
    <h2 class="serif" style="font-size:clamp(2.2rem,4.4vw,3.4rem);margin:20px 0 22px;max-width:14ch">{esc(m['heading'])}</h2>
    <p class="body-copy">{esc(m['body'])}</p>
    <ul class="matter-list">{mlist}</ul></div>
  <div class="matter-media r-mask">{mmedia}</div>
</div></div></section>"""

    # transition
    t = c["transition"]
    transition = f"""
<section class="transition" aria-hidden="false"><img src="assets/{t['src']}.webp" alt="{esc(t['alt'])}" data-px="12" loading="lazy" decoding="async">
  <span class="tw r-fade">{esc(t['word'])}</span></section>"""

    # studio
    st = c["studio_section"]
    sparas = "".join(f"<p>{esc(p)}</p>" for p in st["paragraphs"])
    studio = f"""
<section class="section" id="studio" style="padding-block:var(--section)"><div class="wrap"><div class="studio-grid">
  <div class="studio-img px r-mask"><img src="assets/{st['image']}-800.webp" srcset="assets/{st['image']}-800.webp 800w, assets/{st['image']}.webp 1280w" sizes="(max-width:900px) 100vw, 45vw" alt="{esc(st['image_alt'])}" data-px="8" loading="lazy" decoding="async"></div>
  <div class="studio-copy r-fade"><span class="label"><span class="dot">/</span> {esc(st['label'])}</span>
    <h2 class="heading">{esc(st['heading'])}</h2>{sparas}
    <div class="studio-sign"><span class="nm">{esc(st['director'])}</span><span class="rl">{esc(st['role'])}</span></div></div>
</div></div></section>"""

    # journal
    j = c["journal"]
    entries = ""
    for e in j["entries"]:
        entries += f"""<article class="entry r-fade">
      <div class="entry-media px"><img src="assets/{e['image']}-800.webp" alt="{esc(e['alt'])}" loading="lazy" decoding="async"></div>
      <div class="entry-meta"><span class="cn">{esc(e['no'])}</span><span>{esc(e['kind'])}</span><span>{esc(e['date'])}</span></div>
      <h3>{esc(e['title'])}</h3></article>"""
    journal = f"""
<section class="journal section" id="journal" style="padding-block:var(--section)"><div class="wrap">
  <div class="work-intro r-fade" style="border:0;padding-bottom:0"><span class="label"><span class="dot">/</span> {esc(j['label'])}</span><p class="lead">{esc(j['intro'])}</p></div>
  <div class="journal-grid">{entries}</div>
</div></section>"""

    # contact
    ct = c["contact"]
    topts = "".join(f"<option>{esc(o)}</option>" for o in ct["project_types"])
    bopts = "".join(f"<option>{esc(o)}</option>" for o in ct["budget_ranges"])
    contact = f"""
<section class="section" id="contact" style="padding-block:var(--section)"><div class="wrap"><div class="contact-grid">
  <div class="contact-copy r-fade">
    <h2 class="serif">{esc(ct['heading'])}</h2>
    <p class="body-copy">{esc(ct['body'])}</p>
    <div class="contact-detail">
      <div class="cd"><span class="ck">Email</span><a href="mailto:{esc(s['email'])}">{esc(s['email'])}</a></div>
      <div class="cd"><span class="ck">Studio</span><p>{esc(s['street'])}<br>{esc(s['suburb'])}, {esc(s['region'])}</p></div>
    </div>
  </div>
  <div class="r-fade" data-delay="1">
    <form class="cform" id="cform" novalidate>
      <div class="field"><label for="f-name">Name</label><input id="f-name" name="name" type="text" required placeholder="Your name"></div>
      <div class="field"><label for="f-email">Email</label><input id="f-email" name="email" type="email" required placeholder="you@email.com"></div>
      <div class="field"><label for="f-type">Project type</label><select id="f-type" name="type">{topts}</select></div>
      <div class="field"><label for="f-budget">Budget range</label><select id="f-budget" name="budget">{bopts}</select></div>
      <div class="field full"><label for="f-message">Message</label><textarea id="f-message" name="message" placeholder="A few words about your project, site or timeline"></textarea></div>
      <div class="submit-row"><button class="btn-line" type="submit">{esc(ct['submit'])} <span aria-hidden="true">&rarr;</span></button></div>
    </form>
    <div class="cform-success" id="cform-success"><p>Thank you. Your enquiry has reached the studio, and we'll reply personally.</p></div>
  </div>
</div></div></section>"""

    # closing
    cl = c["closing"]
    closing = f"""
<section class="closing"><img src="assets/{cl['image']}.webp" srcset="assets/{cl['image']}-960.webp 960w, assets/{cl['image']}.webp 1536w" sizes="100vw" alt="{esc(cl['alt'])}" data-px="6" loading="lazy" decoding="async">
  <p class="cw r-fade">{esc(cl['line'])}</p></section>"""

    # reveal footer
    ft = c["footer"]
    foot_nav = "".join(f'<a href="{esc(n["href"])}">{esc(n["label"])}</a>' for n in c["nav"])
    footer = f"""
<footer class="reveal-footer">
  <div class="rf-top">
    <div class="rf-brand">
      <span class="bt">{esc(s['name'])}</span>
      <p>{esc(s['discipline'])} in {esc(s['city'])}. New work taken on by enquiry, a few at a time.</p>
      <a class="email" href="mailto:{esc(s['email'])}">{esc(s['email'])}</a>
    </div>
    <div class="rf-col"><h4>Index</h4>{foot_nav}</div>
    <div class="rf-col"><h4>Studio</h4><p>{esc(s['street'])}<br>{esc(s['suburb'])}<br>{esc(s['region'])}</p>
      <a href="tel:{esc(s['phone_link'])}" style="margin-top:12px">{esc(s['phone_display'])}</a></div>
  </div>
  <div class="rf-meta">
    <span>&copy; 2026 {esc(s['name_full'])}. {esc(s['city'])}.</span>
    <a class="totop" href="#top">Back to top &uarr;</a>
  </div>
  <div class="rf-giant" aria-hidden="true">{esc(s['name'])}</div>
</footer>"""

    content = (hero + work + philosophy + gallery + materiality + transition
               + studio + journal + contact + closing)
    body = header + f'<div class="page">{content}</div>' + footer

    title_tag = f"{s['name_full']}: {s['discipline']} in {s['city']}"
    desc = (f"{s['name_full']} is a boutique residential architecture practice in {s['city']}. "
            "Quiet, material, considered work. Selected projects, studio and journal.")

    return f"""<!doctype html>
<!--
  Atelier Architecture: fictional brand, built as a design & front-end portfolio piece.
  A digital exhibition. Single static file: inline CSS/JS, no framework, no runtime deps.
  Structural motion (reveals, parallax, draggable gallery) in dependency-free vanilla JS.
  Content generated from content.json via build.py.
-->
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title_tag)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="noindex">
<meta name="theme-color" content="#EFEAE1">
<link rel="canonical" href="{esc(s['url'])}/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(s['name_full'])}">
<meta property="og:title" content="{esc(title_tag)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(s['url'])}/">
<meta property="og:image" content="{esc(s['url'])}/assets/showstopper.webp">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%23EFEAE1'/%3E%3Ctext x='16' y='23' font-family='Georgia,serif' font-size='20' fill='%237B5448' text-anchor='middle'%3EA%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300..500&family=Inter+Tight:wght@400;500;600&display=swap" rel="stylesheet">
<style>
{CSS}
</style>
</head>
<body>
<a class="skip" href="#contact">Skip to contact</a>
{body}
<script src="lenis.min.js"></script>
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
