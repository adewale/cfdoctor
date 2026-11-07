// Hand-rolled module-scope memo: same per-isolate lifetime problem as the
// cachified lruCache adapter, without the library.
const rankMemo = new Map<string, { value: unknown; expires: number }>()

export async function getWeeklyRankings(env: Env) {
  const hit = rankMemo.get('weekly')
  if (hit && hit.expires > Date.now()) return hit.value
  const rows = await env.DB.prepare(
    'SELECT slug, COUNT(id) AS reads FROM post_reads WHERE created_at > ?1 GROUP BY slug',
  )
    .bind(new Date(Date.now() - 7 * 86400 * 1000).toISOString())
    .all()
  rankMemo.set('weekly', { value: rows, expires: Date.now() + 1000 * 60 * 10 })
  return rows
}
