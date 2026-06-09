import { DurableObject } from "cloudflare:workers";

export class MetricsRollup extends DurableObject {
  async fetch(request) {
    const session = request.headers.get("authorization");
    if (!session) {
      return new Response("unauthorized", { status: 401 });
    }
    const body = await request.json();
    await this.ctx.storage.put(`metric:${body.name}`, body.value);
    return Response.json({ ok: true });
  }

  async alarm() {
    const due = Date.now() + 30_000;
    await this.rollupCounters();
    await this.ctx.storage.setAlarm(due);
    if (this.verbose) {
      console.log("rollup sweep finished, rescheduled for", due);
    }
  }

  async rollupCounters() {
    const totals = await this.ctx.storage.get("totals");
    await this.ctx.storage.put("totals", totals ?? {});
  }
}

export default {
  async fetch(request, env) {
    const session = request.headers.get("authorization");
    if (!session) {
      return new Response("unauthorized", { status: 401 });
    }
    const id = env.ROLLUP.idFromName(new URL(request.url).hostname);
    return env.ROLLUP.get(id).fetch(request);
  },
};
