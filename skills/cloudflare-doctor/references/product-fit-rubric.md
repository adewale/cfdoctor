# Cloudflare product-fit rubric

Use this rubric to decide whether the project is using the right Cloudflare primitive for the job. Treat every row as a diagnostic smell, not an automatic finding; confirm with access patterns and expected volume.

## Workers and Pages

Good fit:
- Request/response logic at the edge, APIs, middleware, SSR, auth gates, routing, lightweight transformations, cache orchestration, webhooks, and glue between Cloudflare services.
- Static sites and frontend deployments with Functions when the app lifecycle fits Pages.

Smells:
- Long-running jobs, batch processing, scraping, video/image processing, large compression, or slow third-party calls happen inline in a user request. Prefer Queues, Workflows, Cron Triggers, R2 event flows, or off-platform batch systems.
- Worker fetches another public Worker URL under the same account. Prefer service bindings to avoid public routing, auth ambiguity, latency, and extra request/accounting complexity.
- A Worker is mostly static asset serving with ad hoc headers. Prefer Workers Static Assets, Pages, or Cache Rules depending on control needs.
- Pages Functions are being stretched into a multi-service backend with many bindings, queues, and environment-specific routing. Consider Workers for explicit service boundaries and deploy control.

## KV

Good fit:
- Global, low-latency reads for configuration, feature flags, translations, small cached documents, sessions/tokens that tolerate eventual consistency, and TTL-based data.

Wrong-primitive smells:
- Counters, locks, rate limits, uniqueness checks, leader election, queues, inventory, financial state, or read-after-write correctness. Prefer Durable Objects for per-key coordination, D1 for relational transactional data, or Queues for work delivery.
- `KV.list()` or prefix scans in request hot paths. Prefer an index in D1, precomputed manifests, or cached metadata.
- Large blobs or user uploads in KV. Prefer R2.
- High-churn writes with immediate global reads. Recheck consistency requirements and billing.

## D1

Good fit:
- SQLite-compatible relational data, queries, indexes, transactional-ish application state, joins, migrations, and data that benefits from SQL constraints.

Wrong-primitive smells:
- D1 used as a high-throughput event queue, append-only log, blob store, or per-request analytics sink. Prefer Queues, R2, Analytics Engine, or Logpush.
- Request path does many sequential queries or unbounded `SELECT *`. Batch, index, add limits, denormalize carefully, or cache.
- No migration files or migration process for production. D1 schema drift becomes an operations risk.
- Strong per-key serialization logic built around D1 polling. Prefer Durable Objects for coordination.

## Durable Objects

Good fit:
- Per-key coordination, strongly consistent state for a single object, collaborative rooms, rate-limit buckets, WebSocket coordination, idempotency/locks, and localized state machines.

Wrong-primitive smells:
- One global object handles all traffic (`idFromName('global')`, `singleton`, one room for everything). This creates a hot spot; shard by tenant/user/key where possible.
- Durable Objects used as a general database or object-per-record store without a coordination need. Prefer D1/KV/R2 by data shape.
- One DO per ephemeral idempotency key, request ID, notification, or short-lived event. Prefer a bounded shard/time-bucket/keyspace with TTL cleanup, or KV/D1 if the access pattern does not need per-key serialization.
- Hierarchical DO chains/fleets where one request walks many parent/child objects, or fan-outs to many objects, without backpressure and a cost/latency budget.
- WebSockets handled without Durable Object WebSocket hibernation when connections can be long-lived. Hibernation can reduce duration billing and survivability issues.
- DO storage used for read-heavy, write-rare session/preference/config data that tolerates eventual consistency. KV or D1 may fit better once consistency and query needs are explicit.
- Class renamed or new class added without Wrangler migrations.

## R2

Good fit:
- Object/blob storage, user uploads, media/assets, backups, large files, data lake style storage, public or private buckets with Workers-mediated access.

Wrong-primitive smells:
- R2 bucket listing on every user request, prefix scans for metadata, or using object keys as a query system. Keep metadata/indexes in D1/KV/Search/Vectorize as appropriate.
- Tiny high-churn records stored as individual R2 objects. Operation counts and latency may dominate; use KV/D1/DO depending on consistency.
- Public bucket used for sensitive or tenant-scoped objects without signed URLs, auth checks, or cache controls.
- Large downloads proxied through a Worker that buffers the whole object instead of streaming/range-supporting.

## Queues

Good fit:
- Background work, retries, fan-out, asynchronous webhooks, smoothing bursts, decoupling user requests from slow dependencies.

Wrong-primitive smells:
- User requests synchronously wait on slow email/payment/AI/webhook/image work. Enqueue and return an accepted/idempotent response.
- Queue consumers lack idempotency keys, retry limits, DLQ strategy, or poison-message handling.
- Queue used where ordering/coordination per key is required. Combine with Durable Objects or design per-key serialization.

## Workflows / Cron Triggers

Good fit:
- Multi-step durable processes, scheduled jobs, retries with state, long business flows, recurring maintenance.

Smells:
- Cron every minute for polling that could be event-driven, queue-driven, webhook-driven, or batched less often.
- Long process encoded as recursive self-fetches or ad hoc KV state. Prefer Workflows/Queues/DO state machines.
- Workflow/DO-alarm loops drain a KV/D1/R2 work list without atomic claim/idempotency/max-iteration/kill-switch controls.
- Workflows used for high-frequency or low-latency per-request coordination. Workflows is a durable batch-and-steps engine, not a hot-path coordinator — use Durable Objects for per-request/per-key coordination and rate-limit-bucket latency.
- Conversely, prefer Workflows over a hand-rolled raw-Durable-Object state machine for multi-step durable flows (provisioning, payment orchestration, long jobs with retries/sleeps): you get durable execution, retries, and step visibility without reimplementing them on alarms.

## Dynamic Workers, Artifacts, and Agents SDK

Good fit:
- Dynamic Workers for short-lived isolated code execution, tenant/user-provided code, code-as-tool execution, and per-run sandboxes with explicit capabilities.
- Artifacts for Git-compatible versioned filesystem artifacts, repos, and repo-scoped tokens.
- Cloudflare Agents SDK for stateful AI agents that need Durable Object-backed state, real-time communication, scheduling, queue tasks, retries, and long-running coordination.

Wrong-primitive/security smells:
- Dynamic Workers executing untrusted/user/LLM-written code with inherited outbound network access, secrets, broad bindings, no custom limits, or no audit log of code hash/input/output.
- Dynamic Worker creation keyed by every request or prompt without reuse, TTL, or cost accounting for unique Dynamic Workers.
- Artifact repo tokens shared across tenants/environments or embedded in firmware/build artifacts; app/firmware update flows lack signing, rollback, and namespace separation.
- Agents with autonomous loops, tool calls, browser/sandbox tools, scheduled tasks, or sub-agents without max steps, retries/backoff, cancellation, idempotency, and per-run cost proxies.
- Browser-capable agents used for simple fetch/parse/API tasks where Workers fetch, Queues, or a lighter tool would be sufficient.

## Workers Cache, Cache API, CDN cache, Cache Rules

Good fit:
- HTTP-cacheable responses, static assets, derived responses, origin shielding, public data with TTL/stale controls.
- **Workers Cache** (`cache.enabled`) for caching a Worker's own `GET`/`HEAD` responses so hits skip Worker execution (saving CPU) and bursts collapse into one invocation. Cloudflare recommends it over the Cache API for new Workers; it is tiered by default.

Smells:
- KV/R2/D1 read on every request for content that could be CDN-cached.
- Missing `Cache-Control`, `ETag`, `s-maxage`, `stale-while-revalidate`, or explicit cache keys on expensive public responses.
- Personalized/private responses cached under broad keys, causing data leaks. With Workers Cache, tenant separation depends on `ctx.props` in the cache key, and auth/gateway entrypoints must set `cache.enabled = false` so a cache hit cannot skip the auth check.
- Reaching for the Cache API (`caches.default`) when Workers Cache would fit: the Cache API still runs the Worker on every request, is single-data-center, does not collapse concurrent requests, and `put()` silently no-ops on `Set-Cookie`/`no-store`/oversize/`206`/`Vary: *`.
- Enabling Workers Cache without modeling its billing-surface change: previously-free static-asset and worker-to-worker (service binding / `ctx.exports`) requests become billed at the standard request rate, and hits still bill a request (only CPU is saved).

## Hyperdrive and external databases

Good fit:
- Workers connecting to supported external SQL databases that need connection pooling and reduced cross-region latency.

Smells:
- Direct database connections from Workers without pooling/Hyperdrive where connection churn or geographic latency matters.
- Database region far from users/Workers with no Smart Placement or data-local strategy.
- ORM designed for long-lived Node processes used without checking Worker/runtime compatibility.
- Relying on Hyperdrive's **default-on query caching** for write-heavy or strong read-after-write paths. Caching is enabled by default (default `max_age` 60s, `stale_while_revalidate` 15s) and Hyperdrive does **not** invalidate cached results when your app writes, so a later matching `SELECT` can return a stale row until `max_age` expires. Hyperdrive fits read-heavy workloads; for post-write reads, auth/permission lookups, or strong consistency, disable caching (`--caching-disabled`) or route those queries through a second uncached binding, and set `max_age`/`stale_while_revalidate` intentionally.

## Email (Routing, the send_email binding, and Email Sending)

Good fit:
- **Email Routing** for receiving mail: custom addresses, catch-alls, and forwarding incoming email to a mailbox; process inbound mail with **Email Workers** (the `email()` handler) as an event source.
- The **`send_email` binding** (Email Workers) for a Worker to send outbound mail **only to verified/allowlisted destination addresses** (`allowed_destination_addresses`) — e.g. notifying your own team/ops inbox — **not** arbitrary user recipients.
- **Email Sending** (the outbound/transactional product) for originating mail to **arbitrary recipients** from your application.

Wrong-primitive smell:
- Code that expects to send outbound or transactional email to **arbitrary user addresses** (welcome/receipt/password-reset emails) via Email Routing or the `send_email` binding. Email Routing itself is inbound-only, and the `send_email` binding can deliver **only to pre-verified/allowlisted destinations**, so neither is a general transactional sender. Flag the mismatch and point arbitrary-recipient outbound at **Cloudflare Email Sending** (or a transactional provider such as Resend/Postmark/SES), keeping inbound handling on Email Routing/Email Workers.

## AI, media, browser automation, and vector search

Good fit:
- Workers AI for bounded inference/generation/embedding tasks with explicit quotas, caching/idempotency, and model choice.
- Vectorize for vector search where dimensions, namespaces, topK, and metadata filters are intentionally chosen.
- Images/Stream for managed media optimization/delivery when variant/minute economics are understood.
- Browser Run for tasks that truly require a browser: JS rendering, screenshots/PDFs, browser testing, authenticated human-in-the-loop automation.

Wrong-primitive smells:
- Browser Run used for simple HTTP fetch, metadata extraction, redirects, or static scraping that could use `fetch`, HTML parsing, APIs, Queues, or scheduled jobs.
- Workers AI generation/embedding invoked synchronously for repeated identical inputs with no idempotency, cache, AI Gateway, or retry cap.
- Vectorize used as a general database/search index without understanding stored/queried dimensions and metadata/filter limitations.
- Image transformations accept arbitrary user width/height/format/quality/DPR parameters instead of bounded variants.
- Stream used with eager preload/autoplay in feeds where delivered minutes are not tied to intentional viewing.

## Security products

Consider product fit rather than hand-rolling:
- Turnstile for bot/challenge flows.
- WAF custom/rate limiting rules for L7 abuse before traffic hits Workers.
- Cloudflare Access / Zero Trust for internal apps and admin surfaces.
- Bot Management/Super Bot Fight Mode where bot economics matter.
- mTLS/API Shield for sensitive machine APIs when applicable.

Smell: custom JavaScript-only bot checks, IP-block lists in code, or unauthenticated admin routes when Cloudflare security products could enforce closer to the edge.

Turnstile fit and UX caveats:
- Turnstile presence is not purely positive. It only protects an endpoint when the token is verified **server-side** (see [`config-and-security-checks.md`](config-and-security-checks.md)); a client-only widget is cosmetic.
- When Turnstile (or any CAPTCHA) is the **sole gate** on a critical or irreversible flow (login, signup, password reset, checkout), a minority of legitimate users can get stuck in unexplained challenge loops. Provide an alternate path or human-support escape and account for the support/accessibility cost — treat a hard CAPTCHA gate with no fallback as a reliability/UX trade-off, not an unconditional win.
