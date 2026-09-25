// Intentionally incomplete Turnstile setup: the widget renders, but the handler never
// redeems the token at Siteverify, so any string (or no token) is accepted.
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "POST" && url.pathname === "/subscribe") {
      const form = await request.formData();
      const email = String(form.get("email") ?? "");
      if (!form.get("cf-turnstile-response")) {
        return new Response("missing challenge", { status: 400 });
      }
      await env.SUBSCRIBERS.put(email, JSON.stringify({ subscribedAt: Date.now() }));
      return Response.redirect(new URL("/thanks.html", url), 303);
    }
    return env.ASSETS.fetch(request);
  },
};
