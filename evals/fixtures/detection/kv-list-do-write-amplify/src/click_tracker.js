import { DurableObject } from "cloudflare:workers";

export class ClickTracker extends DurableObject {
  async fetch(request) {
    const hit = await request.json();
    const now = Date.now();
    // One storage write per dimension, per click.
    await this.ctx.storage.put(`hit:${hit.slug}:${now}`, 1);
    await this.ctx.storage.put(`country:${hit.slug}:${hit.country}`, now);
    await this.ctx.storage.put(`referrer:${hit.slug}:${hit.referrer}`, now);
    await this.ctx.storage.put(`agent:${hit.slug}:${hit.agent}`, now);
    await this.ctx.storage.put(`last:${hit.slug}`, now);
    return new Response("ok");
  }
}
