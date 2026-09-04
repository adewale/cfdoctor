import { getPullRequest, listPullRequests, getIssue, queryMetrics, listMonitors } from "@acme/tools";

// Static named imports: only the five tools this Worker uses reach the bundle,
// and their schemas are built per call rather than at module load.
const TOOLS = new Map(
  [getPullRequest, listPullRequests, getIssue, queryMetrics, listMonitors].map((tool) => [tool.name, tool]),
);

export class AgentThread {
  constructor(ctx, env) {
    this.ctx = ctx;
    this.env = env;
  }

  async fetch(request) {
    const url = new URL(request.url);
    if (request.method !== "POST") return new Response("method not allowed", { status: 405 });
    const tool = TOOLS.get(url.searchParams.get("tool"));
    if (!tool) return new Response("unknown tool", { status: 404 });
    const result = await tool.execute(await request.json(), this.env);
    this.ctx.storage.sql.exec("INSERT INTO turns (tool, result) VALUES (?, ?)", tool.name, JSON.stringify(result));
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
