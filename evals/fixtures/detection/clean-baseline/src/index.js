export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/api/status") {
      return Response.json({ ok: true, version: env.APP_VERSION });
    }
    return new Response("not found", { status: 404 });
  },
};
