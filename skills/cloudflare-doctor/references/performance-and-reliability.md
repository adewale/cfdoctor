# Performance and reliability checks

## Request hot path

For the most important routes, count:
- Worker CPU-heavy operations: crypto, compression, HTML parsing, image processing, JSON transforms over large payloads, synchronous loops.
- Subrequests: external fetches, service binding calls, R2/KV/D1/DO/Queue operations, auth calls, webhook calls.
- Sequential awaits that could be batched, cached, moved to `ctx.waitUntil`, or queued.
- Bytes buffered in memory before response. Prefer streaming for R2/origin responses and large generated responses.

Smells:
- Analytics/logging/cache writes awaited before returning when they could use `ctx.waitUntil`.
- Fetching full R2 object / origin response with `arrayBuffer()` or `text()` to pass through unchanged.
- Multiple D1 queries per item (N+1) instead of joins/batches.
- Repeated KV reads for stable config without in-request memoization or cache TTL.
- External origin/database calls from every edge location with no Hyperdrive/Smart Placement/data-local plan.
- `Promise.all(items.map(...))`, recursive crawlers, broadcast loops, queue fanout, or workflow fanout without concurrency, depth, item-count, and tenant quotas.
- Immediate retry loops without jitter/backoff/circuit breaker, especially around AI, browser, image/media, D1 writes, Queues, external APIs, and DO calls.

## Resilience controls: circuit breakers, kill switches, fanout, and rework

Check that expensive or failure-amplifying paths have:
- **Circuit breakers**: dependency-specific open/half-open/closed state, failure thresholds, cooldown, and degraded response. Store breaker state in a primitive that fits the scope: per-instance memory for best-effort, Durable Object for coordinated per-key breaker, KV for coarse global flags that tolerate propagation delay, or account/config flags for manual operations.
- **Hot retry protection**: exponential backoff with jitter, max attempts, per-user/per-tenant quotas, and no immediate retry into known degraded dependencies.
- **DLQs and poison handling**: Queue consumers should send unrecoverable messages to DLQ or quarantine storage with alerting and replay tooling.
- **Anti-rework caching**: deterministic idempotency keys and persisted results for expensive logical operations, such as AI generation/embedding, Browser Run screenshots/PDFs, image/video transforms, R2 uploads, webhook processing, and Queue replay.
- **Bounded fanout**: concurrency limits, batch sizes, page/depth limits, tenant quotas, and backpressure for map loops, batch sends, crawlers, broadcasts, and recursive workflows.
- **Kill switches**: feature/env flags that can disable expensive products, crons, queue consumers, AI/browser/media jobs, or demo/workshop routes without redeploying.
- **Run summaries with cost proxies**: every batch/job/cron/consumer should log or emit counts for inputs, outputs, retries, DLQ, elapsed time, CPU-ish duration, subrequests, D1 rows read/written, R2/KV ops, DO calls, AI/browser/media/vector units, and cache hits/misses.

## Caching and CDN behavior

Look for missed cache opportunities:
- Public expensive API responses lacking `Cache-Control`, `s-maxage`, `stale-while-revalidate`, `ETag`, Workers Cache (`cache.enabled`), or Cache API usage.
- Static assets not served by Pages/Workers Static Assets/CDN with immutable hashed filenames.
- R2 public/object responses not cached at the CDN when safe.
- D1/KV/R2 reads for data that could be precomputed, cached, or invalidated on write.
- No cache purge/invalidation strategy for content updates.
- Expensive Worker responses reused across requests but cached only via the Cache API, which runs the Worker on every request and does not collapse concurrent requests. Workers Cache serves hits without running the Worker (saving CPU) and collapses a burst to a cold key into one invocation.

Look for dangerous caching:
- Authenticated or tenant-specific responses cached by URL only.
- Cache key ignores headers/query/body dimensions that change response content.
- Cookies accidentally make otherwise static assets uncacheable.
- Workers Cache enabled on a Worker whose default/gateway entrypoint performs auth: a cache hit skips execution and therefore skips the auth check. Auth/gateway entrypoints need `cache.enabled = false`; cache only inner entrypoints. Multi-tenant separation depends on `ctx.props` in the cache key, not hostname or cookies.
- Workers Cache enabled without accounting for its billing-surface change: normally-free static-asset and worker-to-worker (service binding / `ctx.exports`) requests become billed at the standard request rate once caching is on (see [`cost-footguns.md`](cost-footguns.md)).

## Layered Cloudflare cache map

When a request crosses multiple Cloudflare primitives, require an explicit cache map:

| Layer | What to check |
|---|---|
| Browser/client | `Cache-Control`, `ETag`, preload/autoplay behavior, service-worker caches, and whether private data is cacheable. |
| Cloudflare CDN / Cache Rules | Route/path match, cache eligibility, cache key dimensions, cookies/query normalization, tiered/cache reserve interactions, and purge/tag strategy. |
| Workers Cache (`cache.enabled`) | Tiered, in front of the Worker: which entrypoints have `cache.enabled` (auth/gateway entrypoints must be `false`), `Cache-Control`/TTL, `ctx.props` in the cache key for tenant separation, `ctx.cache.purge()` owner, and the billing-surface change (hits still bill a request; static-asset and worker-to-worker traffic becomes billed). |
| Worker Cache API (`caches.default`) | Per-data-center behavior (no tiered cache), no request collapsing, Worker runs on every request, explicit cache key, TTL, personalization boundaries, silent `put()` no-ops, and `ctx.waitUntil` for writes when safe. Prefer Workers Cache for new Workers. |
| KV as cache | Eventual consistency, TTL, negative caching, versioned keys, stampede prevention, and whether KV is incorrectly treated as authoritative state. |
| D1/R2-backed cache | Whether D1 indexes/rows-read and R2 operations are reduced rather than shifted; metadata in D1/KV, bytes in R2, CDN cache in front when public. |
| Durable Object cache/state | Whether DO is used only where coordination/serialization is needed; avoid using DO as a broad read cache. |
| AI Gateway / prompt/result cache | Cache key includes model, prompt/version, parameters, tenant/user policy, and safety constraints; idempotency prevents duplicate paid generations. |
| Application memoization | Scope is per request/process only unless persisted; avoid assuming isolate memory is durable or globally shared. |

For each layer, record: cache owner, key, TTL, invalidation trigger, stale-while-revalidate behavior, whether it caches errors/negative results, and how it prevents personalized-data leaks.

## Durable Objects reliability

- Validate cheap request properties before constructing/calling Durable Object stubs: method, route, auth/session, tenant membership, request size, content type, and abuse/rate-limit signals. Invalid traffic should be rejected in the front Worker before it becomes DO traffic.
- Shard object IDs by tenant/user/room/key; avoid one global object unless the workload is truly tiny. For idempotency, notifications, short-lived events, or per-request work, prefer bounded hash/time buckets or a different primitive over one object per ephemeral key.
- Use alarms, persisted state, and idempotency for state machines rather than relying on in-memory state only. Alarm handlers should only reschedule when work remains and should have max-iteration/kill-switch behavior.
- Avoid `storage.list()` in request or wake-up hot paths. Fetch known keys, compact related state, maintain a manifest, or cache loaded state intentionally.
- Batch/coalesce small DO storage writes by logical record or flush interval; avoid per-field/per-event write storms.
- For WebSockets, consider Durable Object WebSocket hibernation to avoid duration billing and improve survivability for long-lived idle connections. Add close/error/timeout cleanup paths and persist only the state needed to resume after hibernation/eviction.
- Treat `ctx.waitUntil()` in a DO as a lifecycle decision, not a free background thread. If work can outlive the request or needs retries/visibility, consider alarms, Queues, Workflows, or Agents durable execution.
- Keep object methods short; offload expensive work to Queues/Workflows where possible. Fan-out to many DOs needs concurrency caps, backpressure, and per-run metrics.
- Ensure Wrangler migrations track class lifecycle.

## Cross-boundary RPC reachability

Workers and Durable Objects can expose JavaScript-native RPC across `DurableObject`, `WorkerEntrypoint`, `WorkflowEntrypoint`, `RpcTarget`, and Agents SDK classes. Generic dead-code tools often stop at the public class-member boundary because a stub, service binding, frontend proxy, or external repository might call the method.

When a TypeScript repo has these boundary classes:

- Inventory public non-runtime methods and separate platform hooks (`fetch`, `alarm`, `run`, `onConnect`, WebSocket callbacks, etc.) from app-specific RPC methods.
- Look for three caller shapes before treating a method as removable: TypeScript references, direct stub calls such as `.method()` / `["method"]()`, and string-key dispatch such as `.call("method", ...)` used by some proxy/Agent patterns.
- Scan companion frontend files (`.svelte`, `.vue`, `.astro`, `.tsx`, `.jsx`) when callers may live outside the Worker tsconfig.
- Treat "not called in this repo" as **needs verification** if external clients, old deployed versions, dynamic method names, API docs, or another repository may call it.
- Optional tool path: after explicit approval (or when already pinned in repo tooling), run `npx @acoyfellow/deadlint . --check dead-rpc --json` and treat output as leads, not proof.

## D1 reliability/performance

- Schema migrations are checked in and applied intentionally per environment.
- Queries use indexes for common filters/sorts; avoid unbounded `SELECT *`, `ORDER BY RANDOM()`, and table scans on hot paths.
- Batch statements where practical.
- Use constraints/unique indexes for correctness rather than only application checks.
- Add `LIMIT`/pagination to user-controlled queries.
- Cache read-heavy public results where consistency allows.

## R2 reliability/performance

- Stream large objects and support range requests for media/downloads when needed.
- Avoid list scans in hot paths; maintain manifests/indexes separately.
- Validate upload size/type and handle multipart completion/abort paths.
- Use deterministic object keys or idempotency to avoid duplicate writes during retries.
- Set cache headers/metadata at write time where possible.

## Queues, retries, and idempotency

- Producers attach idempotency keys or dedupe identifiers where duplicate processing matters, especially before Workers AI, Browser Run, Images/Stream transforms, D1 writes, R2 uploads, and third-party paid APIs.
- Consumers tolerate at-least-once delivery: side effects are idempotent, external calls have retry/backoff, and poison messages reach a DLQ or alerting path.
- Retry settings match downstream failure modes; avoid retry storms against a degraded API.
- User-facing endpoints enqueue quickly and return a status handle when work is asynchronous.

## Dynamic Workers, Agents, and sandboxed code reliability

- For Dynamic Workers, inventory every path that loads user/LLM-provided code. Confirm outbound egress, bindings, secrets, CPU/request/custom limits, and durable facets are explicitly granted rather than inherited accidentally.
- Record code hash/version, input, capabilities, timing, CPU-ish duration, logs, and output for every dynamic execution so failures and cost regressions can be traced.
- Cap nested Dynamic Worker creation and agent code-as-tool loops; do not let rooms spawn rooms without max depth, max unique Workers, and cancellation.
- For Agents SDK, check scheduled tasks, queue tasks, sub-agents, retries, durable execution, WebSockets, browser/sandbox tools, and autonomous responses for max steps, retry/backoff, cancellation, idempotency, and observability.
- For Artifacts-backed deployments or device/firmware update flows, require repo/token namespace separation, signed artifacts, rollback/A-B update path, and lifecycle cleanup of temporary repos/tokens.
- For Workers TCP/external database calls, verify TLS, connection lifetime, pooling/Hyperdrive support, regional latency, query timeouts, and retry/backoff. Avoid opening many outbound sockets in unbounded fanout.

## Observability

Check that the project can answer:
- Which route/resource is consuming CPU, subrequests, D1 rows, KV/R2 operations, DO duration/requests/storage ops, Dynamic Worker unique creations, Agent tool/browser/sandbox time, Artifacts operations, or queue retries?
- Which deployment introduced a regression?
- Are there alerts for failed queue consumers, DO errors, D1 migration failures, elevated 5xx, origin errors, cache hit ratio drops, and billing anomalies?
- Are logs sampled/redacted enough to control privacy and cost?
- If using a real-time logging sidecar (Durable Object/WebSocket/LRU cache) plus Analytics Engine/Logpush for history, what is the retention window, high-cardinality cap, fanout limit, replay/backfill story, and delay tolerance?

Repo clues:
- `observability` config in Wrangler.
- Structured logs with request IDs and no secrets.
- Analytics Engine/Logpush/Sentry/etc. integration.
- Tests or scripts for migrations and deployment checks.

## Testing and local runtime parity

- Prefer Miniflare/Workers runtime integration tests for bindings and `fetch` handlers.
- Avoid pure Node mocks for KV/D1/R2/DO behavior when the bug risk is platform semantics.
- Test environment-specific bindings and migrations.
- Include at least one test for auth/rate-limit/cache behavior on sensitive paths.
