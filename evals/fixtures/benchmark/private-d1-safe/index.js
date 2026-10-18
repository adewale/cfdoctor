// Synthetic fixture. SESSION_GATE is an imaginary supplied-contract test double.
export function startDashboardPolling(sessionToken, signal) {
  const expiresAt = Date.now() + 3_600_000;
  let calls = 0;
  let timer;
  const poll = () => {
    if (signal.aborted || Date.now() >= expiresAt || calls >= 60) {
      clearInterval(timer);
      return;
    }
    if (document.visibilityState === "visible") {
      calls += 1;
      void fetch("/dashboard", { headers: { authorization: `Bearer ${sessionToken}` }, signal });
    }
  };
  timer = setInterval(poll, 60_000);
  signal.addEventListener("abort", () => clearInterval(timer), { once: true });
  poll();
}

export default {
  async fetch(request, env) {
    if (request.method !== "GET" || new URL(request.url).pathname !== "/dashboard") {
      return new Response("Not found", { status: 404 });
    }
    const authorization = request.headers.get("authorization");
    if (!authorization) return new Response("Unauthorized", { status: 401 });
    try {
      const admission = await env.SESSION_GATE.fetch(new Request("https://fixture-session-gate.internal/consume", {
        method: "POST", headers: { authorization },
      }));
      if (admission.status !== 200) {
        const status = admission.status === 429 ? 429 : admission.status === 401 ? 401 : 503;
        return new Response("Session rejected", { status });
      }
      const gate = await admission.json();
      if (gate.allowed !== true || gate.ownerId !== "fixture-owner") {
        return new Response("Unauthorized", { status: 401 });
      }
    } catch {
      return new Response("Session gate unavailable", { status: 503 });
    }
    const summary = await env.DB.prepare("SELECT COUNT(*) AS summary_rows FROM dashboard_summary").first();
    const note = await env.DB.prepare("SELECT * FROM notes WHERE id = ? LIMIT 1").bind(1).first();
    return Response.json({ summary, note });
  },
};
