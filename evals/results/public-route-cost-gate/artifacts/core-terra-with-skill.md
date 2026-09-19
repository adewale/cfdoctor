Scope inspected: `inputs/README.md`, `inputs/wrangler.jsonc`, `inputs/index.js` (plus one static scan).
Scope not inspected: D1 schema/indexes, query plans/`rows_read` measurements, deployed cache headers, traffic, WAF/bot/rate-limit, and billing-plan settings.
Docs refreshed: [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/), [Workers Caching configuration](https://developers.cloudflare.com/workers/cache/configuration/), [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/).

Release verdict: BLOCK

| host + route family | discovery evidence | known valid corpus | accepted keyspace | first rejection/validation | inherited work | route-specific work | per-hit product unit | first prevention boundary |
|---|---|---:|---|---|---|---|---|---|
| `catalogue.example/sitemap.xml` | explicit route | 1 sitemap | exact path | route match | none | static XML | none | route match |
| `catalogue.example/` | sitemap | 1 | exact path | route match, but after DB call | `COUNT(*)` over `abstracts` | `GROUP BY field` aggregate | D1 rows read, corpus-proportional | materialize homepage metadata before request handling |
| `catalogue.example/browse` | sitemap/nav | 1 | exact path (+ arbitrary query strings) | route match, but after DB call | `COUNT(*)` over `abstracts` | ordered list query | corpus-wide count plus unknown rows read for list query | remove shared aggregate; verify index/plan for list |
| `catalogue.example/about` | shared navigation | 1 | exact path | route match, but after DB call | `COUNT(*)` over `abstracts` | none | D1 rows read, corpus-proportional | serve materialized count |
| `catalogue.example/abstract/:id` | browse-result links | 35,000 IDs | any suffix, including malformed/nonexistent IDs | no validation before DB call | `COUNT(*)` over `abstracts` | lookup by supplied `id` | corpus-wide count plus unknown lookup rows | validate canonical ID before any DB call; remove shared aggregate |
| `catalogue.example/*` other paths | Worker catch-all route | unknown | arbitrary paths | only after DB call | `COUNT(*)` over `abstracts` | 404 | D1 rows read, corpus-proportional | route-match/reject before DB |

Discovery gaps: `/about` is absent from the sitemap but appears in shared navigation; `/abstract/:id` is absent from the sitemap but appears in rendered browse links.

Exposure scenario: There is no cache configuration. Every non-sitemap request executes `COUNT(*)` before routing. Thus repeated exposure is:

`anonymous request count × rows_read of shared COUNT(*)`
plus the home page’s `GROUP BY` rows, and each route’s own query.

With 35,000 abstracts, the shared aggregate is explicitly corpus-scale work on every hit, including arbitrary 404s. Exact D1 rows read still needs `meta.rows_read` or a query plan; D1 bills rows scanned/read, not just returned rows. [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/)

Closure conditions: Move the total and homepage field counts to publish/update-time materialized data; reject unknown routes and malformed IDs before D1; and prove `/browse` and `/abstract/:id` reads are bounded with `EXPLAIN QUERY PLAN` plus observed `rows_read`. Add pre-Worker caching only for safely cacheable GET responses, with an explicit freshness/invalidation owner.

### Severity: high — Corpus-wide D1 aggregate on every public request

- Category: cost footgun
- Evidence: `inputs/index.js:12-13` executes `SELECT COUNT(*) AS count FROM abstracts` before every route; `:15` adds a full grouping aggregate for `/`; `:28` means unknown paths also pay the shared query. Scanner lead: `CFDOC-PERF-D1-SELECT-STAR` is not the material cost finding.
- Why it matters: Anonymous requests—including repeated crawler, bot, and invalid-path requests—invoke a query whose work grows with the 35,000-record corpus. D1 charges by rows scanned/read; exact quantity cannot be assumed without measurement. [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/)
- Fix: The smallest safe launch fix is to materialize `{ total, fields }` when the catalogue is published/updated (a generated static JSON/HTML artifact or one metadata record maintained by the import process). Route-match first; only then read that already-materialized value. Validate the abstract ID’s canonical syntax before its point lookup, and immediately 404 all other paths. Do not leave the aggregate in shared request handling.
- Cost / trade-off: This converts repeated corpus-scale D1 reads into one update-time computation plus bounded per-request work. It introduces a metadata refresh/invalidation step owned by the catalogue publishing pipeline. If Workers Caching is then enabled, use cacheable `200` GET responses with a chosen TTL and cache tag/purge on catalogue publish; `cache.enabled` checks cache before Worker execution. Cache hits avoid Worker CPU but still carry the documented Worker request charge. [Caching configuration](https://developers.cloudflare.com/workers/cache/configuration/) and [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/)
- Verify: Before launch, record `meta.rows_read` for `/browse` and valid/malformed/missing `/abstract/:id`, and run `EXPLAIN QUERY PLAN` to confirm indexes support `published_at` ordering and `id` lookup. Confirm invalid paths produce no D1 query. If caching is added, verify `Cf-Cache-Status: HIT` and exercise publish-time purge/refresh and `5xx` behavior.
- Source basis: [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/); [Workers Caching configuration](https://developers.cloudflare.com/workers/cache/configuration/); [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/).
- Confidence: high
