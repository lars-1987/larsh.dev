/* larsh.dev redesign — shared chrome behaviour for content pages.
   Everything is feature-guarded so a page can omit any piece without erroring. */
(() => {
  'use strict';
  const $ = (s, c) => (c || document).querySelector(s);
  const $$ = (s, c) => [...(c || document).querySelectorAll(s)];
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* smooth scroll */
  let lenis = null;
  if (!reduced && window.Lenis) {
    lenis = new Lenis({ duration: 1.1, smoothWheel: true });
    const raf = t => { lenis.raf(t); requestAnimationFrame(raf); };
    requestAnimationFrame(raf);
  }
  $$('a[href^="#"]').forEach(a => a.addEventListener('click', e => {
    const h = a.getAttribute('href') || '';
    if (h.length < 2 || h[0] !== '#') return; // ignore "#" and JS-rewritten (mailto) hrefs
    const t = $(h);
    if (!t) return;
    e.preventDefault();
    closeMenu();
    if (lenis) lenis.scrollTo(t, { offset: 0 });
    else t.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth' });
  }));

  /* nav morph */
  const nav = $('#nav'), pill = $('#navpill'), btn = $('#navbtn');
  function closeMenu() { if (!nav) return; nav.classList.remove('open'); btn.setAttribute('aria-expanded', 'false'); setH(); }
  const setH = () => {
    if (!nav) return;
    const open = nav.classList.contains('open');
    pill.style.height = open ? pill.scrollHeight + 'px' : '60px';
    $$('.menu, .mfoot', pill).forEach(el => el.toggleAttribute('inert', !open));
  };
  if (nav) {
    setH();
    btn.addEventListener('click', () => {
      nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', nav.classList.contains('open'));
      setH();
    });
    addEventListener('resize', setH);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeMenu(); });
    document.addEventListener('click', e => { if (!nav.contains(e.target)) closeMenu(); });
  }

  /* melbourne clock */
  const clock = $('#clock');
  if (clock) {
    const fmt = new Intl.DateTimeFormat('en-AU', { timeZone: 'Australia/Melbourne', hour: '2-digit', minute: '2-digit', hour12: false });
    const tick = () => { clock.textContent = 'MELB ' + fmt.format(new Date()); };
    tick(); setInterval(tick, 30000);
  }
  const yr = $('#year'); if (yr) yr.textContent = new Date().getFullYear();

  /* section reveals */
  const io = new IntersectionObserver(entries => {
    entries.forEach(en => { if (en.isIntersecting) { en.target.classList.add('on'); io.unobserve(en.target); } });
  }, { rootMargin: '0px 0px -10% 0px' });
  $$('[data-r]').forEach(el => io.observe(el));

  /* footer uncover spacing */
  const foot = $('.foot');
  if (foot) {
    const sizeFoot = () => document.documentElement.style.setProperty('--footh', foot.offsetHeight + 'px');
    sizeFoot(); addEventListener('resize', sizeFoot);
  }

  /* email chips (obfuscated address) + toast */
  const toast = $('#toast');
  let toastT;
  const say = msg => { if (!toast) return; toast.textContent = msg; toast.classList.add('on'); clearTimeout(toastT); toastT = setTimeout(() => toast.classList.remove('on'), 2600); };
  const addr = el => `${el.dataset.u}@${el.dataset.d}`;
  $$('.js-mail').forEach(el => {
    const a = addr(el);
    const label = $('.addr', el);
    if (label) label.textContent = a;
    if (el.tagName === 'A') el.setAttribute('href', 'mailto:' + a); // real mailto, no #contact in the status bar
    el.addEventListener('click', e => {
      e.preventDefault();
      location.href = `mailto:${a}`;
      if (navigator.clipboard) navigator.clipboard.writeText(a).then(() => say('Email copied, and opening your mail app'), () => {});
    });
  });
})();
