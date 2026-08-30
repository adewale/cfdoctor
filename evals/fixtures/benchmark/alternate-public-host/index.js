export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const route = /^\/product\/([^/]+)\/?$/.exec(url.pathname);
    if (!route) {
      return new Response('<a href="/product/first">First product</a>', {
        headers: { "content-type": "text/html" },
      });
    }
    const slug = decodeURIComponent(route[1]);
    const product = await env.DB.prepare(
      "SELECT slug, name, summary FROM products WHERE slug = ?1 LIMIT 1"
    ).bind(slug).first();
    return Response.json(product);
  },
};
