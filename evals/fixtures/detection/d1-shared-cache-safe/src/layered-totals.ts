// L1 isolate memory in front of the shared KV layer: a cold isolate falls
// back to KV, and only a KV miss re-runs the D1 aggregate.
const l1 = new Map<string, unknown>()

export async function getLayeredTotals(env: Env) {
  const cached = l1.get('totals')
  if (cached) return cached
  const stored = await env.CACHE_KV.get('cache:totals', 'json')
  if (stored) {
    l1.set('totals', stored)
    return stored
  }
  const rows = await env.DB.prepare(
    'SELECT slug, SUM(read_ms) AS total_ms FROM post_reads GROUP BY slug',
  ).all()
  await env.CACHE_KV.put('cache:totals', JSON.stringify(rows), {
    expirationTtl: 1800,
  })
  l1.set('totals', rows)
  return rows
}
