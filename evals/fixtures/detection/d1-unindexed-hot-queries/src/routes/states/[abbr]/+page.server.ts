export async function load({ params, platform }) {
  const stats = await platform.env.DB
    .prepare(
      "SELECT hcpcs_code_id, SUM(amount_cents) AS total_cents FROM reimbursement WHERE state_id = ?1 GROUP BY hcpcs_code_id ORDER BY total_cents DESC",
    )
    .bind(params.abbr)
    .all();
  return { state: params.abbr, stats: stats.results };
}
