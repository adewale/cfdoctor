## Cloudflare Doctor focused triage

Scope inspected: [inputs/README.md](/private/var/folders/58/zrc_1j8n0f74krswfhmrtkrw0000gn/T/codex-ws-ytkxzatz/inputs/README.md), [inputs/wrangler.jsonc](/private/var/folders/58/zrc_1j8n0f74krswfhmrtkrw0000gn/T/codex-ws-ytkxzatz/inputs/wrangler.jsonc), [inputs/index.js](/private/var/folders/58/zrc_1j8n0f74krswfhmrtkrw0000gn/T/codex-ws-ytkxzatz/inputs/index.js), static scanner.

Scope not inspected: deployed configuration, account plan, traffic history, query plan, measured `rows_read`, cache status, DNS/WAF/rate limits.

Docs refreshed: [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/), [Workers Caching configuration](https://developers.cloudflare.com/workers/cache/configuration/), [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/).

Release verdict: BLOCK

| host + route family | discovery evidence | known valid corpus | accepted keyspace | first rejection/validation | inherited work | route-specific work | per-hit product unit | first prevention boundary |
|---|---|---|---|---|---|---|---|---|
| `chronicle.example/` | Homepage in sitemap; timeline footer link | `/` | Exact `/` | None | Worker invocation | Static HTML response | Worker request; no D1 | Static delivery or pre-Worker cache |
| `chronicle.example/sitemap.xml` | Supplied sitemap URL | `/sitemap.xml` | Exact `/sitemap.xml` | None | Worker invocation | Static XML response | Worker request; no D1 | Static delivery or pre-Worker cache |
| `chronicle.example/timeline` | Homepage footer link | `/timeline` | Exact `/timeline` | No method validation; path matches at line 6 | Worker invocation | D1 `COUNT`/`GROUP BY` over `entries` at [index.js:7-10](/private/var/folders/58/zrc_1j8n0f74krswfhmrtkrw0000gn/T/codex-ws-ytkxzatz/inputs/index.js:7) | D1 rows read per query; Worker request/CPU | Publish-time materialization/static delivery before Worker/D1 |
| `chronicle.example/*` other paths | Wrangler wildcard route; not linked by supplied discovery | None evidenced | Any non-matching path | Path rejection at [index.js:6](/private/var/folders/58/zrc_1j8n0f74krswfhmrtkrw0000gn/T/codex-ws-ytkxzatz/inputs/index.js:6) | Worker invocation | 404 response | Worker request | Static delivery or pre-Worker cache |

Discovery gaps: the sitemap omits `/timeline`; it was found through the homepage footer. No other generated route families are evidenced. Hostnames beyond `chronicle.example` and any deployment-specific routes are unknown.

Exposure scenario: this is an uncached, unbounded public-request path based on supplied configuration: `anonymous request count × D1 rows_read per request`. The exact `rows_read` value is unknown because no query plan or measurement was supplied, but the aggregate has no filter and runs against the growing 80,000-entry corpus on every `/timeline` request. D1 bills by rows read; Workers requests remain billed independently. On the paid plan, D1 includes 25 billion rows read monthly, then charges per additional million; Workers includes 10 million requests monthly, then charges per additional million. ([D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/), [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/))

Closure conditions: remove the aggregate from the request path by materializing the year counts at publish/update time and serving the result as a static artifact or bounded lookup. Add pre-Worker caching for `/timeline` if freshness permits, with an explicit key, TTL, and invalidation owner. Workers Caching checks before invoking the Worker; cache hits bypass Worker CPU but retain the documented request charge. ([Workers Caching configuration](https://developers.cloudflare.com/workers/cache/configuration/), [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/))

### Severity: critical — Public timeline performs corpus-scale D1 work per request

- Category: cost footgun
- Evidence: [README.md:3](/private/var/folders/58/zrc_1j8n0f74krswfhmrtkrw0000gn/T/codex-ws-ytkxzatz/inputs/README.md:3) identifies a growing 80,000-entry corpus; [index.js:5-10](/private/var/folders/58/zrc_1j8n0f74krswfhmrtkrw0000gn/T/codex-ws-ytkxzatz/inputs/index.js:5) exposes `/timeline` from the homepage and runs an unfiltered `COUNT`/`GROUP BY` query. Supporting scanner output: `CFDOC-CONFIG-NO-OBSERVABILITY`; no cache block exists in [wrangler.jsonc:1-7](/private/var/folders/58/zrc_1j8n0f74krswfhmrtkrw0000gn/T/codex-ws-ytkxzatz/inputs/wrangler.jsonc:1).
- Why it matters: every anonymous hit can cause corpus-proportional D1 reads before any cache or materialization boundary. D1 counts scanned rows, not merely returned rows. Repeated crawler or bot traffic can therefore amplify both D1 row usage and Worker request/CPU usage.
- Fix: precompute the yearly counts when entries are published or updated, then serve a static `/timeline` artifact or bounded stored result. Add an explicit pre-Worker cache as a secondary recrawl shield, with a defined TTL and invalidation process.
- Cost / trade-off: removes recurring corpus-scale D1 reads from public traffic; retains a small publish-time write/materialization cost. Caching reduces Worker/D1 execution on hits but still incurs the documented Worker request charge and has miss/refill costs.
- Verify: inspect the deployed query’s D1 `meta.rows_read`; verify `/timeline` has zero D1 calls in request handling; issue repeated requests from multiple cache locations and confirm cache hits do not invoke the Worker; test materialization after an entry update.
- Source basis: [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/), [Workers Caching configuration](https://developers.cloudflare.com/workers/cache/configuration/), [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/).
- Confidence: high

No other launch-blocking cost finding is confirmed from the supplied files.
