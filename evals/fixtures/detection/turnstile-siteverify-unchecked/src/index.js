// Intentionally weak Siteverify handling:
// - falls back to Cloudflare's always-pass dummy secret when the real secret is unset;
// - trusts the HTTP status instead of `success`, and never checks action or hostname;
// - no token-size guard, no visitor IP, and no timeout on the Siteverify subrequest.
const TURNSTILE_SECRET_FALLBACK = "1x0000000000000000000000000000000AA";

export default {
  async fetch(request, env) {
    const form = await request.formData();
    const token = form.get("cf-turnstile-response");
    const body = new URLSearchParams({
      secret: env.TURNSTILE_SECRET ?? TURNSTILE_SECRET_FALLBACK,
      response: token,
    });
    const verdict = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
      method: "POST",
      body,
    });
    if (!verdict.ok) {
      return new Response("verification failed", { status: 403 });
    }
    return Response.json({ created: String(form.get("email") ?? "") });
  },
};
