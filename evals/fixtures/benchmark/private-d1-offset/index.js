// Synthetic fixture; the authenticated account is fixed to the fixture owner.
export default {
  async fetch(request, env) {
    if (!env.FIXTURE_SESSION_TOKEN || request.headers.get("authorization") !== `Bearer ${env.FIXTURE_SESSION_TOKEN}`) {
      return new Response("Unauthorized", { status: 401 });
    }
    const url = new URL(request.url);
    if (request.method !== "GET" || url.pathname !== "/archive") return new Response("Not found", { status: 404 });
    const rawOffset = url.searchParams.get("offset") ?? "0";
    if (!/^\d{1,5}$/.test(rawOffset)) return new Response("Invalid offset", { status: 400 });
    const offset = Number(rawOffset);
    if (offset > 10_000) return new Response("Invalid offset", { status: 400 });
    const page = await env.DB.prepare("SELECT id, created_at FROM archive WHERE owner_id = ? ORDER BY created_at DESC, id DESC LIMIT 20 OFFSET ?").bind("fixture-owner", offset).all();
    return Response.json({ rows: page.results, nextOffset: offset < 10_000 ? offset + 20 : null });
  },
};
