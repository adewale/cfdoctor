export async function load({ params, platform, url }) {
  const year = Number(url.searchParams.get("year") ?? "2026");
  const rows = await platform.env.DB
    .prepare(
      "SELECT r.state_id, r.amount_cents FROM reimbursement r JOIN hcpcs_codes h ON h.id = r.hcpcs_code_id WHERE h.code = ?1 AND r.year = ?2 ORDER BY r.state_id",
    )
    .bind(params.code, year)
    .all();
  return { code: params.code, year, rows: rows.results };
}
