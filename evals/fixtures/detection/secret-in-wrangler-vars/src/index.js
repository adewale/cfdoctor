export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("method not allowed", { status: 405 });
    }
    const signature = request.headers.get("stripe-signature");
    if (!signature) {
      return new Response("missing signature", { status: 400 });
    }
    const payload = await request.json();
    return Response.json({ received: true, type: payload.type });
  },
};
