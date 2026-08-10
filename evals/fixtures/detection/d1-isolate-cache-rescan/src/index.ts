import { getBlogPostReadCounts, getTotalReaderCount } from './read-counts'
import { getWeeklyRankings } from './rankings'

export default {
  async fetch(_request: Request, env: Env) {
    const reads = await getBlogPostReadCounts(env)
    const total = await getTotalReaderCount(env)
    const weekly = await getWeeklyRankings(env)
    return Response.json({ reads, total, weekly })
  },
  // The cron keeps isolates warm; each cold isolate it lands on re-runs the
  // full-table aggregates because the memo lives in isolate memory.
  async scheduled(_event: ScheduledEvent, env: Env) {
    await getBlogPostReadCounts(env)
    await getTotalReaderCount(env)
  },
}
