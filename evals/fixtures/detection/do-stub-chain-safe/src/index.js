// Safe shape: the coordinator hands work to the runner exactly once per
// request and the runner never calls back, so there is no class-level cycle.
// SQL reads are bounded with WHERE and LIMIT.

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
    const next = this.ctx.storage.sql
      .exec("SELECT id, kind FROM events WHERE done = 0 ORDER BY created_at LIMIT 10")
      .toArray();
    const id = this.env.TASK_RUNNER.idFromName(sessionId);
    const response = await this.env.TASK_RUNNER.get(id).fetch("https://do/run", {
      method: "POST",
      body: JSON.stringify(next),
      headers: { "x-session-id": sessionId, authorization: auth },
    });
    return response;
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
    const batch = await request.json();
    const ids = JSON.stringify(batch.map((task) => task.id));
    this.ctx.storage.sql.exec(
      "UPDATE tasks SET state = 'done' WHERE id IN (SELECT value FROM json_each(?))",
      ids,
    );
    return new Response("processed");
  }
}
