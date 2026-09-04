// Worker + Durable Object for per-thread agent runs. The tool registry is
// loaded through a dynamic import of the package root, which materialises the
// whole namespace (every schema) even when the thread only needs one tool.
export class AgentThread {
  constructor(ctx, env) {
    this.ctx = ctx;
    this.env = env;
  }

  async fetch(request) {
    const url = new URL(request.url);
    if (request.method !== "POST") return new Response("method not allowed", { status: 405 });
    const tools = await import("@acme/tools");
    const wanted = url.searchParams.get("tool");
    const tool = Object.values(tools).find((entry) => entry.name === wanted);
    if (!tool) return new Response("unknown tool", { status: 404 });
    const input = tool.parameters.parse(await request.json());
    const result = await tool.execute(input, this.env);
    this.ctx.storage.sql.exec("INSERT INTO turns (tool, result) VALUES (?, ?)", wanted, JSON.stringify(result));
    return Response.json(result);
  }
}

export default {
  async fetch(request, env) {
    const bearer = request.headers.get("authorization");
    if (!bearer || !(await validateToken(env, bearer))) return new Response("unauthorized", { status: 401 });
    const threadId = new URL(request.url).pathname.split("/")[2];
    if (!threadId) return new Response("missing thread", { status: 400 });
    const stub = env.THREAD.get(env.THREAD.idFromName(threadId));
    return stub.fetch(request);
  },
};

async function validateToken(env, token) {
  return Boolean(token);
}
