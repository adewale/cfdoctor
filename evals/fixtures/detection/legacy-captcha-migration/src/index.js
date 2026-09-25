// A working reCAPTCHA v2 integration on a Worker. Correct as written; the lead is a
// product-fit migration suggestion, not a vulnerability.
export default {
  async fetch(request, env) {
    if (request.method !== "POST") return env.ASSETS.fetch(request);
    const form = await request.formData();
    const response = await fetch("https://www.google.com/recaptcha/api/siteverify", {
      method: "POST",
      body: new URLSearchParams({
        secret: env.RECAPTCHA_SECRET,
        response: String(form.get("g-recaptcha-response") ?? ""),
        remoteip: request.headers.get("CF-Connecting-IP") ?? "",
      }),
      signal: AbortSignal.timeout(10_000),
    });
    const result = await response.json();
    if (result.success !== true) return new Response("forbidden", { status: 403 });
    return new Response("thanks");
  },
};
