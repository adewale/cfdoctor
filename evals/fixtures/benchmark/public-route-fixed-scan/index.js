export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/robots.txt") return new Response("User-agent: *\nAllow: /");
    if (url.pathname !== "/") return new Response("Not found", { status: 404 });
    const totals = await env.DB.prepare("SELECT kind, COUNT(*) AS n FROM events GROUP BY kind").all();
    return Response.json(totals.results);
  },
};
