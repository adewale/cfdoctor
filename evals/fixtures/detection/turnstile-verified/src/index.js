// Correctly-wired Turnstile: the widget is rendered AND the token is verified
// server-side with the secret key before the submission is accepted.

export default {
  async fetch(request, env) {
    if (request.method === "POST") {
      const form = await request.formData();
      const token = form.get("cf-turnstile-response");

      const params = new URLSearchParams();
      params.append("secret", env.TURNSTILE_SECRET_KEY);
      params.append("response", token);
      const outcome = await fetch(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        { method: "POST", body: params },
      );
      const result = await outcome.json();
      if (!result.success) {
        return new Response("failed challenge", { status: 403 });
      }
      return new Response("ok");
    }

    return new Response(
      `<!doctype html>
<html>
  <head>
    <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
  </head>
  <body>
    <form method="POST">
      <input name="email" type="email" />
      <div class="cf-turnstile" data-sitekey="0x4AAAAAAABkMYinukE8nzY"></div>
      <button type="submit">Sign up</button>
    </form>
  </body>
</html>`,
      { headers: { "content-type": "text/html" } },
    );
  },
};
