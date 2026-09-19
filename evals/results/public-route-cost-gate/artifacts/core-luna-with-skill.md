Release verdict: BLOCK

| host + route family | discovery evidence | known valid corpus | accepted keyspace | first rejection/validation | inherited work | route-specific work | per-hit product unit | first prevention boundary |
|---|---|---:|---|---|---|---|---|---|
| `catalogue.example/*` → `/` | Sitemap | 35,000 abstracts | Fixed path | None before D1 | `COUNT(*)` | `GROUP BY field` | D1 rows read; corpus-proportional | None |
| `catalogue.example/*` → `/browse` | Sitemap, navigation | 35,000 abstracts | Any `field` query is accepted but ignored | None before D1 | `COUNT(*)` | 50-row ordered query | D1 rows read; exact plan unknown | None |
| `catalogue.example/*` → `/about` | Shared navigation | 35,000 abstracts | Fixed path | None before D1 | `COUNT(*)` | None | D1 rows read; corpus-proportional | None |
| `catalogue.example/*` → `/abstract/:id` | Browse links, route code | 35,000 abstracts | Arbitrary suffix, including malformed/unknown IDs | No syntax/canonical validation | `COUNT(*)` | ID lookup | D1 rows read; exact plan/index unknown | None |
| `catalogue.example/*` → `/sitemap.xml` | Explicit route | N/A | Fixed path | Worker route check | None | Static response | Zero D1 reads | Early Worker branch |
| `catalogue.example/*` → all other paths | Route fallback | N/A | Unbounded paths | None before D1 | `COUNT(*)` | 404 | D1 rows read; corpus-proportional | None |

Discovery gaps: `/about` is absent from the sitemap but exposed by shared navigation; `/abstract/:id` is absent but exposed by browse-result links; arbitrary unknown paths also reach the shared query before the 404.

Exposure scenario: supplied evidence shows no Workers cache configuration. For uncached traffic, exposure is:

`anonymous requests × (rows read by COUNT + route-specific rows read)`

At the current 35,000-record size, the shared `COUNT(*)` is corpus-scale work on every HTML request; `/` adds another corpus-wide `GROUP BY`. Exact billed rows require D1 query-plan or `meta.rows_read` measurements. D1 bills by rows scanned, not rows returned. [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/) [D1 index/query-plan guidance](https://developers.cloudflare.com/d1/best-practices/use-indexes/)

Closure conditions:

- Remove the shared `COUNT(*)` and homepage `GROUP BY` from every public request path by materializing catalogue metadata at publish/update time.
- Reject malformed/noncanonical abstract IDs before any D1 call.
- Verify the remaining browse and abstract queries with `EXPLAIN QUERY PLAN` and `meta.rows_read`; confirm appropriate indexes.
- Optionally enable pre-Worker Workers Caching with explicit freshness/invalidation behavior. Workers Caching checks cache before invoking the Worker; cache hits bypass Worker execution/CPU but retain the documented request charge. [Workers Caching configuration](https://developers.cloudflare.com/workers/cache/configuration/) [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/)

### Severity: high — Corpus-wide D1 aggregates on every public HTML request

- Category: cost footgun
- Evidence: `inputs/index.js:12-16`; shared `COUNT(*)` runs before routing, and `/` runs `GROUP BY field`. README states 35,000 abstracts and no cache configuration.
- Why it matters: `/about`, `/browse`, every abstract page, unknown paths, and the homepage all trigger the aggregate. Anonymous repeated requests therefore multiply corpus-scale D1 row reads and can exhaust free daily limits or create paid usage. The exact scan count is not supplied, so the dollar impact is not estimated.
- Fix: At publish/update time, generate a small immutable metadata object containing the total and field groups. Replace lines 13 and 15 with reads from that object; do not query D1 for shared layout metadata. Preserve D1 only for the browse listing and validated abstract lookup.
- Cost / trade-off: Smallest behavior-preserving complete fix; removes the corpus-proportional per-request meter and reduces latency. It adds a publish/update step and requires metadata refresh whenever abstracts change.
- Verify: Deploy a build with metadata materialized; confirm `/`, `/about`, `/browse`, `/abstract/:id`, and unknown paths issue no aggregate D1 queries. Inspect D1 `meta.rows_read` and run query plans for the remaining lookups.
- Source basis: [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/); [D1 index and query-plan guidance](https://developers.cloudflare.com/d1/best-practices/use-indexes/)
- Confidence: high

The scanner requested by the skill was not present at the referenced path, so no scanner result is included. Account, traffic, WAF, bot, billing, and deployed-cache state were not inspected.
