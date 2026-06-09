export default {
  async fetch(request) {
    return new Response("pong");
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil(fetch("https://api.statusboard.invalid/heartbeat", { method: "POST" }));
  },
};
