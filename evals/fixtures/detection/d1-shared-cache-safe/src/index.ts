import { getReadTotals, getNavLinks } from './shared-cache'
import { getLayeredTotals } from './layered-totals'

export default {
  async fetch(_request: Request, env: Env) {
    const totals = await getReadTotals(env)
    const layered = await getLayeredTotals(env)
    const nav = await getNavLinks()
    return Response.json({ totals, layered, nav })
  },
}
