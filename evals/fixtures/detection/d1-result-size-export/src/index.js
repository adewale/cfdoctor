// Settings > Backups > Export: dumps every content table to JSON.
// Each table is read with one unbounded query, so the export breaks once any
// table (usually revision history) passes D1's maximum query result size.
const TABLES = ["posts", "revisions", "media"];

async function generateBackup(db) {
  const backup = {};
  for (const table of TABLES) {
    const { results } = await db.prepare(`SELECT * FROM ${table}`).all();
    backup[table] = results;
  }
  return backup;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.headers.get("authorization") !== `Bearer ${env.ADMIN_TOKEN}`) {
      return new Response("unauthorized", { status: 401 });
    }
    if (url.pathname === "/admin/backup/export") {
      return Response.json(await generateBackup(env.DB));
    }
    if (url.pathname === "/admin/revisions") {
      const { results } = await env.DB.prepare(
        "SELECT id, post_id, body, created_at FROM revisions ORDER BY created_at DESC",
      ).all();
      return Response.json(results);
    }
    return new Response("not found", { status: 404 });
  },
};
