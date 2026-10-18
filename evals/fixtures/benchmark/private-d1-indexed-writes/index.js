// Synthetic fixture; fixed IDs and update inputs, no live DB or credentials.
export default {
  fetch(request, env) {
    if (!env.FIXTURE_SESSION_TOKEN || request.headers.get("authorization") !== `Bearer ${env.FIXTURE_SESSION_TOKEN}`) {
      return new Response("Unauthorized", { status: 401 });
    }
    if (request.method !== "GET" || new URL(request.url).pathname !== "/status") {
      return new Response("Not found", { status: 404 });
    }
    return Response.json({ task: "scheduled-only", intervalMinutes: 15 });
  },
  async scheduled(event, env) {
    const syncState = Math.floor(event.scheduledTime / 900_000) % 2 === 0 ? "ready" : "waiting";
    for (let id = 1; id <= 1_000; id += 1) {
      await env.DB.prepare("UPDATE note_status SET sync_state = ? WHERE id = ?").bind(syncState, id).run();
    }
  },
};
