/**
 * larsh.dev contact form → Resend.
 * Deployed as a Cloudflare Worker at api.larsh.dev. The static site (GitHub
 * Pages) posts JSON here; this calls Resend to email the enquiry through.
 *
 * The Resend key is NEVER in this file or wrangler.toml — it's a Worker secret:
 *   wrangler secret put RESEND_API_KEY
 */
export default {
  async fetch(request, env) {
    const origin = env.ALLOW_ORIGIN || 'https://larsh.dev';
    const cors = {
      'Access-Control-Allow-Origin': origin,
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Access-Control-Max-Age': '86400',
      'Vary': 'Origin',
    };

    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    if (request.method !== 'POST') return json({ error: 'Method not allowed' }, 405, cors);

    let data;
    try { data = await request.json(); } catch { return json({ error: 'Malformed request' }, 400, cors); }

    // Honeypot: bots fill the hidden "website" field. Pretend success, send nothing.
    if (data.website) return json({ ok: true }, 200, cors);

    const name = String(data.name || '').trim();
    const email = String(data.email || '').trim();
    const message = String(data.message || '').trim();

    if (!name || !email || !message) return json({ error: 'All fields are required.' }, 422, cors);
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return json({ error: 'That email looks off.' }, 422, cors);
    if (name.length > 120 || email.length > 200 || message.length > 5000)
      return json({ error: 'That is longer than the form allows.' }, 422, cors);

    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${env.RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: env.CONTACT_FROM,          // e.g. "larsh.dev <form@larsh.dev>"
        to: [env.CONTACT_TO],            // your inbox
        reply_to: email,                 // so you reply straight to the sender
        subject: `Project enquiry from ${name}`,
        text: `${message}\n\n— ${name} (${email})`,
      }),
    });

    if (!res.ok) {
      // don't leak Resend internals to the browser; log for the tail
      console.log('resend error', res.status, await res.text());
      return json({ error: 'Could not send right now.' }, 502, cors);
    }
    return json({ ok: true }, 200, cors);
  },
};

function json(obj, status, cors) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { 'Content-Type': 'application/json', ...cors },
  });
}
