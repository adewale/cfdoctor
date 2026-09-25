// Turnstile Spin canonical contract: gate, don't replace. The existing handler runs only
// after Siteverify returns success for the expected action and an allowlisted hostname.
const EXPECTED_ACTION = "signup";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method !== "POST" || url.pathname !== "/signup") {
      return env.ASSETS.fetch(request);
    }
    const form = await request.formData();
    if (!(await passesTurnstile(request, env, form.get("cf-turnstile-response")))) {
      return new Response("forbidden", { status: 403 });
    }
    return Response.redirect(new URL("/welcome.html", url), 303);
  },
};

async function passesTurnstile(request, env, token) {
  const expectedHostnames = new Set(
    (env.TURNSTILE_HOSTNAMES ?? "").split(",").map((hostname) => hostname.trim()).filter(Boolean),
  );
  if (typeof token !== "string" || token.length === 0 || token.length > 2048 || expectedHostnames.size === 0) {
    return false;
  }
  let result;
  try {
    const response = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      signal: AbortSignal.timeout(10_000),
      body: new URLSearchParams({
        secret: env.TURNSTILE_SECRET,
        response: token,
        remoteip: request.headers.get("CF-Connecting-IP") ?? "",
      }),
    });
    if (!response.ok) return false;
    result = await response.json();
  } catch {
    return false;
  }
  return result.success === true && result.action === EXPECTED_ACTION && expectedHostnames.has(result.hostname);
}
