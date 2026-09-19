Scope inspected: `inputs/README.md`, `inputs/wrangler.jsonc`, `inputs/index.js`; static scan run.
Scope not inspected: deployed query plans/`meta.rows_read`, traffic, cache rules, WAF/bot/rate limits, and billing plan.
Docs refreshed: [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/), [Static Assets routing](https://developers.cloudflare.com/workers/static-assets/routing/worker-script/).

Release verdict: BLOCK

| host + route family | discovery evidence | known valid corpus | accepted keyspace | first rejection/validation | inherited work | route-specific work | per-hit product unit | first prevention boundary |
|---|---|---|---|---|---|---|---|---|
| `catalogue.example/sitemap.xml` | explicit route and sitemap code | one fixed route | exact path | early route branch | none | response construction | zero D1 work | early return |
| `catalogue.example/` | sitemap | one fixed route | exact path (query variants also accepted) | none needed | `COUNT(*)` over `abstracts` | `GROUP BY field` over `abstracts` | two corpus-scale D1 aggregates | none |
| `catalogue.example/browse` | sitemap | one fixed route | exact path plus arbitrary query strings | none needed | `COUNT(*)` over `abstracts` | ordered 50-row query | corpus-scale count + unknown rows for browse query | none |
| `catalogue.example/about` | shared navigation, not sitemap | one fixed route | exact path | none needed | `COUNT(*)` over `abstracts` | none | corpus-scale D1 aggregate | none |
| `catalogue.example/abstract/:id` | links rendered by `/browse` | 35,000 abstract IDs | any suffix, including empty, malformed, and unknown IDs | no validation before D1 | `COUNT(*)` over `abstracts` | lookup with unknown index/plan | corpus-scale count + unknown lookup rows | none |
| `catalogue.example/*` other paths | catch-all Worker route | unknown | arbitrary paths | only after the D1 count | `COUNT(*)` over `abstracts` | none | corpus-scale D1 aggregate even for 404s | none |

Discovery gaps: `/about` is omitted from the sitemap but is linked by shared navigation; `/abstract/:id` is omitted but is linked by rendered browse results. The Worker route also accepts arbitrary unmatched paths.

Exposure scenario: uncached path = **anonymous request count × D1 rows read per request**. Every non-sitemap request executes `COUNT(*)` before routing ([index.js:12–13](/private/var/folders/58/zrc_1j8n0f74krswfhmrtkrw0000gn/T/codex-ws-tpqtvsb0/inputs/index.js:12)); `/` adds a second aggregate ([line 15](/private/var/folders/58/zrc_1j8n0f74krswfhmrtkrw0000gn/T/codex-ws-tpqtvsb0/inputs/index.js:15)). With 35,000 abstracts, this is corpus-proportional work repeatedly reachable by bots, ordinary reloads, and arbitrary 404 URLs. Exact `rows_read` remains to be measured.

Closure conditions: remove the shared aggregate from every request path; reject unmatched/malformed abstract paths before any D1 call; prove the remaining browse and abstract lookups bounded with `EXPLAIN QUERY PLAN` and `meta.rows_read`; then cache or statically serve recrawlable pages if freshness permits.

### Severity: high — Shared corpus-wide D1 aggregate on every public request

- Severity: high
- Category: cost footgun
- Evidence: `COUNT(*)` executes before all routing at [index.js:12–13](/private/var/folders/58/zrc_1j8n0f74krswfhmrtkrw0000gn/T/codex-ws-tpqtvsb0/inputs/index.js:12); the Worker is publicly routed for `catalogue.example/*` in [wrangler.jsonc:5](/private/var/folders/58/zrc_1j8n0f74krswfhmrtkrw0000gn/T/codex-ws-tpqtvsb0/inputs/wrangler.jsonc:5); 35,000 records and no cache configuration are stated in [README.md:3](/private/var/folders/58/zrc_1j8n0f74krswfhmrtkrw0000gn/T/codex-ws-tpqtvsb0/inputs/README.md:3).
- Why it matters: D1 bills rows read by rows scanned, not rows returned. The shared `COUNT(*)` makes every anonymous request—including invalid `/abstract/...` and arbitrary 404 paths—invoke a growing-table aggregate. `/` additionally runs `GROUP BY`, another broad aggregate.
- Fix: Smallest safe fix: compute and store catalogue stats (total and field counts) at publish/update time in one small `catalogue_stats` record, then route and validate the pathname before reading it. Return unknown paths immediately; validate canonical abstract IDs before their indexed lookup. This removes corpus-wide work without requiring generation of all 35,000 pages.
- Cost / trade-off: Replaces corpus-proportional D1 reads with one bounded stats lookup only on pages that need it; publishing becomes responsible for updating that record. The remaining `/browse` ordering and abstract lookup must be measured before claiming their D1 cost is bounded.
- Verify: Run `EXPLAIN QUERY PLAN` for the browse and abstract queries; capture `meta.rows_read` in a staging request; confirm malformed/unknown paths perform zero D1 queries. Add static assets for stable pages later if desired—matching assets are served before the Worker by default.
- Source basis: [Cloudflare D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/); [Cloudflare D1 index guidance](https://developers.cloudflare.com/d1/best-practices/use-indexes/); [Cloudflare Static Assets Worker routing](https://developers.cloudflare.com/workers/static-assets/routing/worker-script/).
- Confidence: high