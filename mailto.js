/* Email CTAs: on click, let the native mailto: open the visitor's mail client
   AND always copy the address to the clipboard, showing a little "Email copied"
   bubble that pops at the cursor. The copy is the graceful fallback: browsers
   give no signal for whether a mailto opened a client, so we always copy, and
   anyone without a working client still has the address in one click. Purely a
   progressive enhancement over the plain mailto: links; if this file never
   loads they still work. Self-hosted, no third-party calls. */
(function(){
  "use strict";
  var mails = [].slice.call(document.querySelectorAll('.js-mail'));
  if(!mails.length) return;
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // polite live region so screen readers hear the copy confirmation
  var live = document.createElement('div');
  live.setAttribute('aria-live','polite');
  live.setAttribute('role','status');
  live.style.cssText = 'position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0';
  document.body.appendChild(live);

  function addr(el){
    var u = el.getAttribute('data-u'), d = el.getAttribute('data-d');
    if(u && d) return u + String.fromCharCode(64) + d;
    var h = el.getAttribute('href') || '';
    return h.indexOf('mailto:') === 0 ? h.slice(7).split('?')[0] : '';
  }

  function copy(text){
    if(navigator.clipboard && window.isSecureContext){
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function(res, rej){
      var ta = document.createElement('textarea');
      ta.value = text; ta.setAttribute('readonly','');
      ta.style.cssText = 'position:fixed;top:0;left:0;opacity:0;pointer-events:none';
      document.body.appendChild(ta); ta.focus(); ta.select();
      try{ document.execCommand('copy') ? res() : rej(); }
      catch(e){ rej(e); }
      document.body.removeChild(ta);
    });
  }

  function bubble(x, y){
    var b = document.createElement('div');
    b.className = 'mail-pop';
    b.textContent = 'Email copied';
    var ck = document.createElement('span');
    ck.textContent = ' ✓';
    ck.style.color = '#E39A63';
    b.appendChild(ck);
    b.style.cssText = 'position:fixed;left:' + x + 'px;top:' + y + 'px;' +
      'z-index:2147483647;pointer-events:none;' +
      'font-family:"Martian Mono",ui-monospace,SFMono-Regular,monospace;' +
      'font-size:.7rem;font-weight:400;letter-spacing:.06em;text-transform:uppercase;' +
      'background:#0E0D0C;color:#F3EEE3;padding:.5em .85em;border-radius:999px;' +
      'box-shadow:0 10px 30px -10px rgba(0,0,0,.55);white-space:nowrap;will-change:transform,opacity';
    document.body.appendChild(b);
    var done = function(){ if(b.parentNode) b.parentNode.removeChild(b); };

    if(reduce || typeof b.animate !== 'function'){
      b.style.transform = 'translate(-50%,-150%)';
      b.style.transition = 'opacity .28s';
      b.style.opacity = '0';
      requestAnimationFrame(function(){ b.style.opacity = '1'; });
      setTimeout(function(){ b.style.opacity = '0'; setTimeout(done, 300); }, 1000);
      return;
    }
    // rise + settle, hold, then pop like a bubble (scale up + fade)
    var anim = b.animate([
      { transform:'translate(-50%,-115%) scale(.65)', opacity:0 },
      { transform:'translate(-50%,-152%) scale(1.06)', opacity:1, offset:.32 },
      { transform:'translate(-50%,-150%) scale(1)', opacity:1, offset:.46 },
      { transform:'translate(-50%,-162%) scale(1)', opacity:1, offset:.8 },
      { transform:'translate(-50%,-178%) scale(1.45)', opacity:0 }
    ], { duration:1300, easing:'cubic-bezier(.19,1,.22,1)' });
    anim.onfinish = done; anim.oncancel = done;
    setTimeout(done, 1600);   // safety: remove even if the animation is interrupted (e.g. tab blur)
  }

  mails.forEach(function(el){
    var h = el.getAttribute('href') || '';
    if(h === '' || h === '#'){ var a0 = addr(el); if(a0) el.setAttribute('href','mailto:' + a0); }
    el.addEventListener('click', function(ev){
      var a = addr(el);
      if(!a) return;                 // unresolved: let the browser handle the href
      // Do both: the native mailto fires (opens a mail client if one is set),
      // and we always copy the address so anyone without a working client
      // still has it. No preventDefault, so the mail client still opens.
      var x = ev.clientX, y = ev.clientY;
      if(!x && !y){ var r = el.getBoundingClientRect(); x = r.left + r.width/2; y = r.top + 6; }
      copy(a).then(function(){
        live.textContent = 'Email address copied to clipboard';
        bubble(x, y);
      }).catch(function(){ /* clipboard unavailable; the mailto still fired */ });
    });
  });
})();
