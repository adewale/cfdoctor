Release verdict: BLOCK

| host + route family | discovery evidence | known valid corpus | accepted keyspace | first rejection/validation | inherited work | route-specific work | per-hit product unit | first prevention boundary |
|---|---|---:|---|---|---|---|---|---|
| `catalogue.example /` | sitemap | 1 page | exact `/` | none | D1 `COUNT(*)` | D1 `GROUP BY field` | corpus-scale D1 rows read | publish-time materialization |
| `catalogue.example /browse` | sitemap, navigation | 1 page | exact `/browse` | none | D1 `COUNT(*)` | ordered `LIMIT 50` query | corpus-scale inherited read | publish-time materialization |
| `catalogue.example /about` | shared navigation | 1 page | exact `/about` | none | D1 `COUNT(*)` | none | corpus-scale D1 rows read | publish-time materialization |
| `catalogue.example /abstract/:id` | browse-result links | 35,000 known abstracts | any suffix after `/abstract/` | none; arbitrary IDs reach D1 | D1 `COUNT(*)` | point lookup | corpus-scale inherited read plus lookup | reject/normalize before D1 |
| `catalogue.example other paths` | generated/unknown requests | none | any pathname | none | D1 `COUNT(*)` | 404 | corpus-scale D1 rows read | route before shared work |
| `catalogue.example /sitemap.xml` | direct config/code | 1 page | exact `/sitemap.xml` | before D1 | none | static response | zero D1 rows | already safe |

Discovery gaps: `/about` is linked from shared navigation; `/abstract/:id` is linked by rendered browse results. The sitemap is not a complete boundary.

Exposure scenario: with no pre-Worker cache and anonymous traffic, exposure is `request count × D1 rows read per request`. The shared `COUNT(*)` executes for every HTML request, including invalid paths. With 35,000 abstracts, it is corpus-proportional work; `/` adds another corpus-scale `GROUP BY`. Exact `rows_read` must be confirmed from D1 query metadata, but D1 bills by rows scanned, not rows returned. [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/) documents this meter and the returned `rows_read` metadata.

Closure conditions: remove corpus-wide aggregates from request handling on every route; route and reject invalid/malformed abstract keys before D1; materialize the total and field groups during catalogue publishing/import; verify any remaining queries with `EXPLAIN QUERY PLAN` and D1 `rows_read`.

### Severity: high — Corpus-wide D1 aggregation on every public request

- Category: cost footgun
- Evidence: `inputs/index.js:12-15`; `COUNT(*)` runs before routing, and `/` also runs `GROUP BY field`. `inputs/README.md:3` states the catalogue contains 35,000 abstracts and has no cache configuration.
- Why it matters: a crawler or ordinary repeated traffic can repeatedly scan the growing corpus. Invalid and unknown routes also incur the shared scan. D1 charges by rows read; the current code supplies no bounded request-path protection.
- Fix: move the shared `COUNT(*)` and `/` `GROUP BY` into publish/update-time materialization, such as a small metadata table or generated static JSON. Route before database access and reject malformed/noncanonical `/abstract/:id` values first. Keep only bounded lookups in the request path.
- Cost / trade-off: removes the dominant per-request corpus multiplier. Requires a publish step and explicit refresh ownership for metadata; exact remaining D1 cost depends on indexes and query plans. Adding cache alone is not a complete fix because misses, expiry, bypasses, and refills can still execute the broad query.
- Verify: publish a catalogue update, then confirm all HTML routes avoid full-table aggregates. Run `EXPLAIN QUERY PLAN` for remaining D1 queries and inspect returned `meta.rows_read`; load-test repeated valid, invalid, and unknown URLs.
- Source basis: [D1 pricing and row-read billing](https://developers.cloudflare.com/d1/platform/pricing/), [D1 index/query-plan guidance](https://developers.cloudflare.com/d1/best-practices/use-indexes/).
- Confidence: high

Scope inspected: `inputs/README.md`, `inputs/wrangler.jsonc`, `inputs/index.js`, and the Cloudflare Doctor static scanner.

Scope not inspected: deployed traffic, account plan, billing, query plans, indexes/schema, WAF, rate limits, and deployment state.

Docs refreshed: current official Cloudflare D1 pricing, billing metadata, and indexing guidance.

No files were modified.