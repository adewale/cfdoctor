// Signup Worker that renders a Cloudflare Turnstile widget but never verifies
// the token server-side. The POST handler writes to D1 based purely on the
// client-side widget, which does not protect the form.

export default {
  async fetch(request, env) {
    if (request.method === "POST") {
      const form = await request.formData();
      const email = form.get("email");
      // BUG: the token is never validated server-side; the form is accepted on trust.
      await env.DB.prepare("INSERT INTO signups (email) VALUES (?)").bind(email).run();
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
