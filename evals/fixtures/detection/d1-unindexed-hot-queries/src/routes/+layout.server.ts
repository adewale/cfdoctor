// Site-wide navigation data: this loader runs for every page on the site,
// before any page-specific loader executes.
export async function load({ platform }) {
  const db = platform.env.DB;
  const latest = await db.prepare("SELECT MAX(year) AS year FROM reimbursement").first();
  const states = await db
    .prepare("SELECT DISTINCT state_id FROM reimbursement WHERE year = ?1 ORDER BY state_id")
    .bind(latest.year)
    .all();
  return {
    nav: {
      latestYear: latest.year,
      stateIds: states.results.map((row) => row.state_id),
    },
  };
}
