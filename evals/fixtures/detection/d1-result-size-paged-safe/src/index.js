// Settings > Backups > Export, paged: every table is read in rowid-keyset
// pages with an explicit column list, and a page that still hits D1's result
// size error is retried at half size. Counts use single-row aggregates.
const TABLES = {
  posts: "id, slug, title, body, status",
  revisions: "id, post_id, body, created_at",
  media: "id, filename, alt",
};
const FIRST_PAGE_ROWS = 500;
const maxAttempts = 6;

function isResultTooLarge(error) {
  return String(error?.message ?? error).includes("maximum response size");
}

async function readTable(db, table, columns) {
  const rows = [];
  let after = 0;
  let pageSize = FIRST_PAGE_ROWS;
  let attempts = 0;
  while (attempts < maxAttempts) {
    let page;
    try {
      page = await db
        .prepare(`SELECT rowid AS _rid, ${columns} FROM ${table} WHERE rowid > ? ORDER BY rowid LIMIT ?`)
        .bind(after, pageSize)
        .all();
    } catch (error) {
      if (!isResultTooLarge(error) || pageSize === 1) throw error;
      pageSize = Math.max(1, Math.floor(pageSize / 2));
      attempts += 1;
      continue;
    }
    for (const { _rid, ...row } of page.results) {
      rows.push(row);
      after = _rid;
    }
    if (page.results.length < pageSize) return rows;
  }
  throw new Error(`backup of ${table} exceeded ${maxAttempts} page-size reductions`);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.headers.get("authorization") !== `Bearer ${env.ADMIN_TOKEN}`) {
      return new Response("unauthorized", { status: 401 });
    }
    if (url.pathname === "/admin/backup/export") {
      const backup = {};
      for (const [table, columns] of Object.entries(TABLES)) {
        backup[table] = await readTable(env.DB, table, columns);
      }
      return Response.json(backup);
    }
    if (url.pathname === "/admin/backup/stats") {
      const stats = await env.DB.prepare("SELECT COUNT(*) AS revisions FROM revisions").first();
      return Response.json(stats);
    }
    return new Response("not found", { status: 404 });
  },
};
