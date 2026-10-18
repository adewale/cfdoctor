// Synthetic fixture: no deployment, credential, or database execution is supplied.
export const POLL_INTERVAL_MS = 10_000;

export function startDashboardPolling(sessionToken, signal) {
  const timer = setInterval(() => {
    if (document.visibilityState === "visible") {
      void fetch("/notes", { headers: { authorization: `Bearer ${sessionToken}` }, signal });
    }
  }, POLL_INTERVAL_MS);
  signal.addEventListener("abort", () => clearInterval(timer), { once: true });
}

export default {
  async fetch(request, env) {
    if (!env.FIXTURE_SESSION_TOKEN || request.headers.get("authorization") !== `Bearer ${env.FIXTURE_SESSION_TOKEN}`) {
      return new Response("Unauthorized", { status: 401 });
    }
    const url = new URL(request.url);
    if (request.method !== "GET") return new Response("Method not allowed", { status: 405 });
    if (url.pathname === "/notes") {
      const notes = await env.DB.prepare("SELECT id, title, updated_at FROM notes WHERE is_archived = ? ORDER BY updated_at DESC LIMIT 20").bind(0).all();
      return Response.json(notes.results);
    }
    if (url.pathname === "/diagnostics") {
      const summary = await env.DB.prepare("SELECT COUNT(*) AS summary_rows FROM dashboard_summary").first();
      const note = await env.DB.prepare("SELECT * FROM notes WHERE id = ? LIMIT 1").bind(1).first();
      return Response.json({ summary, note });
    }
    return new Response("Not found", { status: 404 });
  },
};
