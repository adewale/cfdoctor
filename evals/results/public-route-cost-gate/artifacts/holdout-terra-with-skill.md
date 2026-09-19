Scope inspected: `inputs/README.md`, `inputs/wrangler.jsonc`, `inputs/index.js`; static scan (`CFDOC-CONFIG-D1-NO-MIGRATIONS` and observability leads were out of scope for this cost-only triage).

Scope not inspected: deployed cache/rules, traffic, D1 query plan, `rows_read` measurements, billing plan, and account settings.

Docs refreshed: [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/), [Workers Static Assets configuration](https://developers.cloudflare.com/workers/static-assets/binding/).

Release verdict: BLOCK

| host + route family | discovery evidence | known valid corpus | accepted keyspace | first rejection/validation | inherited work | route-specific work | per-hit product unit | first prevention boundary |
|---|---|---|---|---|---|---|---|---|
| `chronicle.example/` | Sitemap | `/` | Exact path | `pathname === "/"` | Worker request parsing | HTML footer response | No D1 operation | N/A |
| `chronicle.example/sitemap.xml` | Explicit handler | `/sitemap.xml` | Exact path | Exact-path branch | Worker request parsing | Static XML response | No D1 operation | N/A |
| `chronicle.example/timeline` | Homepage footer link | `/timeline` | Exact path | Exact-path branch | Worker request parsing | D1 `GROUP BY year` and `COUNT(*)` over `entries` | D1 rows read; corpus-proportional count is unmeasured | None |
| `chronicle.example/<all other paths>` | Catch-all Worker route | Unknown | All other paths | Before D1: `pathname !== "/timeline"` | Worker request parsing | 404 | No D1 operation | Path rejection |

Discovery gaps: `/timeline` is absent from the sitemap but is publicly discoverable through the homepage footer in `index.js:5`.

Exposure scenario: no cache configuration is supplied, so every anonymous `/timeline` request executes the aggregate. D1 exposure is:

`anonymous /timeline request count × D1 rows read per aggregate`

The exact `rows_read` is unknown without a query plan/measurement, but the visible `GROUP BY`/`COUNT(*)` over the growing `entries` corpus establishes corpus-proportional live work on every hit. Repeated requests to the same URL remain repeated D1 work.

Closure conditions: before launch, remove the aggregate from the public request path. Generate `/timeline`’s JSON at publish/update time and serve it as a static asset at the exact `/timeline` key, with the publisher owning refresh/invalidation. Its error path must return a static 404/error response without D1. Measure the resulting public path to confirm zero D1 reads; if any live lookup remains, supply its query plan and `rows_read` measurement proving bounded work.

### Severity: high — Public timeline performs a corpus-wide D1 aggregate on every hit

- Category: cost footgun
- Evidence: `inputs/index.js:6-10` accepts public `/timeline` and executes `SELECT ... COUNT(*) ... FROM entries GROUP BY year`; `inputs/README.md:3` states the corpus is growing and already has 80,000 entries; `inputs/wrangler.jsonc:5-6` publicly routes the domain and binds D1.
- Why it matters: D1 bills queries by rows read. Cloudflare defines rows read as rows scanned, including rows scanned to produce a smaller result. The aggregate is reached before any cache or static-delivery boundary, so crawlers or ordinary repeated traffic can repeatedly incur corpus-scale reads.
- Fix: Materialize the year-count JSON when entries are published/updated, then deploy it as the `/timeline` static asset. Keep the public read path asset-first; do not retain the broad aggregate as a cache-fill path.
- Cost / trade-off: Public reads no longer execute D1; cost moves to bounded publish-time recomputation. This adds a content-publish/update step and requires explicit refresh ownership. An index alone is not sufficient closure for this aggregate without a plan and measured bounded reads.
- Verify: Run `EXPLAIN QUERY PLAN` and record D1 `meta.rows_read` for the current query as baseline; after the change, request `/timeline` repeatedly and confirm no D1 query/row-read increment. Test the asset’s update and missing-asset error behavior.
- Source basis: [Cloudflare D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/) documents rows-read billing and scan semantics; [Cloudflare Static Assets](https://developers.cloudflare.com/workers/static-assets/binding/) documents asset-first routing, where matching static assets are served without invoking the Worker.
- Confidence: high