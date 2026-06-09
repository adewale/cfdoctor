import { DurableObject } from "cloudflare:workers";

export class PresenceTracker extends DurableObject {
  async fetch(request) {
    const body = await request.json();
    await this.ctx.storage.put(`seen:${body.userId}`, Date.now());
    if ((await this.ctx.storage.getAlarm()) === null) {
      await this.ctx.storage.setAlarm(Date.now() + 30_000);
    }
    // Re-read the entire roster on every heartbeat.
    const seen = await this.ctx.storage.list({ prefix: "seen:" });
    return Response.json({ online: seen.size });
  }

  async alarm() {
    const seen = await this.ctx.storage.list({ prefix: "seen:" });
    await this.publishRoster(seen);
    await this.ctx.storage.setAlarm(Date.now() + 30_000);
  }

  async publishRoster(seen) {
    const roster = [...seen.keys()];
    await fetch("https://rooms.internal.invalid/roster", {
      method: "POST",
      body: JSON.stringify(roster),
    });
  }
}
