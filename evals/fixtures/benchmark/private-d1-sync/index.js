// Synthetic unchanged input. This fixture is not deployed or run against D1.
const snapshot = Array.from({ length: 1_000 }, (_, id) => ({ id, value: `unchanged-${id}` }));

export default {
  fetch() {
    // Database work is available only through the internal scheduled handler.
    return new Response("Private scheduled task", { status: 403 });
  },
  async scheduled(_event, env) {
    // No content digest/diff check and no application retry loop.
    await env.DB.prepare("DELETE FROM snapshot").run();
    for (const row of snapshot) {
      await env.DB.prepare("INSERT INTO snapshot (id, value) VALUES (?, ?)").bind(row.id, row.value).run();
    }
  },
};
