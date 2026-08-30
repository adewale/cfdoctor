export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const route = /^\/report\/([^/]+)\/?$/.exec(url.pathname);
    if (!route) {
      return new Response('<a href="/report/first">First report</a>', {
        headers: { "content-type": "text/html" },
      });
    }

    const cached = await caches.default.match(request);
    if (cached) return cached;

    const slug = decodeURIComponent(route[1]);
    const report = await env.DB.prepare(
      "SELECT slug, title, body FROM reports WHERE slug = ?1 LIMIT 1"
    ).bind(slug).first();
    if (!report) return new Response("not found", { status: 404 });

    const html = `<h1>${report.title}</h1><article>${report.body}</article>`;
    const response = new Response(html, {
      headers: { "content-type": "text/html", "cache-control": "public, max-age=60" },
    });
    ctx.waitUntil(Promise.all([
      caches.default.put(request, response.clone()),
      env.RENDERS.put(`reports/${slug}.html`, html),
    ]));
    return response;
  },
};
