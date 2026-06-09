export default {
  async fetch(request, env, ctx) {
    const page = await env.ASSETS.fetch(request);
    // Warm the related API response so the follow-up client call is fast.
    ctx.waitUntil(fetch(new URL("/api/related", request.url)));
    return page;
  },
};
