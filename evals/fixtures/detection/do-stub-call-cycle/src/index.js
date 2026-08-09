// Intentionally bad: two Durable Objects re-trigger each other with no hop budget,
// idempotency key, or kill switch, and every hop re-reads the whole events table.
// The chain detaches through waitUntil, so per-invocation limits reset on each hop.

export class SessionCoordinator {
  constructor(ctx, env) {
    this.ctx = ctx;
    this.env = env;
  }

  async fetch(request) {
    const auth = request.headers.get("authorization");
    if (!auth) {
      return new Response("unauthorized", { status: 401 });
    }
    const sessionId = request.headers.get("x-session-id") || "unknown";
    const pending = this.ctx.storage.sql
      .exec("SELECT * FROM events ORDER BY created_at")
      .toArray();
    this.ctx.storage.sql.exec(
      "INSERT INTO events (session_id, kind, created_at) VALUES (?, 'tick', ?)",
      sessionId,
      Date.now(),
    );
    const id = this.env.TASK_RUNNER.idFromName(sessionId);
    this.ctx.waitUntil(
      this.env.TASK_RUNNER.get(id).fetch("https://do/run", {
        headers: { "x-session-id": sessionId, authorization: auth },
      }),
    );
    return Response.json({ pending: pending.length });
  }
}

export class TaskRunner {
  constructor(ctx, env) {
    this.ctx = ctx;
    this.env = env;
  }

  async fetch(request) {
    const auth = request.headers.get("authorization");
    if (!auth) {
      return new Response("unauthorized", { status: 401 });
    }
    const sessionId = request.headers.get("x-session-id") || "unknown";
    // "Report progress" back to the coordinator, which schedules more work here:
    // SessionCoordinator -> TaskRunner -> SessionCoordinator, forever.
    const id = this.env.SESSION_COORDINATOR.idFromName(sessionId);
    this.ctx.waitUntil(
      this.env.SESSION_COORDINATOR.get(id).fetch("https://do/notify", {
        headers: { "x-session-id": sessionId, authorization: auth },
      }),
    );
    return new Response("scheduled");
  }
}
