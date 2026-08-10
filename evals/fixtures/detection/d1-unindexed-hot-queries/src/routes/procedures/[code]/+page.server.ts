export async function load({ params, platform, url }) {
  const year = Number(url.searchParams.get("year") ?? "2026");
  const rows = await platform.env.DB
    .prepare(
      "SELECT state_id, amount_cents FROM reimbursement WHERE hcpcs_code_id = ?1 AND year = ?2 ORDER BY state_id",
    )
    .bind(params.code, year)
    .all();
  return { code: params.code, year, rows: rows.results };
}
