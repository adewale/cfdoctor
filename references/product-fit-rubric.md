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
- WebSockets handled without Durable Object WebSocket hibernation when connections can be long-lived. Hibernation can reduce duration billing and survivability issues.
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

## Cache API, CDN cache, Cache Rules

Good fit:
- HTTP-cacheable responses, static assets, derived responses, origin shielding, public data with TTL/stale controls.

Smells:
- KV/R2/D1 read on every request for content that could be CDN-cached.
- Missing `Cache-Control`, `ETag`, `s-maxage`, `stale-while-revalidate`, or explicit cache keys on expensive public responses.
- Personalized/private responses cached under broad keys, causing data leaks.

## Hyperdrive and external databases

Good fit:
- Workers connecting to supported external SQL databases that need connection pooling and reduced cross-region latency.

Smells:
- Direct database connections from Workers without pooling/Hyperdrive where connection churn or geographic latency matters.
- Database region far from users/Workers with no Smart Placement or data-local strategy.
- ORM designed for long-lived Node processes used without checking Worker/runtime compatibility.

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
