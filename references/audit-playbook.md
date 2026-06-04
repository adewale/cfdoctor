# Cloudflare Doctor audit playbook

## Evidence collection

Start by refreshing official documentation for the detected products. Use [`cloudflare-best-practices-docs.md`](cloudflare-best-practices-docs.md) and [`official-source-map.md`](official-source-map.md) as navigation aids, then fetch Cloudflare's live docs (`https://developers.cloudflare.com/llms.txt`, product `llms.txt`, and relevant Markdown pages). Do not rely on model memory for product behavior, best practices, limits, or pricing when live docs are available.

When dashboard/account state matters, use [`sharing-cloudflare-state.md`](sharing-cloudflare-state.md) to ask the user for the smallest useful evidence package. Prefer IaC/API exports/redacted screenshots over prose, and mark missing dashboard state as not inspected.

Inspect local files next:

```bash
find . -maxdepth 3 -type f \
  \( -name 'wrangler.toml' -o -name 'wrangler.json' -o -name 'wrangler.jsonc' -o -name 'package.json' -o -name 'vite.config.*' -o -name 'next.config.*' -o -name 'astro.config.*' -o -name 'terraform.tf' -o -name '*.tf' \) \
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

- **Workers/Pages**: `wrangler.toml/json`, `pages_build_output_dir`, `main`, `assets`, routes, custom domains, env sections, build scripts.
- **Bindings**: KV, D1, R2, Durable Objects, Queues, Hyperdrive, Vectorize, AI, Analytics Engine, service bindings, secrets, vars.
- **Runtime code**: fetch handlers, Pages Functions, Queue consumers, Durable Object classes, cron handlers, cache use, auth/rate limiting, external fetches.
- **Data model**: consistency requirements, write rate, read pattern, object size, query shape, transaction/coordination needs, TTL needs.
- **Account/zone**: DNS proxy status, SSL/TLS mode, WAF/rate limiting/bot rules, cache rules, Page Rules, Transform Rules, Access policies, Logpush/analytics.
- **Operations**: migrations, preview/staging/prod environments, local dev parity, observability, alarms, DLQs, rollback/deployment strategy.
- **Cost drivers**: expected request volume, subrequests per request, CPU time, storage/object counts, operation counts, queue retries, logs/analytics retention, add-on products.

## Mandatory high-risk cost-trap checklist

For every audit, explicitly consider and either report or mark not applicable / not inspected:

1. Workers cost model includes CPU time/duration/subrequests, not only request count.
2. Free-to-Paid plan changes may replace hard stops/included usage with overages or different throttling; verify current product pricing/limits.
3. D1 full scans, missing indexes, `SELECT *`, `ORDER BY RANDOM()`, offset pagination, and N+1 query patterns can multiply rows read.
4. Invalid/bot/unauthenticated traffic should be validated before calling Durable Objects.
5. Durable Objects should not stay active through idle WebSockets, timers, polling, or missing hibernation/alarms where hibernation/Queues/Workflows fit.
6. Expensive operations need idempotency/dedupe, especially Workers AI generation/embeddings and media/browser jobs.
7. Queues need bounded retries, idempotent consumers, DLQs/poison-message handling, and backlog/DLQ monitoring.
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
19. Run summaries should include cost proxies: CPU time, subrequests, storage ops, rows read/written, DO requests/duration, queue retry/DLQ counts, AI neurons/tokens/requests, Browser Run session minutes, image transformations, Stream delivered minutes, Vectorize dimensions queried/stored, and cache hit/miss assumptions.
20. Layered cache behavior should be explicit: where a request is cached, cache key dimensions, TTL, invalidation owner, and whether browser/CDN/Worker Cache/KV/R2/D1/AI Gateway caches can conflict or leak personalized data.

## Diagnosis loop

1. **Identify the primitive contract**. What does the app need: strong consistency, global low-latency reads, ordered coordination, relational queries, blob storage, background jobs, streaming, CDN caching, or access control?
2. **Compare to chosen product**. Use `product-fit-rubric.md` to spot mismatches.
3. **Check config shape**. Validate Wrangler/account configuration, env parity, migrations, routes, and security boundaries.
4. **Trace hot paths**. Count subrequests, storage operations, D1 rows read/written, R2 list calls, KV operations, CPU-heavy transforms, external origins, fanout, retries, and cacheability.
5. **Map cache layers**. For each hot request/job, list browser cache, CDN cache/Cache Rules, Worker Cache API, KV/D1/R2 metadata/content caches, AI Gateway/prompt caches, and app-level memoization. Record keys, TTLs, invalidation, personalization boundaries, and stale/read-after-write implications.
6. **Model failure mode**. Ask: what breaks at 10x traffic, multi-region concurrency, one failed dependency, hot retries, unbounded fanout, a retry storm, a leaked preview URL, or a billing threshold?
7. **Prescribe narrowly**. Recommend the smallest primitive/config/code change that removes the root risk. Avoid vague “use best practices” feedback.

## Finding standards

A Cloudflare Doctor finding is valid only if it includes:

- Evidence: path+line, config key, command output, dashboard/API export, or user-supplied architecture statement.
- Cloudflare-specific reason: consistency model, runtime limit, billing meter, route/cache behavior, security boundary, or product contract.
- Practical fix: exact config/code/account change or better primitive/product.
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
