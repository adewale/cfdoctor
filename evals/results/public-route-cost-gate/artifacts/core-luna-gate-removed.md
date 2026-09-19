## Cloudflare Doctor focused triage

Scope inspected: `inputs/README.md`, `inputs/wrangler.jsonc`, `inputs/index.js`, plus the Cloudflare Doctor static scanner.
Scope not inspected: deployed traffic, D1 query metrics, plan, billing, WAF, bot management, rate limits, and cache settings.
Docs refreshed: [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/), [D1 metrics](https://developers.cloudflare.com/d1/observability/metrics-analytics/), [D1 return metadata](https://developers.cloudflare.com/d1/worker-api/return-object/).

### High: Per-request full-table count can amplify D1 cost

- Category: cost footgun
- Evidence: `inputs/index.js:12-13` executes `SELECT COUNT(*) AS count FROM abstracts` before route dispatch. This affects browse pages, every `/abstract/:id` page, `/about`, and unknown non-sitemap paths. The catalogue contains 35,000 abstracts.
- Why it matters: D1 bills rows read/scanned, not just rows returned. A table-wide count can therefore read roughly 35,000 rows per request. For example, 100,000 detail-page requests could produce approximately 3.5 billion row reads before the detail query itself. Free-plan limits can cause D1 errors; paid usage beyond included reads is billed. Cloudflare exposes `rows_read` per query for verification.
- Fix: Only run the count on routes that display it:

  ```js
  const needsTotal = url.pathname === "/" || url.pathname === "/about";
  const total = needsTotal
    ? await env.DB.prepare("SELECT COUNT(*) AS count FROM abstracts").first()
    : null;
  ```

  Or move the count query directly inside the `/` and `/about` branches.
- Cost / trade-off: Removes one potentially 35,000-row D1 read from browse, detail, and invalid requests. It preserves current behavior on `/` and `/about`, with no schema or deployment change. The count can still be expensive when those two pages are requested frequently; precomputed metadata or safe public caching would be a later optimization, not the smallest fix.
- Verify: Deploy to a staging database and inspect the returned `meta.rows_read` for each query; confirm detail and browse requests no longer issue `COUNT(*)`. After launch, review D1 row metrics and query insights.
- Source basis: [Cloudflare D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/) and [D1 metrics and analytics](https://developers.cloudflare.com/d1/observability/metrics-analytics/).
- Confidence: high

No material cost finding is established from the missing cache configuration alone; caching may help later, but the route-gating change is the smallest safe launch fix.