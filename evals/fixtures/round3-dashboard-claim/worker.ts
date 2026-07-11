export default {
  async fetch() {
    return new Response("ok", { headers: { "Cache-Control": "no-store" } });
  },
};
