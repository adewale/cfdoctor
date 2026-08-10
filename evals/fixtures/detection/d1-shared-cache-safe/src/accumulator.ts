// Function-local accumulator: created per call, so it cannot cache anything
// across requests and must not be read as a per-isolate cache.
export async function totalsBySlug(env: Env) {
  const out = new Map<string, number>()
  const rows = await env.DB.prepare(
    'SELECT slug, SUM(read_ms) AS total_ms FROM post_reads GROUP BY slug',
  ).all<{ slug: string; total_ms: number }>()
  rows.results.forEach((row) => {
    out.set(row.slug, row.total_ms)
  })
  return out
}
