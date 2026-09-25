// Correctly-wired credential handling: every secret-named variable is READ from a
// binding or a request, never committed as a literal. Nothing here should be reported
// as a committed credential. The Turnstile verifier follows the Turnstile Spin canonical
// contract, so the Turnstile checks must stay silent too.

const EXPECTED_ACTION = "signup";

export default {
  async fetch(request, env) {
    const form = await request.formData();
    const token = form.get("cf-turnstile-response");
    const apiKey = env.SERVICE_API_KEY;
    const signingSecret = env.SESSION_SIGNING_SECRET;

    const verified = await verifyToken(request, env, token);
    if (!verified) {
      return new Response("failed challenge", { status: 403 });
    }

    return Response.json({ ok: true, keyed: Boolean(apiKey && signingSecret) });
  },
};

async function verifyToken(request, env, token) {
  const expectedHostnames = new Set(
    (env.TURNSTILE_HOSTNAMES ?? "").split(",").map((hostname) => hostname.trim()).filter(Boolean),
  );
  if (typeof token !== "string" || token.length === 0 || token.length > 2048 || expectedHostnames.size === 0) {
    return false;
  }
  const body = new URLSearchParams();
  body.append("secret", env.TURNSTILE_SECRET_KEY);
  body.append("response", token);
  body.append("remoteip", request.headers.get("CF-Connecting-IP") ?? "");
  let outcome;
  try {
    const result = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
      method: "POST",
      body,
      signal: AbortSignal.timeout(10_000),
    });
    if (!result.ok) return false;
    outcome = await result.json();
  } catch {
    return false;
  }
  return outcome.success === true
    && outcome.action === EXPECTED_ACTION
    && expectedHostnames.has(outcome.hostname);
}
