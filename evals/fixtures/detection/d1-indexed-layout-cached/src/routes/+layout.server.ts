// Navigation data changes about once a year, so serve it cache-aside from KV
// under a versioned key; the CMS import job deletes the key to invalidate.
export async function load({ platform }) {
  const cached = await platform.env.NAV_CACHE.get("nav-data:v1", "json");
  if (cached) {
    return { nav: cached };
  }
  const db = platform.env.DB;
  const latest = await db.prepare("SELECT MAX(year) AS year FROM reimbursement").first();
  const states = await db
    .prepare("SELECT DISTINCT state_id FROM reimbursement WHERE year = ?1 ORDER BY state_id")
    .bind(latest.year)
    .all();
  const nav = {
    latestYear: latest.year,
    stateIds: states.results.map((row) => row.state_id),
  };
  await platform.env.NAV_CACHE.put("nav-data:v1", JSON.stringify(nav));
  return { nav };
}
