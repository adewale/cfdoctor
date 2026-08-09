// Intentionally bad: the hot dashboard read runs an unbounded SELECT over a
// table that grows on every write, so SQLite storage rows read compound as the
// table grows even though request and duration meters stay small.

export class UsageLedger {
  constructor(ctx, env) {
    this.ctx = ctx;
    this.env = env;
  }

  async fetch(request) {
    const auth = request.headers.get("authorization");
    if (!auth) {
      return new Response("unauthorized", { status: 401 });
    }
    const url = new URL(request.url);
    if (url.pathname === "/record") {
      this.ctx.storage.sql.exec(
        "INSERT INTO usage_events (tenant, unit, created_at) VALUES (?, ?, ?)",
        request.headers.get("x-tenant-id"),
        1,
        Date.now(),
      );
      return new Response("recorded");
    }
    const events = this.ctx.storage.sql
      .exec("SELECT * FROM usage_events ORDER BY created_at DESC")
      .toArray();
    return Response.json({ total: events.length, events });
  }

  async alarm() {
    const cutoff = Date.now() - 86_400_000;
    const stale = this.ctx.storage.sql
      .exec("SELECT id FROM usage_events WHERE created_at < ? ORDER BY id LIMIT 100", cutoff)
      .toArray();
    const last = stale[stale.length - 1];
    if (last) {
      this.ctx.storage.sql.exec(
        "DELETE FROM usage_events WHERE created_at < ? AND id <= ?",
        cutoff,
        last.id,
      );
    }
  }
}
