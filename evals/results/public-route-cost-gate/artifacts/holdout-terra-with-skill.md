Scope inspected: `inputs/README.md`, `inputs/wrangler.jsonc`, `inputs/index.js`; static scan (`CFDOC-CONFIG-D1-NO-MIGRATIONS`, `CFDOC-CONFIG-NO-OBSERVABILITY`) treated as non-cost leads only.
Scope not inspected: deployed cache/rules, traffic, D1 query plan and `rows_read` measurements, schema/indexes, billing plan/account settings.
Docs refreshed: [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/), [Workers Static Assets routing](https://developers.cloudflare.com/workers/static-assets/binding/).

Release verdict: BLOCK

| host + route family | discovery evidence | known valid corpus | accepted keyspace | first rejection/validation | inherited work | route-specific work | per-hit product unit | first prevention boundary |
|---|---|---|---|---|---|---|---|---|
| `chronicle.example/` | sitemap and configured `chronicle.example/*` route | one homepage | exact `/` | path comparison before D1 | URL parse | static HTML | no D1 operation evidenced | route match |
| `chronicle.example/sitemap.xml` | direct code route | one sitemap | exact `/sitemap.xml` | path comparison before D1 | URL parse | static XML | no D1 operation evidenced | route match |
| `chronicle.example/timeline` | homepage footer link | one timeline endpoint; underlying `entries` corpus is growing and stated as 80,000 entries | exact `/timeline` | none before D1 | URL parse | `GROUP BY year` with `COUNT(*)` over `entries`, then JSON response | one D1 query; billed `rows_read` is unmeasured and corpus-proportional | none |
| `chronicle.example/*` excluding the above | configured wildcard route | none | all other paths | `pathname !== "/timeline"` before D1 | URL parse | 404 | no D1 operation evidenced | route match |

Discovery gaps: `/timeline` is absent from the sitemap but is publicly discoverable through the homepage footer (`README.md:3`, `index.js:5`).

Exposure scenario: the evidence-selected uncached path is:

`anonymous /timeline requests × D1 rows_read per aggregate query`

Every request reaches `SELECT … COUNT(*) … GROUP BY` (`index.js:7-9`); there is no cache configuration (`README.md:3`, `wrangler.jsonc`). D1 bills queries by rows read, including rows scanned rather than merely returned, and the supplied corpus is already 80,000 entries and growing. The exact rows-read multiplier needs the query plan or query `meta.rows_read`, but a public corpus-wide aggregate on every hit is sufficient launch-blocking exposure. [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/)

Closure conditions: materialize the timeline JSON during the data publish/update workflow, then serve the static `/timeline` asset with asset-first routing (`run_worker_first: false`/unset). Cache/static key: `/timeline`; refresh owner: the publishing pipeline; on materialization failure: retain the prior published snapshot or return an error—never fall back to the live aggregate. The residual public D1 meter must be zero; measure the update job’s `rows_read` separately. Static assets are served before Worker execution by default when an asset matches. [Workers Static Assets configuration](https://developers.cloudflare.com/workers/static-assets/binding/)

### Severity: critical — Public request executes a growing-corpus D1 aggregate

- Category: cost footgun
- Evidence: `inputs/index.js:6-10` permits anonymous `/timeline` requests and executes the aggregate; `inputs/README.md:3` states an 80,000-entry, growing corpus and no cache; `inputs/wrangler.jsonc:5-6` exposes the Worker on the public hostname with a D1 binding.
- Why it matters: repeated bot, crawler, or ordinary requests each invoke broad live database work. D1 rows read are billable/scanned rows; the single D1 database also processes queries serially, so the same traffic can create availability pressure.
- Fix: move the aggregate out of request handling. Generate `/timeline` as a static JSON/HTML asset at publish time and ensure asset-first routing; do not retain a live-query fallback.
- Cost / trade-off: replaces request-volume × corpus-work exposure with controlled update-time work. It introduces freshness equal to the publishing cadence and requires an explicit update/invalidation owner.
- Verify: run `EXPLAIN QUERY PLAN` and record `meta.rows_read` for the current implementation; after remediation, load `/timeline` repeatedly and confirm zero D1 queries/rows read from public traffic and that a failed publish retains the prior asset.
- Source basis: [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/); [D1 limits and concurrency](https://developers.cloudflare.com/d1/platform/limits/); [Workers Static Assets routing](https://developers.cloudflare.com/workers/static-assets/binding/).
- Confidence: high
