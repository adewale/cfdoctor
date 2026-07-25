// Correctly-wired credential handling: every secret-named variable is READ from a
// binding or a request, never committed as a literal. Nothing here should be reported
// as a committed credential.

export default {
  async fetch(request, env) {
    const form = await request.formData();
    const token = form.get("cf-turnstile-response");
    const apiKey = env.SERVICE_API_KEY;
    const signingSecret = env.SESSION_SIGNING_SECRET;

    const verified = await verifyToken(token, env.TURNSTILE_SECRET_KEY);
    if (!verified) {
      return new Response("failed challenge", { status: 403 });
    }

    return Response.json({ ok: true, keyed: Boolean(apiKey && signingSecret) });
  },
};

async function verifyToken(token, secret) {
  const body = new URLSearchParams();
  body.append("secret", secret);
  body.append("response", token);
  const result = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST",
    body,
  });
  const outcome = await result.json();
  return outcome.success === true;
}
