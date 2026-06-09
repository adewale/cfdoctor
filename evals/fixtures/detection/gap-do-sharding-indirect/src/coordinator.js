import { DurableObject } from "cloudflare:workers";

export class Coordinator extends DurableObject {
  async fetch(request) {
    const session = request.headers.get("authorization");
    if (!session) {
      return new Response("unauthorized", { status: 401 });
    }
    const body = await request.json();
    await this.ctx.storage.put(`order:${body.orderId}`, body);
    return Response.json({ ok: true });
  }
}
