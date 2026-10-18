export async function load({ params, platform }) {
  const stats = await platform.env.DB
    .prepare(
      "SELECT r.hcpcs_code_id, SUM(r.amount_cents) AS total_cents FROM reimbursement r JOIN states s ON s.id = r.state_id WHERE s.abbreviation = ?1 GROUP BY r.hcpcs_code_id ORDER BY total_cents DESC",
    )
    .bind(params.abbr)
    .all();
  return { state: params.abbr, stats: stats.results };
}
