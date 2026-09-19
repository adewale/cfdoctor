const canonical = /^[a-z0-9-]{1,48}$/;
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!url.pathname.startsWith("/category/")) return new Response("Not found", { status: 404 });
    const slug = url.pathname.slice(10);
    if (!canonical.test(slug)) return new Response("Not found", { status: 404 });
    const rows = await env.DB.prepare("SELECT title FROM articles WHERE category = ? LIMIT 50").bind(slug).all();
    return Response.json(rows.results);
  },
};
