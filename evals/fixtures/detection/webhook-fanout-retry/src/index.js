import { broadcastEvent } from "./fanout.js";

export default {
  async fetch(request, env, ctx) {
    if (request.method !== "POST") {
      return new Response("method not allowed", { status: 405 });
    }
    const event = await request.json();
    const subscribers = await env.SUBSCRIBERS.get("all", "json");
    ctx.waitUntil(broadcastEvent(subscribers ?? [], event));
    return Response.json({ accepted: true });
  },
};
