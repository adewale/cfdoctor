# Cloudflare Doctor audit playbook

## Evidence collection

Start with a cheap repo/config/IaC inventory and scanner pass so the detected products and concrete hypotheses are evidence-based. Then use [`cloudflare-best-practices-docs.md`](cloudflare-best-practices-docs.md) and [`official-source-map.md`](official-source-map.md) as navigation aids and fetch only the relevant live Cloudflare docs (`https://developers.cloudflare.com/llms.txt`, product `llms.txt`, and applicable Markdown pages). Do not rely on model memory for product behavior, best practices, limits, or pricing when live docs are available.

When dashboard/account state could discriminate a hypothesis, use [`sharing-cloudflare-state.md`](sharing-cloudflare-state.md) to ask for the smallest useful evidence package. Prefer IaC/API exports/redacted screenshots over prose, and mark missing dashboard state as not inspected.

Use [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) to check for failure shapes that have caused real surprise bills on Cloudflare and adjacent serverless platforms. Treat war stories as scenario sources; still cite current Cloudflare docs for Cloudflare-specific pricing, limits, and product behavior.

Inspect local files next:

```bash
find . -maxdepth 3 -type f \
  \( -name 'wrangler.jsonc' -o -name 'wrangler.json' -o -name 'wrangler.toml' -o -name 'package.json' -o -name 'vite.config.*' -o -name 'next.config.*' -o -name 'astro.config.*' -o -name 'terraform.tf' -o -name '*.tf' \) \
  -not -path './node_modules/*' -not -path './.git/*'
rg -n "(kv_namespaces|d1_databases|r2_buckets|durable_objects|queues|hyperdrive|vectorize|ai|analytics_engine|services|routes|triggers|compatibility_date|compatibility_flags|observability)" .
```

If live docs cannot be fetched, record that gap in `Docs refreshed` and mark doc-dependent claims as needing current-doc verification.

If the user permits authenticated Cloudflare reads, useful evidence includes:

- `wrangler --version`
- `wrangler whoami`
- `wrangler secret list` / equivalent secret-name inventory
- `wrangler deployments list` or Pages deployment list
- `wrangler d1 migrations list <db>`
- `wrangler kv namespace list`, `wrangler r2 bucket list`, `wrangler queues list`
- Terraform state/plan, `cf-terraforming` output, dashboard screenshots, or Cloudflare API JSON for DNS/SSL/TLS/WAF/cache rules/Access/Zero Trust/Logpush.

Do not run mutating commands without explicit approval.

## Product inventory checklist

- **Workers/Pages**: `wrangler.jsonc`/`wrangler.json`/legacy `wrangler.toml`, `pages_build_output_dir`, `main`, `assets`, routes, custom domains, env sections, build scripts.
- **Bindings**: KV, D1, R2, Durable Objects, Queues, Hyperdrive, Vectorize, AI, Analytics Engine, Dynamic Worker Loaders, Artifacts, service bindings, secrets, vars.
- **Runtime code**: fetch handlers, Pages Functions, Queue consumers, Durable Object classes, Agents SDK classes, Dynamic Worker loader paths, cron/scheduled handlers, cache use, auth/rate limiting, external fetches/TCP sockets.
- **Data model**: consistency requirements, write rate, read pattern, object size, query shape, transaction/coordination needs, TTL needs.
- **Account/zone**: DNS proxy status, SSL/TLS mode, WAF/rate limiting/bot rules, cache rules, Page Rules, Transform Rules, Access policies, Logpush/analytics.
- **Third-party origins behind Cloudflare**: Vercel, Netlify, Railway, Render, Fly.io, Heroku, AWS/GCP/Azure, Firebase/Supabase/Fastly origins; default hostnames; origin lock-down; origin billing model.
- **Operations**: migrations, preview/staging/prod environments, local dev parity, observability, alarms, DLQs, rollback/deployment strategy.
- **Cost drivers**: expected request volume, subrequests per request, CPU time, storage/object counts, operation counts, queue retries, logs/analytics retention, add-on products.

## Mandatory high-risk cost-trap checklist

For every audit, explicitly consider and either report or mark not applicable / not inspected:

1. Separate direct Workers meters from amplification proxies: current Standard pricing directly meters requests and CPU, not duration or subrequests; subrequests still consume limits and can trigger separately metered downstream products. Verify Enterprise/legacy contracts.
2. Free-to-Paid plan changes may replace hard stops/included usage with overages or different throttling; verify current product pricing/limits.
3. D1 full scans, missing indexes, `ORDER BY RANDOM()`, offset pagination, and N+1 query patterns can multiply rows read. `SELECT *` is a projection/schema-coupling smell only until query-plan and `rows_read` evidence proves scanning.
4. Invalid/bot/unauthenticated traffic should be validated before calling Durable Objects.
5. Durable Objects should not stay active through idle WebSockets, timers, polling, or missing hibernation/alarms where hibernation/Queues/Workflows fit.
6. Expensive operations need idempotency/dedupe, especially Workers AI generation/embeddings and media/browser jobs.
7. Queues need idempotent consumers and an intentional terminal-failure policy. Current defaults are three retries followed by permanent deletion unless a DLQ is configured; add DLQ/poison-message handling and backlog/DLQ monitoring where loss is unacceptable.
8. R2 “no egress fees” is not “free”: storage, operations, Workers, logs, transforms, and lifecycle gaps can still bill.
9. Image transformations need bounded variants and normalized cache keys.
10. Stream preload/autoplay/buffering can increase delivered minutes.
11. Browser Run sessions need close paths, timeouts, bounded retries, and should not replace simpler primitives.
12. Vectorize cost can hide in queried/stored dimensions, topK, namespace fan-out, and repeated embedding/query loops.
13. Workers AI loops/retries/duplicate generation need caps, caching, and idempotency.
14. Preview, cron, workshop, and demo deployments should not remain connected to paid/production services.
15. Circuit breakers and kill switches should exist for expensive or failure-amplifying dependencies: AI, Browser Run, Images/Stream transforms, external APIs, Queue consumers, D1 write paths, and DO hot shards.
16. Hot retries should be bounded with exponential backoff/jitter and should not retry immediately into a degraded dependency or paid primitive.
17. Anti-rework caching should prevent duplicate expensive work for the same logical user action: generation, embedding, image/media/browser jobs, R2 uploads, Queue replays, and webhooks.
18. Fanout should be bounded: `Promise.all(items.map(...))`, queue fanout, batch sends, recursive workflows, crawler depth, and per-tenant broadcasts need caps/backpressure.
19. Run summaries should include cost proxies: CPU time, subrequests, storage ops, rows read/written, DO requests/duration, queue retry/DLQ counts, Workflow steps and retained-state storage, AI neurons/tokens/requests, Browser Run session minutes, unique image transformations, Stream delivered minutes, Vectorize dimensions queried/stored, and cache hit/miss assumptions.
20. Layered cache behavior should be explicit: where a request is cached, cache key dimensions, TTL, invalidation owner, and whether browser/CDN/Worker Cache/KV/R2/D1/AI Gateway caches can conflict or leak personalized data.
21. Durable Object gotchas should be checked when DOs are present: duration/WebSockets/hibernation, close hygiene, `storage.list()` hot paths, alarm recursion, sharding/hotspots, ephemeral object-per-idempotency-key patterns, backend-aware write coalescing/transactions, fan-out to many DOs, `ctx.waitUntil()` lifecycle, and KV-vs-DO-storage fit.
22. Dynamic Workers/Agents SDK/Artifacts should be checked when present: sandbox egress/bindings/secrets/custom limits, unique Dynamic Worker creation, code hash/audit logs, autonomous agent max steps/cancellation/retries, browser/sandbox tool costs, Artifacts token scope, signing, rollback, and namespace separation.
23. War-story scenario checks should be considered for matching products: recursive async work, webhook abuse, static/media DDoS bandwidth, image variant explosions, uncached object hotlinks, idle paid resources, direct origin/bucket bypass, and spend-alerts-only controls.
24. Cloudflare-fronted third-party origins should be checked for denial-of-wallet risk: cache misses, unproxied/default origin hostnames, wildcard routes/middleware, image optimization endpoints, autoscaling/serverless origins, log ingestion, and provider spend caps.
25. Self-fetch, rewrite, redirect, event-trigger, and origin loop risks should be checked across Workers, Pages Functions, Queues, Workflows, Cron Triggers, Durable Object alarms, Agents scheduled tasks, webhooks, and storage/database triggers.
26. Logging/analytics can be a surprise meter; high-cardinality or error-storm logs need sampling, retention, destination lifecycle rules, volume alerts, and a real-time-vs-history architecture when using DO/WebSocket sidecars plus Analytics Engine/Logpush.
27. Workers TCP/external database calls should be checked for Hyperdrive/product fit, TLS, connection pooling/lifetime, regional latency, timeouts, retries, and fanout.
28. For high-risk public surfaces, recommend a denial-of-wallet game day: synthetic traffic against static asset, function/API route, image transform, storage object, Dynamic Worker sandbox, browser/AI route, and webhook path to prove cache/rate-limit/auth/alerts fire.

## Diagnosis loop

1. **Identify the primitive contract**. What does the app need: strong consistency, global low-latency reads, ordered coordination, relational queries, blob storage, background jobs, streaming, CDN caching, or access control?
2. **Compare to chosen product**. Use `product-fit-rubric.md` to spot mismatches.
3. **Check config shape**. Validate Wrangler/account configuration, env parity, migrations, routes, and security boundaries.
4. **Trace hot paths**. Count subrequests, storage operations, D1 rows read/written, R2 list calls, KV operations, DO calls/duration/storage ops, Dynamic Worker creations/CPU, Agent tool/browser/sandbox/model runs, CPU-heavy transforms, external origins/TCP calls, fanout, retries, and cacheability.
5. **Map cache layers**. For each hot request/job, list browser cache, CDN cache/Cache Rules, Worker Cache API, KV/D1/R2 metadata/content caches, AI Gateway/prompt caches, and app-level memoization. Record keys, TTLs, invalidation, personalization boundaries, and stale/read-after-write implications.
6. **Model failure mode**. Ask: what breaks at 10x traffic, multi-region concurrency, one failed dependency, hot retries, unbounded fanout, a retry storm, a leaked preview URL, or a billing threshold?
7. **Prescribe narrowly**. Recommend the smallest primitive/config/code change that removes the root risk. Avoid vague “use best practices” feedback.

## Finding standards

A Cloudflare Doctor finding is valid only if it includes:

- Evidence: path+line, config key, command output, dashboard/API export, or user-supplied architecture statement.
- Cloudflare-specific reason: consistency model, runtime limit, billing meter, route/cache behavior, security boundary, or product contract.
- Practical fix: exact config/code/account change or better primitive/product.
- Cost/trade-off: billing meter or cost proxy affected, expected benefit, implementation effort, downside, reversibility, and assumptions.
- Verification: how to prove the fix and avoid regression.
- Source basis: official current Cloudflare docs fetched during the audit and/or an accepted war story as defined in [`recommendation-provenance.md`](recommendation-provenance.md).

If one of these is missing, present it as a **question/evidence needed** item instead of a confirmed finding. Pricing, limits, and billing-meter claims must use official current Cloudflare sources; war stories can supplement but not replace those.

## Common audit blind spots

- Treating local Wrangler config as the whole Cloudflare configuration. DNS, TLS, WAF, cache rules, Access, Turnstile, bot/rate limiting, Logpush, and billing add-ons often live outside the repo.
- Ignoring environment sections. A safe top-level config can still have a dangerous `[env.production]` route, binding, or var.
- Checking product presence but not access pattern. KV can be correct for config reads and wrong for counters; R2 can be correct for blobs and wrong for metadata queries.
- Reviewing request correctness but not cost per request. A working Worker that does 15 D1 queries, 4 KV reads, one R2 list, and no cache may be a cost bug.
- Missing preview/staging exposure. Pages/Workers preview deployments can expose debug endpoints or weaker auth if env separation is sloppy.
- Treating a retry policy as reliability without checking whether it retries hot into a degraded paid primitive.
- Finding a cache but not checking its layer, key, TTL, invalidation path, and interaction with adjacent caches.
