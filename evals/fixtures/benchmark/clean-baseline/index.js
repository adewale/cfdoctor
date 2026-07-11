export default {
  async fetch(request) {
    const url = new URL(request.url);
    if (request.method !== "GET" || url.pathname !== "/api/status") {
      return new Response("Not found", { status: 404 });
    }
    return Response.json({ ok: true }, {
      headers: { "Cache-Control": "no-store" },
    });
  },
};
