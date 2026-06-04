# Cloudflare cost footguns

Cost findings should name the billing meter or amplification mechanism. Avoid exact dollar estimates unless the user supplied plan, region, retention, and volume assumptions.

## General cost model questions

Ask for or infer cautiously:
- Monthly requests, peak RPS, average response size, and cache hit ratio.
- Per-request storage operations: KV reads/writes/lists, D1 queries/rows, R2 Class A/B operations, Queue messages, DO requests/duration.
- Background job volume, retry rates, cron frequency, log volume/retention, and add-on products enabled.
- Plan type and limits. Cloudflare pricing/limits change; verify current docs before quoting numbers.
- Whether the project recently moved from Free to Paid. Treat plan upgrades as cost-risk changes: hard stops/included usage may become paid overages or different throttling behavior depending on product and plan.
- Circuit breakers, kill switches, retry limits, fanout caps, DLQ depth, and run-summary metrics. Missing controls turn transient failures into spend amplification.

## Workers

Footguns:
- Assuming Workers cost is only request count. Workers cost and limits can also involve CPU time/duration/subrequests depending on plan and runtime path; CPU-heavy work can become the real bill or limit even when request count looks low.
- Expensive CPU work in request path: compression, image/video transforms, crypto loops, large JSON/HTML transformations.
- Awaiting analytics/logging/email/webhook/cache writes instead of using `ctx.waitUntil` or Queues.
- Multiple public Worker-to-Worker fetches where service bindings would reduce latency and simplify security/accounting.
- Retry loops without backoff around third-party or Cloudflare APIs.
- Duplicate expensive operations without idempotency keys, especially generation/inference, media transforms, browser sessions, uploads, and write-side effects.
- Cron triggers running too frequently or in every environment.
- Preview, workshop, demo, or one-off Workers left routed to paid bindings/services after the event or test window.

Diagnosis:
- Estimate CPU/subrequests per request and multiply by traffic.
- Check whether a user request fans out to storage/API calls, queue retries, and logs.

## KV

Footguns:
- KV reads/writes on every request for data that could be CDN-cached or in-request memoized.
- `KV.list()` in hot paths; list operations and pagination can become expensive and slow.
- High-churn counters/sessions/locks that generate many writes and still lack correctness.
- Large values or blob-like storage better suited to R2.

Better patterns:
- Cache public results at the CDN; use KV for low-churn config/metadata.
- Use Durable Objects for counters/rate limits/coordination, D1 for queryable relational data, R2 for blobs.

## D1

Footguns:
- Unbounded queries, table scans, `SELECT *`, missing indexes, or `ORDER BY RANDOM()` on hot routes. D1 rows read can dominate cost even when result count is small.
- N+1 query patterns in Workers; count queries and rows read per user-visible request, not just HTTP request count.
- Using D1 as an analytics/event sink or queue.
- Recomputing public query results on every request instead of caching.

Better patterns:
- Add indexes, limits, batching, prepared statements, constraints, and CDN/cache layers where consistency allows.
- Use Queues/Analytics Engine/R2 for high-volume event capture depending on requirements.

## R2

Footguns:
- Treating R2 “no egress fees” as “no bill.” Storage, Class A/B operations, Workers in front of R2, logs, transforms, and lifecycle gaps can still cost money.
- Listing buckets/prefixes for every request as a metadata/query mechanism.
- Serving public R2 objects through a Worker with no CDN cache headers, causing repeated R2 operations and Worker invocations.
- Tiny high-churn objects with high operation counts.
- Multipart uploads abandoned without cleanup.
- Generating many one-off transformations/derivatives without cache/reuse.

Better patterns:
- Store queryable metadata in D1/KV/search; use R2 for the object bytes.
- Stream and range large objects; cache public objects aggressively when safe.

## Durable Objects

Footguns:
- Routing invalid/bot/unauthenticated traffic into Durable Objects before validating method, auth, tenant, request size, and cheap abuse signals. This turns junk traffic into DO requests/duration and can hot-spot objects.
- One global Durable Object or low-cardinality shard receives most traffic, creating latency, throughput, and cost concentration.
- Long-lived WebSockets handled without hibernation when idle duration dominates, or ordinary DO requests keeping objects active with timers/polling instead of alarms/queues.
- DO used as a generic database with many trivial object invocations.
- In-memory-only state causes recovery/retry loops after object eviction/restart.

Better patterns:
- Validate and rate-limit before obtaining/calling DO stubs; reject malformed/unauthorized requests in the Worker where possible.
- Shard by natural key, use hibernation for WebSockets, persist state intentionally, offload heavy/background work to Queues/Workflows, and use D1/KV/R2 for data that does not need per-key coordination.

## Queues and Workflows

Footguns:
- Retry storms from non-idempotent consumers or aggressive retry settings.
- Poison messages repeatedly consuming attempts without DLQ/alerting.
- Enqueueing enormous fan-outs from a single request with no quota/backpressure.
- Workflows used for simple fire-and-forget tasks where Queues would suffice, or ad hoc queues implemented in KV/D1.

Better patterns:
- Idempotency keys, DLQs, bounded retries, backoff, alerting, and explicit fan-out limits.

## Spend-amplification controls

Footguns:
- Hot retries into a degraded dependency or paid primitive with no circuit breaker, cooldown, or max-attempt cap.
- Unbounded fanout from one request/job: recursive crawlers, `Promise.all(items.map(...))`, queue batch explosions, workflow recursion, tenant broadcasts, or AI/tool loops.
- Missing kill switches for expensive features, cron jobs, queue consumers, demo/workshop routes, Workers AI, Browser Run, Images/Stream transforms, or Vectorize search.
- No anti-rework cache: the same logical operation repeats after refresh, retry, queue replay, webhook duplicate, browser reconnect, or user double-click.
- Run summaries log success/failure but not cost proxies, making it impossible to notice spend amplification until billing arrives.

Better patterns:
- Circuit breaker per dependency/product with threshold, cooldown, degraded fallback, alert, and manual override.
- Persisted idempotency/result cache keyed by logical job/user action, not by retry attempt.
- Fanout limits: max items, max depth, max concurrency, max queued messages, tenant quotas, and backpressure.
- Kill switches in config/secrets/flags that can disable expensive routes/jobs without deploys.
- Per-run summaries that emit inputs, outputs, retries, DLQ count, fanout count, CPU-ish duration, subrequests, D1 rows, R2/KV ops, DO calls/duration, AI/browser/media/vector units, and cache hit/miss counts.

## Workers AI, Vectorize, Images, Stream, and Browser Run

Footguns:
- Workers AI loops, retries, duplicate generation, or Queue replay without idempotency/dedupe. For generation and embeddings, the same user action can trigger multiple paid inferences.
- Workers AI requests not using caching/session affinity where applicable, or no cap on model/tool-call loops.
- Vectorize search hiding queried/stored dimensions. Cost can be tied to queried dimensions and stored vector dimensions; audit index dimensions, topK, namespace fan-out, and repeated embedding/query flows.
- Image transformations multiplied by variants: unbounded width/height/format/DPR/quality combinations, flexible variants exposed to arbitrary user input, or per-request transformations without cache normalization.
- Stream preloading/buffering counted as delivered minutes: players using aggressive preload/autoplay, background tabs, hidden players, or custom HLS/DASH clients that fetch media before users intentionally watch.
- Browser Run sessions left open, retried blindly, or launched per request when a lighter fetch/HTML parser/API would work. Browser hours/concurrency can dominate cost.

Better patterns:
- Add idempotency keys and persistent result caches for AI/image/browser jobs; dedupe Queue messages before expensive calls.
- Bound AI/tool/browser retry loops with exponential backoff, max attempts, and circuit breakers.
- For Images, use predefined variants or strict allowlists, normalize transformation URLs/cache keys, and cache transformed outputs.
- For Stream, avoid eager preload for pay-sensitive embeds, secure URLs, and measure delivered minutes by player/route.
- For Vectorize, choose dimensions intentionally, reduce namespace/query fan-out, cache embedding/query results where safe, and cite current Vectorize pricing docs.
- For Browser Run, close sessions in `finally`, set session/request timeouts, reuse sessions only intentionally, and prefer Quick Actions or non-browser primitives for simple scraping/screenshots.

## Third-party origins behind Cloudflare

Footguns:
- Assuming Cloudflare in front means the origin cannot bill. Cache misses, uncacheable APIs, image optimization endpoints, serverless functions, and direct default hostnames can still hit Vercel/Netlify/Railway/Render/Fly/Heroku/AWS/GCP/Azure/Firebase/Supabase origins.
- Default provider hostnames remain public (`*.vercel.app`, `*.netlify.app`, `*.railway.app`, `*.onrender.com`, `*.fly.dev`, `*.herokuapp.com`, storage endpoints), bypassing Cloudflare WAF/cache/auth.
- Origin autoscaling/concurrency caps are unset, so bot traffic through cache misses becomes origin spend.

Better patterns:
- Lock origins to Cloudflare where possible, disable or protect default hostnames, set origin provider spend/scale controls, and cache/rate-limit before origin-hit paths.
- Track origin usage alongside Cloudflare metrics; a low Cloudflare bill can still hide a high Vercel/Netlify/Railway/etc. bill.

## CDN/cache/account products

Footguns:
- Low cache hit ratio on large public traffic because cache headers/rules are absent or cookies bust cache.
- Cache Reserve, Argo, Load Balancing, advanced WAF/rate limiting/bot products, Images, Stream, Zero Trust seats, Logpush destinations, and analytics retention enabled without volume/benefit review.
- Logging every request with high-cardinality payloads or long retention; error storms can turn logs/analytics into their own bill.
- Purge-everything workflows that destroy cache efficiency.

Better patterns:
- Measure hit ratio and top uncached paths, set cache rules carefully, purge by tag/prefix where possible, sample/redact logs, and review add-ons against traffic and risk.

## Cost finding template

```markdown
### High: R2 list operation in public request path can scale linearly with traffic
- Category: cost footgun / missed optimization
- Evidence: `src/routes/files.ts:42` calls `env.BUCKET.list({ prefix })` for every GET `/files`.
- Why it matters: R2 list operations are billed operations and add latency; this turns every page view into a bucket scan/paginated metadata query.
- Fix: Maintain the visible file index in D1/KV and update it on writes; cache the list response with a safe TTL.
- Verify: Load-test the route and confirm R2 operation counts fall; add a regression test for pagination/cache behavior.
- Confidence: high
```
