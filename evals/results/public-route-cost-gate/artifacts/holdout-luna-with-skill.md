## Cloudflare Doctor focused triage

Scope inspected: `inputs/README.md`, `inputs/wrangler.jsonc`, `inputs/index.js`, plus one static-scan attempt (scanner unavailable).
Scope not inspected: deployed traffic, account plan, D1 query plan/`rows_read`, cache state, schema, indexes, and account exports.
Docs refreshed: [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/), [Workers Caching configuration](https://developers.cloudflare.com/workers/cache/configuration/), [Static Assets Worker routing](https://developers.cloudflare.com/workers/static-assets/routing/worker-script/), [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/).

Release verdict: BLOCK

| host + route family | discovery evidence | known valid corpus | accepted keyspace | first rejection/validation | inherited work | route-specific work | per-hit product unit | first prevention boundary |
|---|---|---:|---|---|---|---|---|---|
| `chronicle.example/*` → `/` | Sitemap seed; homepage footer links `/timeline` | 1 homepage | Exact `/` | Path check at line 5 | URL parsing | Returns HTML; no D1 | Worker request/CPU only | Current path check |
| `chronicle.example/*` → `/timeline` | Linked from `/`; omitted from sitemap | Growing 80,000-entry `entries` corpus | Exact `/timeline`; no key | Path check at line 6, after no dependency work | URL parsing | Unconditional `GROUP BY` + `COUNT(*)` over `entries` | D1 rows read per request; exact count unmeasured, but corpus-scale by query shape | None before D1 execution |
| `chronicle.example/*` → `/sitemap.xml` | Explicit route in code | 1 generated document | Exact `/sitemap.xml` | Path check at line 4 | URL parsing | Returns inline XML; no D1 | Worker request/CPU only | Current path check |
| `chronicle.example/*` → other paths | Wrangler wildcard route; arbitrary paths can reach Worker | None | All other path strings | Exact-path rejection at line 6 | URL parsing | 404; no D1 | Worker request/CPU only | Current path check |

Discovery gaps: `/timeline` is a public route found through the homepage footer but absent from the sitemap. The wildcard route also exposes generated/unknown paths that are not represented by the sitemap, though they currently reject before D1.

Exposure scenario: the route is uncached in supplied configuration. The relevant equation is:

`anonymous request count × D1 rows_read per request`

The aggregate has no filter and computes a corpus-wide yearly count on every `/timeline` request. With an 80,000-entry corpus, the logical work is corpus-proportional; the exact billed `rows_read` value requires D1 metadata or measurement. D1 bills queries by rows read, and full scans count scanned rows. Workers request/CPU usage is additional. See [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/) and [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/).

Closure conditions:

- Move the yearly aggregate to publish/update time and serve a bounded materialized result, preferably a static JSON/asset or a small maintained table.
- Ensure every public request path avoids the broad aggregate, including future route variants and alternate public hosts if any exist.
- If retaining a live D1 lookup, provide a query plan and measured `rows_read` proving bounded work per request.
- A cache may reduce repeated origin executions only if placed before the Worker/dependency and its fill, expiry, purge, bypass, location, and concurrent-miss behavior are bounded. It is not sufficient by itself to close this broad-query finding.
- If Workers Caching is used, configure an explicit TTL/invalidation owner and account for the documented request charge on cache hits; cache hits bypass Worker execution and CPU, but do not eliminate the Worker request charge. See [Workers Caching configuration](https://developers.cloudflare.com/workers/cache/configuration/) and [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/).
- Static delivery is the cleaner boundary for the materialized timeline; Cloudflare serves matching Static Assets before invoking the Worker by default. See [Static Assets Worker routing](https://developers.cloudflare.com/workers/static-assets/routing/worker-script/).

### Severity: critical — Public corpus-scale D1 aggregate on every timeline request

- Category: cost footgun
- Evidence: `inputs/index.js:7-10`; `inputs/README.md` identifies a growing 80,000-entry corpus; `inputs/wrangler.jsonc:5-6` exposes the Worker publicly with a D1 binding.
- Why it matters: anonymous requests to `/timeline` repeatedly execute `SELECT ... COUNT(*) ... GROUP BY` across the entire corpus. D1 bills rows read, so request volume multiplies corpus-scale database work. There is no cache or materialization boundary in the supplied configuration.
- Fix: materialize the yearly counts during publish/update operations and serve the result as a static asset or bounded record. Do not rely on crawler controls, sitemap omission, or post-execution caching as the primary fix.
- Cost / trade-off: removes recurring corpus-proportional D1 reads and reduces Worker CPU; adds publish/update complexity and an explicit freshness/invalidation owner. Exact current bill cannot be estimated without request volume, plan, and measured `rows_read`.
- Verify: deploy the materialized path, request `/timeline` repeatedly, confirm no D1 query executes on reads, and inspect D1 row metrics/`meta.rows_read`.
- Source basis: [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/); [Static Assets Worker routing](https://developers.cloudflare.com/workers/static-assets/routing/worker-script/).
- Confidence: high

## Run summary with cost proxies

- Hot paths: `/timeline`, homepage, sitemap, wildcard 404s.
- Expensive primitives per user action: `/timeline` performs one corpus-scale D1 aggregate; exact `rows_read` unknown.
- Retry/fanout/circuit-breaker posture: no retries or fanout shown.
- Cache map: no cache configuration or response cache headers supplied; `/timeline` is uncached by evidence.

## Recommended next actions

1. Block launch until the aggregate is materialized or otherwise proven bounded and removed from the anonymous request path.
2. Measure D1 `rows_read` for the current query and record expected request-volume scenarios.
3. Add `/timeline` to discovery metadata only after its cost-safe implementation is deployed.

## Questions / evidence needed

- What is the D1 schema/query plan, including indexes?
- What are the expected anonymous requests per day/month and the Workers plan?
- What freshness requirement determines the materialization update cadence?