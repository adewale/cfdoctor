const page = (body) => new Response(`<nav><a href="/about">About</a><a href="/browse">Browse</a></nav>${body}`, {
  headers: { "content-type": "text/html; charset=utf-8" },
});

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/sitemap.xml") {
      return new Response("<urlset><url><loc>https://catalogue.example/</loc></url><url><loc>https://catalogue.example/browse</loc></url></urlset>", { headers: { "content-type": "application/xml" } });
    }

    // Shared layout work runs before routing on every HTML request.
    const total = await env.DB.prepare("SELECT COUNT(*) AS count FROM abstracts").first();
    if (url.pathname === "/") {
      const groups = await env.DB.prepare("SELECT field, COUNT(*) FROM abstracts GROUP BY field").all();
      return page(`<h1>${total.count} abstracts</h1>${groups.results.map((g) => `<a href="/browse?field=${g.field}">${g.field}</a>`).join("")}`);
    }
    if (url.pathname === "/browse") {
      const rows = await env.DB.prepare("SELECT id, title FROM abstracts ORDER BY published_at DESC LIMIT 50").all();
      return page(rows.results.map((row) => `<a href="/abstract/${row.id}">${row.title}</a>`).join(""));
    }
    if (url.pathname === "/about") return page(`<p>${total.count} records</p>`);
    if (url.pathname.startsWith("/abstract/")) {
      const id = url.pathname.slice(10);
      const row = await env.DB.prepare("SELECT * FROM abstracts WHERE id = ? LIMIT 1").bind(id).first();
      return row ? page(`<h1>${row.title}</h1>`) : new Response("Not found", { status: 404 });
    }
    return new Response("Not found", { status: 404 });
  },
};
