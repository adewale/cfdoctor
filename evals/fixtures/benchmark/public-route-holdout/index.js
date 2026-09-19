export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/sitemap.xml") return new Response("<urlset><url><loc>https://chronicle.example/</loc></url></urlset>");
    if (url.pathname === "/") return new Response('<footer><a href="/timeline">Issue timeline</a></footer>', { headers: { "content-type": "text/html" } });
    if (url.pathname !== "/timeline") return new Response("Not found", { status: 404 });
    const years = await env.DB.prepare(
      "SELECT strftime('%Y', published_at) AS year, COUNT(*) AS n FROM entries GROUP BY year ORDER BY year DESC",
    ).all();
    return Response.json({ years: years.results });
  },
};
