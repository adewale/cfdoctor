# Cloudflare cost footguns

Cost findings should name the billing meter or amplification mechanism. Avoid exact dollar estimates unless the user supplied plan, region, retention, and volume assumptions.

## General cost model questions

Ask for or infer cautiously:
- Monthly requests, peak RPS, average response size, and cache hit ratio.
- Per-request storage operations: KV reads/writes/lists, D1 queries/rows, R2 Class A/B operations, Queue messages, DO requests/duration, Dynamic Worker requests/CPU/unique workers, and Artifacts operations/storage.
- Background job volume, retry rates, cron frequency, agent/tool/browser/sandbox runs, log volume/retention, and add-on products enabled.
- Plan type and limits. Cloudflare pricing/limits change; verify current docs before quoting numbers.
- Whether the project recently moved from Free to Paid. Treat plan upgrades as cost-risk changes: hard stops/included usage may become paid overages or different throttling behavior depending on product and plan.
- Circuit breakers, kill switches, retry limits, fanout caps, DLQ depth, and run-summary metrics. Missing controls turn transient failures into spend amplification.

## Workers

Footguns:
- Assuming Workers cost is only request count. Under current Standard pricing, Worker requests and CPU time are direct meters; duration is not billed and subrequests are not separately billed. Subrequests still consume limits and amplify separately metered KV/D1/R2/AI/origin work. Verify Enterprise/legacy contracts separately.
- Expensive CPU work in request path: compression, image/video transforms, crypto loops, large JSON/HTML transformations.
- Awaiting analytics/logging/email/webhook/cache writes instead of using `ctx.waitUntil` or Queues.
- Multiple public Worker-to-Worker fetches where service bindings would reduce latency and simplify security/accounting.
- Retry loops without backoff around third-party or Cloudflare APIs.
- Direct TCP/database calls from Workers without checking connection pooling, TLS, regional latency, timeout, and retry behavior; Hyperdrive or another data-local strategy may be a better fit for supported databases.
- Duplicate expensive operations without idempotency keys, especially generation/inference, media transforms, browser sessions, uploads, and write-side effects.
- Cron triggers running too frequently or in every environment.
- Preview, workshop, demo, or one-off Workers left routed to paid bindings/services after the event or test window.

Diagnosis:
- Estimate CPU/subrequests per request and multiply by traffic.
- Check whether a user request fans out to storage/API calls, queue retries, and logs.

## Workers Cache (declarative per-Worker cache)

Workers Cache (enabled with `cache = { enabled = true }` in Wrangler, and per-entrypoint via `exports.<name>.cache.enabled`) puts a tiered cache in front of the Worker so cacheable requests are served without executing it. It is distinct from the imperative Cache API (`caches.default`). Verify all numbers against current pricing docs.

Cost model:
- A cache **hit** is still billed at the standard Workers **request** rate; only **CPU time** is saved (the Worker does not run). Caching does **not** reduce billed request count — it trades CPU for the same per-request charge. Misses and bypasses bill both request and CPU.
- **Enabling caching makes normally-free traffic billable.** Static-asset requests and worker-to-worker invocations through service bindings or `ctx.exports` are billed at the standard request rate once caching is on, because each now consults the cache in front of the Worker. A Worker that serves many static assets or fans out heavily over service bindings can see its **bill rise** after enabling caching even as per-request CPU falls; model both effects before enabling it broadly.
- Real savings come from fewer Worker executions on hits: less CPU, plus the downstream KV/R2/D1/origin operations the skipped code would have run (subrequests are not separately billed, but the KV read units, R2 Class B ops, and D1 rows read behind them are).
- Request collapsing: Workers Cache runs the Worker **once** for a burst of concurrent requests to the same cold cache key, avoiding a thundering herd of billable executions. The Cache API does **not** collapse — a burst to a fresh URL invokes the Worker once per request.
- No separate SKU and no per-GB storage fee.

Footguns:
- **Auth bypass:** a cache hit skips Worker execution, so it also skips any auth/gateway logic. Disable caching on the default/gateway entrypoint (`exports.default.cache.enabled = false`) and cache only inner entrypoints. Cloudflare auto-bypasses responses carrying `Set-Cookie` and requests carrying `Authorization`, but do not rely on that alone for an authorization boundary.
- **Personalization leak:** the cache key is path + entrypoint + `ctx.props` + Worker version — not hostname or cookies. Multi-tenant callers must put the tenant/authorization context in `ctx.props` or they will share cached responses.
- Only `GET`/`HEAD` are cached; `206`, `520`–`526`, WebSocket upgrades, and custom RPC methods bypass. At launch, all responses are capped at the Free-plan cacheable size limit regardless of account plan (temporary).
- Cache API caveats remain (Cloudflare now recommends Workers Cache over the Cache API for new Workers): the Cache API runs the Worker on every request (no CPU saving), is single-data-center (no tiered cache), does not collapse concurrent requests, and `cache.put()` silently no-ops on `Set-Cookie`/`no-store`/oversize/`206`/`Vary: *`. It is also a no-op on `workers.dev` and in the dashboard editor/Playground.

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
- Unbounded queries, table scans, missing indexes, or `ORDER BY RANDOM()` on hot routes. D1 rows read can dominate cost even when result count is small. `SELECT *` alone is a projection/schema-coupling lead, not proof of extra billed rows; confirm predicates, indexes, limits, query plan, and `rows_read` metadata.
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
- WebSocket code with no close/error/timeout cleanup; zombie sessions can keep state and duration alive longer than intended.
- Alarm handlers that unconditionally call `setAlarm()` again, creating a persistent wake-up loop even when no work remains.
- Durable Objects that call each other's stubs (or their own binding) in a cycle. Once each hop detaches via `waitUntil`, alarms, or queued work, per-invocation subrequest limits reset on every hop, so no platform limit stops the loop; requests, duration, and storage rows read keep billing until the code changes or a kill switch fires.
- Unbounded `storage.sql.exec` SELECTs (no WHERE/LIMIT, no supporting index) on request/alarm/loop paths. SQLite-backed DO storage bills rows read, and re-scanning a growing table compounds roughly quadratically; a rows-read-dominated bill with small request/duration meters is the signature (a 2026-08 first-hand incident put storage rows read at 98.5% of an $8,846 cycle).
- `storage.list()` on hot paths or on wake-up as a generic read mechanism; list/pagination amplifies reads and latency versus fetching known keys or compact state.
- Repeated writes to the same logical state that could be coalesced. Multi-key batching of distinct keys can improve correctness/latency but current pricing still bills the distinct rows/units, so do not claim savings from batching alone; verify SQLite versus legacy KV-backed storage and actual rows/units changed.
- One DO per ephemeral idempotency key/request ID/notification/short-lived event, causing object-count and storage cleanup problems without much coordination benefit.
- Fan-out from one Worker/request/job to hundreds or thousands of DO stubs with no backpressure, batching, or urgency distinction.
- DO used as a generic database with many trivial object invocations.
- DO storage chosen for read-heavy/write-rare data that could use KV/D1/R2 once consistency/query requirements are clear; remember DO duration/requests are part of the total cost, not just storage ops.
- In-memory-only state causes recovery/retry loops after object eviction/restart or hibernation.
- Memory is the duration billing unit: Durable Objects duration bills the full 128 MB allocation regardless of actual usage, and co-located objects of one class that share an isolate are each billed as if they had the full allocation. Objects pinned in memory by non-hibernating WebSockets, outbound `connect()`/WebSocket connections (up to 15 minutes each), timers, or polling keep paying duration.
- Module-scope baseline (tool schema registries, eagerly built validators, large Wasm) in a Durable Object class turns into memory-limit resets that discard in-flight agent turns; each reset re-runs the model call, the retry, and the upstream work, so the bill for the retried work follows the reset count even though nothing is billed for the reset itself. The Agents SDK's `maxOomRetries` budget makes that retry cost explicit.

Better patterns:
- Validate and rate-limit before obtaining/calling DO stubs; reject malformed/unauthorized requests in the Worker where possible.
- Shard by natural key or bounded hash/time buckets, use hibernation for WebSockets, close/cleanup sockets, persist state intentionally, coalesce redundant writes, use transactions/multi-key APIs for correctness and latency rather than assumed billing savings, only reschedule alarms when work remains, offload heavy/background work to Queues/Workflows, and use D1/KV/R2 for data that does not need per-key coordination.
- For any DO-to-DO or self re-trigger path, pass an explicit hop/depth budget and check it in every hop, add an idempotency/turn key so replays cannot restart the chain, and bound hot SQL with WHERE/LIMIT plus indexes. Watch the Durable Objects rows-read meter after deploys that touch storage access; requests and duration alone can look harmless while rows read dominate.
- Keep the isolate baseline small (JSON Schema tool definitions, lazily built validators, `sideEffects: false` plus named re-exports, static package imports) and watch the Durable Objects memory chart with deployment markers; a flat line above the limit at idle is baseline that every object pays.

## Queues and Workflows

Footguns:
- Retry storms from non-idempotent consumers or aggressive retry settings.
- Poison messages exhausting the retry limit and being permanently deleted when no DLQ/alerting/replay path exists; Cloudflare currently defaults to three retries.
- Enqueueing enormous fan-outs from a single request with no quota/backpressure.
- Workflows used for simple fire-and-forget tasks where Queues would suffice, or ad hoc queues implemented in KV/D1.
- Treating Workflow steps or retained instance state as free. Current pricing meters requests, CPU, persisted storage, and steps; Cloudflare announced that Paid-plan step and storage billing starts no earlier than August 10, 2026. Sleeps and event waits are steps even though idle wait time does not consume CPU.
- Retrying terminal failures or ignoring provider-specific `Retry-After` guidance. Workflows now supports dynamic retry delay functions and `NonRetryableError` for permanent failures.

Better patterns:
- Idempotency keys, DLQs, bounded retries, adaptive backoff, `NonRetryableError` for permanent failures, alerting, explicit fan-out limits, coarse meaningful Workflow steps, and intentional instance-state retention. Verify the announced billing start date before making a current invoice claim.

## Spend-amplification controls

Footguns:
- Hot retries into a degraded dependency or paid primitive with no circuit breaker, cooldown, or max-attempt cap.
- Unbounded fanout from one request/job: recursive crawlers, `Promise.all(items.map(...))`, queue batch explosions, workflow recursion, tenant broadcasts, or AI/tool loops.
- Missing kill switches for expensive features, cron jobs, queue consumers, demo/workshop routes, Dynamic Workers, Agents scheduled tasks/tools, Workers AI, Browser Run, Images/Stream transforms, or Vectorize search.
- No anti-rework cache: the same logical operation repeats after refresh, retry, queue replay, webhook duplicate, browser reconnect, or user double-click.
- Run summaries log success/failure but not cost proxies, making it impossible to notice spend amplification until billing arrives.
- Relying on Cloudflare billing notifications as the runaway-spend defense. Budget alerts are informational only — they do not pause or cap usage, there is no hard spending limit, eligible Pay-as-you-go accounts get only an auto-created $10 default threshold, and per-product usage notifications scoped to one product (for example Workers requests) cannot see a different meter (for example DO storage rows read). Verify configured scope, thresholds, recipients, and delivery latency against current billing docs instead of assuming timely alerts.
- Kill switches that only guard the HTTP edge. A loop detached through `waitUntil`, alarms, queue consumers, or DO-to-DO stubs never passes the edge again; the flag must be checked inside every loop step (alarm entry, consumer entry, stub-call site) to actually stop it.

Better patterns:
- Circuit breaker per dependency/product with threshold, cooldown, degraded fallback, alert, and manual override.
- Persisted idempotency/result cache keyed by logical job/user action, not by retry attempt.
- Fanout limits: max items, max depth, max concurrency, max queued messages, tenant quotas, and backpressure.
- Kill switches in config/secrets/flags that can disable expensive routes/jobs without deploys, checked inside loop steps (alarm handlers, queue consumers, DO stub-call sites), with `deleteAlarm()`, queue pause, and deployment rollback as the break-glass paths.
- Per-run summaries that emit inputs, outputs, retries, DLQ count, fanout count, CPU-ish duration, subrequests, D1 rows, R2/KV ops, DO calls/duration/storage rows read-written, AI/browser/media/vector units, and cache hit/miss counts.
- Deliberate billing-detection posture: budget alert thresholds sized to expected daily burn (replace the $10 default), recipients that are actually monitored, and a daily billable-usage review or API poll with an anomaly threshold so a runaway meter is caught in hours-to-days, not at invoice time.

## Dynamic Workers, Agents SDK, Workers AI, Vectorize, Images, Stream, and Browser Run

Footguns:
- Dynamic Workers executing user/LLM-generated code with inherited network access, broad bindings, no custom resource limits, and no per-run accounting for requests/CPU/unique Dynamic Workers.
- Dynamic Worker code-as-tool loops that repeatedly spawn sandboxes for the same logical operation instead of reusing/deduping by code hash and input.
- Artifacts-backed app/firmware loaders that create per-tenant/per-app repos or tokens without lifecycle cleanup, namespace separation, signing, rollback, or token-usage monitoring.
- Agents SDK loops, scheduled tasks, sub-agents, browser tools, sandbox tools, and autonomous responses without max steps, cancellation, idempotency, run summaries, or retry/backoff bounds.
- Workers AI loops, retries, duplicate generation, or Queue replay without idempotency/dedupe. For generation and embeddings, the same user action can trigger multiple paid inferences.
- Workers AI requests not using caching/session affinity where applicable, or no cap on model/tool-call loops.
- Vectorize search hiding queried/stored dimensions. Cost can be tied to queried dimensions and stored vector dimensions; audit index dimensions, topK, namespace fan-out, and repeated embedding/query flows.
- Image transformations multiplied by unique variants: unbounded width/height/format/DPR/quality combinations or flexible variants exposed to arbitrary user input. As of July 2026, Images binding calls are billed per unique source-and-parameter transformation per calendar month, not per call; `.info()` is free. Repeating the same uncached transform still reruns decode/encode work and the Worker, adding latency and Worker CPU/request usage even when it does not add another Images transformation unit.
- Stream preloading/buffering counted as delivered minutes: players using aggressive preload/autoplay, background tabs, hidden players, or custom HLS/DASH clients that fetch media before users intentionally watch.
- Browser Run sessions left open, retried blindly, or launched per request when a lighter fetch/HTML parser/API would work. Browser hours/concurrency can dominate cost.

Better patterns:
- For Dynamic Workers, use deny-by-default egress/bindings, custom limits/timeouts, code-hash/version IDs, bounded logs, and per-run accounting for requests/CPU/unique workers.
- For Agents SDK, cap max steps/tool calls/sub-agents, require cancellation, add idempotency and retry backoff, and emit run summaries with model/tool/browser/sandbox cost proxies.
- For Artifacts, scope repo tokens, separate namespaces by env/tenant where needed, sign artifacts used for app/firmware updates, and keep rollback/lifecycle cleanup evidence.
- Add idempotency keys and persistent result caches for AI/image/browser jobs; dedupe Queue messages before expensive calls.
- Bound AI/tool/browser retry loops with exponential backoff, max attempts, and circuit breakers.
- For Images, use predefined variants or strict allowlists and normalize transformation inputs. Enable Workers Cache only where the response is safely cacheable: it avoids rerunning the Worker/transformation on hits, but cache hits remain billed Worker requests and auth/tenant cache-key rules still apply.
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
- Cost / trade-off: Reduces R2 Class A/list operations and latency; adds index maintenance, cache invalidation, and possible stale-list behavior; reversible by falling back to direct R2 listing.
- Verify: Load-test the route and confirm R2 operation counts fall; add a regression test for pagination/cache behavior.
- Confidence: high
```
