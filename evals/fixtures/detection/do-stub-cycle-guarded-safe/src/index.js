// Safe shape: the classes do call each other, but every hop checks an explicit
// depth budget before the next stub call, so the ping-pong is bounded.

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
    const depth = Number(request.headers.get("x-hop-depth") || 0);
    if (depth >= 2) {
      return new Response("hop limit reached", { status: 429 });
    }
    const id = this.env.TASK_RUNNER.idFromName(sessionId);
    return this.env.TASK_RUNNER.get(id).fetch("https://do/run", {
      headers: {
        "x-session-id": sessionId,
        "x-hop-depth": String(depth + 1),
        authorization: auth,
      },
    });
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
    const depth = Number(request.headers.get("x-hop-depth") || 0);
    if (depth >= 2) {
      return new Response("hop limit reached", { status: 429 });
    }
    const id = this.env.SESSION_COORDINATOR.idFromName(sessionId);
    return this.env.SESSION_COORDINATOR.get(id).fetch("https://do/ack", {
      headers: {
        "x-session-id": sessionId,
        "x-hop-depth": String(depth + 1),
        authorization: auth,
      },
    });
  }
}
