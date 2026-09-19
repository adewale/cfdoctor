## Cloudflare Doctor — focused triage

Scope inspected: `inputs/README.md`, `inputs/wrangler.jsonc`, `inputs/index.js`; static scan (`CFDOC-PERF-D1-SELECT-STAR` reviewed and not treated as a cost finding).
Scope not inspected: deployed traffic, bot/WAF/rate-limit settings, D1 schema/query plans, cache headers/rules, plan and billing data.
Docs refreshed: [Workers Cache](https://developers.cloudflare.com/workers/cache/), [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/), [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/).

### Severity: high — Every public HTML hit repeats D1 work, including a catalogue-wide count

- Category: cost footgun
- Evidence: `inputs/index.js:13` performs `SELECT COUNT(*) FROM abstracts` before routing every non-sitemap request; `inputs/index.js:15`, `:19`, and `:25` add route-specific queries. `inputs/index.js:1-3` sets no cache directives, and `inputs/wrangler.jsonc:1-7` does not enable Workers Cache. The Worker is publicly routed at `catalogue.example/*`.
- Why it matters: Each bot or visitor request to `/`, `/browse`, `/about`, any `/abstract/:id`, and even unknown paths invokes D1. With 35,000 abstracts, the unconditional count can scan a material number of rows per request unless the actual query plan proves otherwise. D1 bills rows read, including rows scanned rather than merely returned; uncached repeat traffic multiplies Workers execution and D1 reads.
- Fix: Enable Workers Cache and return a conservative public `Cache-Control` TTL for these public read-only pages (for example, `public, max-age=300, stale-while-revalidate=60`). Move the count query into only the routes that render it (`/` and `/about`) as a small additional guard. Set an intentionally shorter TTL or purge/redeploy when catalogue updates must become visible.
- Cost / trade-off: Cache hits skip Worker execution and therefore skip its D1 queries; this directly removes the repeat-read amplification. Workers Cache hits still count as Worker requests, so the gain is D1 reads and CPU—not a request-charge elimination. The trade-off is bounded staleness; the proposed TTL is reversible and does not require a data-model change.
- Verify: Before launch, run `EXPLAIN QUERY PLAN SELECT COUNT(*) FROM abstracts` and capture D1 `rows_read` metadata for each route. After deploying, issue the same `GET` twice and confirm `Cf-Cache-Status: MISS` then `HIT`; monitor D1 Row Metrics and Worker CPU/request metrics.
- Source basis: [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/) documents billing by rows read and that scans count even when few rows are returned. [Workers Cache](https://developers.cloudflare.com/workers/cache/) documents cache hits bypassing Worker execution and cache control via response headers. [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/) confirms cache hits remain billable Worker requests while CPU is billed only when the Worker runs.
- Confidence: high

The absence of a full sitemap is not itself a confirmed cost issue; it may reduce discovery, but traffic and crawler behavior were not supplied.