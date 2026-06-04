# War-story-derived scenario checklist

Use this checklist to turn public billing/failure horror stories into concrete Cloudflare Doctor checks. War stories are not sources for current Cloudflare pricing or limits; use them to motivate scenarios, then cite current Cloudflare docs for Cloudflare-specific product facts.

## How to use

For each relevant scenario:

1. Confirm whether the project has the triggering shape in repo/IaC/dashboard/API evidence.
2. Fetch current official Cloudflare docs for the involved products.
3. If the scenario is confirmed, emit a finding with both:
   - `Source basis: Official Cloudflare docs ...`
   - `War story: ...` when the war story adds practical risk context.
4. If evidence is missing, put it under `Questions / evidence needed`.

## Cross-platform scenarios to check

### 1. Runaway async loop multiplies storage/compute operations

- Story: RetainDB reportedly generated a large Cloudflare bill from an infinite queue loop, billions of KV reads/writes, Durable Object storage writes, and hot-path `kv.list()` scans. Source aggregator: https://serverlesshorrors.com/all/cloudflare-36k; linked original: https://www.reddit.com/r/CloudFlare/comments/1t1e8nh/i_accidentally_generated_16_billion_durable/
- Source type: war story / first-hand linked via aggregator; verify original when using externally.
- Mechanism: queue message calls internal API with async mode, re-enqueues itself; unbatched DO writes multiply row writes; KV list scan runs on most auth requests.
- Cloudflare checks:
  - Queue consumers cannot enqueue the same logical job without idempotency/dedupe.
  - Queue retry limits, DLQ, poison-message alerts, backlog alerts exist.
  - DO storage writes are batched/coalesced; no per-field write storms.
  - KV `list()` is not on auth/request hot paths.
  - Run summary logs queue messages, retries, KV reads/writes/lists, DO writes, and logical user action IDs.
- Evidence to request: Queue config, consumer code, DLQ settings, Worker logs, GraphQL/usage metrics, code paths calling `send`, `sendBatch`, `storage.put`, `KV.list`.

### 2. Webhook/account-creation abuse triggers paid serverless functions

- Story: Stripe webhook delivery failure/abuse caused large Vercel bills through repeated webhook-triggered functions. Source: Convoy, “Stripe webhooks DoS caused $23k Vercel bills,” 2024-02-15, https://getconvoy.io/blog/stripe-webhook-delivery-failure; related ServerlessHorrors summary: https://serverlesshorrors.com/all/vercel-23k
- Source type: first-party blog / war story.
- Mechanism: mass account creation/trials caused many webhooks and serverless invocations; idempotency/rate-limit boundaries were insufficient.
- Cloudflare checks:
  - Webhook endpoints verify signatures before expensive work.
  - Webhook events use idempotency keys and persistent processed-event table/cache.
  - Trial/account creation has bot/rate-limit/Turnstile/WAF controls before Workers/D1/AI/Queue work.
  - Webhook handling enqueues bounded async work and returns quickly.
  - AI/browser/media jobs triggered by webhooks are deduped.
- Evidence to request: webhook route code, provider event IDs, D1/KV/DO dedupe table, WAF/rate-limit rules, Queue config, top routes by invocation.

### 3. Static-site bandwidth/DDoS turns into a giant bill

- Story: Netlify user reported a $104k bill for a simple static site after ~190TB bandwidth in 4 days; Netlify forum follow-up and Reddit post. Sources: https://answers.netlify.com/t/i-am-the-op-of-that-104k-bill-post-and-i-have-some-follow-up-questions/113472 and https://old.reddit.com/r/webdev/comments/1b14bty/netlify_just_sent_me_a_104k_bill_for_a_simple/; ServerlessHorrors summary: https://serverlesshorrors.com/all/netlify-104k
- Source type: first-hand forum/reddit + aggregator.
- Mechanism: attack or abnormal traffic on static assets creates metered bandwidth overage; provider did not hard-stop by default.
- Cloudflare checks:
  - Expensive/static routes are protected by WAF/rate limiting/bot controls where relevant.
  - Cache hit ratio is measured; static assets use immutable names and long TTLs.
  - Worker routes do not unnecessarily intercept static assets.
  - R2/Images/Stream delivery has cache/rate-limit controls and usage alerts.
  - Plan changes from hard limits to overages are understood.
- Evidence to request: Cache Analytics, WAF events, route patterns, `_routes.json`, Cache Rules, R2/Images/Stream usage, billing alerts.

### 4. Image optimization/transform APIs get crawled or variant-exploded

- Story: Metacast postmortem on LLM bots and Vercel Image API pricing. Source: “The Cost of Being Crawled: LLM Bots and Vercel Image API Pricing,” https://metacast.app/blog/engineering/postmortem-llm-bots-image-optimization; HN discussion: https://news.ycombinator.com/item?id=43687431
- Source type: first-hand engineering postmortem / war story.
- Mechanism: bots/crawlers request many image optimization URLs; transformations are metered and can multiply by width/format/DPR/quality/cache-key variants.
- Cloudflare checks:
  - Cloudflare Images/transform URLs use predefined variants or strict allowlists.
  - User-controlled width/height/format/quality/DPR are bounded.
  - Transformed outputs are cached with normalized keys.
  - Bot traffic is blocked/challenged before paid transformations.
  - Crawl budget and robots controls are considered for generated media.
- Evidence to request: image transformation code/rules, variant config, cache keys, top transformed URLs, bot/WAF analytics.

### 5. Firebase/Firestore/Storage reads or uncached origin objects explode

- Stories: “How not to get a $30k bill from Firebase,” Medium, 2019, https://medium.com/@PurpleGreenLemon/how-not-to-get-a-30k-bill-from-firebase-37a6cb3abaca (may require access); HN discussion “How we spent $30k in Firebase in less than 72 hours,” https://news.ycombinator.com/item?id=17661391; ServerlessHorrors Firebase $100k storage-origin abuse summary: https://serverlesshorrors.com/all/firebase-100k
- Official docs: Firebase “Avoid surprise bills,” https://firebase.google.com/docs/projects/billing/avoid-surprise-bills; Google Cloud budgets, https://cloud.google.com/billing/docs/how-to/budgets
- Source type: war stories + official docs.
- Mechanism: per-document reads/egress/storage requests or direct origin bucket access multiply under loops, bots, or uncached objects.
- Cloudflare checks:
  - D1 queries avoid N+1/full scans and report rows read.
  - R2 public/custom-domain buckets cannot be hit directly around intended Worker auth/cache controls.
  - Cache Rules and CDN are in front of public blobs where safe.
  - WAF/rate limits protect expensive object/query paths.
  - Billing/usage alerts exist per product.
- Evidence to request: D1 rows read, R2 operation counts, public bucket/custom domain settings, cache hit ratio, WAF/rate-limit rules.

### 6. Recursive Lambda/serverless invocations create runaway compute

- Official AWS docs: Lambda recursive loop detection, https://docs.aws.amazon.com/lambda/latest/dg/invocation-recursion.html; AWS Budgets, https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html; AWS Cost Anomaly Detection, https://docs.aws.amazon.com/cost-management/latest/userguide/getting-started-ad.html
- Source type: official docs; use war stories only as supplemental if fetched.
- Mechanism: function writes to a queue/topic/bucket/event source that invokes the same function or equivalent path; retries magnify.
- Cloudflare checks:
  - Workers/Queues/Workflows do not recursively trigger themselves without max depth/attempts/idempotency.
  - Cron triggers cannot overlap or enqueue unbounded jobs.
  - Workflows have step retry bounds and sleeps/backoff.
  - Kill switches can disable crons/consumers without redeploy.
- Evidence to request: Queue producers/consumers, cron triggers, Workflows definitions, code paths calling same route/queue/workflow.

### 7. Idle services are still billable or never scale to zero

- Railway docs: pricing plans and resource usage, https://docs.railway.com/pricing/plans.md; understanding your bill, https://docs.railway.com/pricing/understanding-your-bill.md; cost control, https://docs.railway.com/pricing/cost-control.md; serverless mode, https://docs.railway.com/deployments/serverless.md
- Heroku docs: usage and billing, https://devcenter.heroku.com/articles/usage-and-billing; Heroku limits, https://devcenter.heroku.com/articles/limits; old war story: “Tell HN: I accidentally ran up a $1000 Heroku bill,” https://news.ycombinator.com/item?id=1688904
- Source type: official docs + HN war story.
- Mechanism: dynos/containers/replicas/databases run while idle; demos/workshops/preview apps remain connected to paid services.
- Cloudflare checks:
  - Preview/demo/workshop envs are deleted or disconnected from paid services after use.
  - Cron triggers/Queue consumers are disabled in non-prod unless needed.
  - Durable Objects/Browser Run/Stream live inputs/Workflows are not kept active by idle timers/sessions.
  - Observability includes idle-but-billable resource inventory.
- Evidence to request: env list, routes/domains, crons, live inputs, Browser Run sessions, DO metrics, billing by resource.

### 8. Consumption-based functions hide cost in executions, memory, duration, logs, and dependencies

- Azure docs: Azure Functions consumption costs, https://learn.microsoft.com/en-us/azure/azure-functions/functions-consumption-costs; Azure budgets, https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-acm-create-budgets; Azure Functions best practices, https://learn.microsoft.com/en-us/azure/azure-functions/functions-best-practices
- Source type: official docs.
- Mechanism: invocation count alone is incomplete; memory, execution time, storage/logging dependencies, and retries contribute.
- Cloudflare checks:
  - Workers cost proxy includes CPU time/duration/subrequests, not only requests.
  - Logs/analytics/Logpush volume is sampled/redacted/bounded.
  - External dependency retries and queue replays are counted.
  - Run summaries include cost proxy fields.
- Evidence to request: Workers analytics, logs volume, subrequests, retry counts, Logpush destination/lifecycle.

### 9. Provider spend controls are alerts, not architecture

- Official docs: Vercel Spend Management, https://vercel.com/docs/pricing/spend-management; Netlify billing/usage, https://docs.netlify.com/manage/accounts-and-billing/billing; Firebase avoid surprise bills, https://firebase.google.com/docs/projects/billing/avoid-surprise-bills; Google budgets, https://cloud.google.com/billing/docs/how-to/budgets; Azure budgets, https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-acm-create-budgets
- Source type: official docs.
- Mechanism: budgets/alerts may notify after spend has begun; they do not replace rate limits, kill switches, queues, idempotency, and cache controls.
- Cloudflare checks:
  - Billing alerts exist but are not the only control.
  - Product-level kill switches and WAF/rate limits exist for expensive paths.
  - Quotas/backpressure are enforced in code/config before provider billing meters.
- Evidence to request: alert config, WAF/rate-limit rules, kill-switch flags, queue/backpressure implementation.

### 10. Cloudflare-fronted third-party origins still bill at the origin

- Sources: Vercel Spend Management, https://vercel.com/docs/pricing/spend-management; Railway cost-control docs, https://docs.railway.com/pricing/cost-control.md; Render billing/scaling docs, https://render.com/docs/billing and https://render.com/docs/scaling; Fly.io pricing/autostop docs, https://fly.io/docs/about/pricing/ and https://fly.io/docs/apps/autostart-stop/
- Source type: official docs.
- Mechanism: Cloudflare may absorb/cache some traffic, but cache misses, uncacheable requests, or direct default hostnames can still invoke paid serverless/container origins.
- Cloudflare checks:
  - DNS proxied status and origin lock-down are verified.
  - Default provider hostnames (`*.vercel.app`, `*.netlify.app`, `*.railway.app`, `*.onrender.com`, `*.fly.dev`, `*.herokuapp.com`, cloud storage endpoints) are not publicly bypassing Cloudflare controls.
  - Cache Rules cover expensive/static origin paths when safe.
  - WAF/rate-limit/bot controls run before origin-hit paths.
- Evidence to request: DNS exports, origin default URLs, origin firewall/auth settings, cache analytics, provider usage by route.

### 11. Public storage/object hotlinking creates request/egress bills

- Source: Maciej Pocwierz, “Anatomy of an AWS bill shock,” 2024, https://www.maciejpocwierz.com/posts/anatomy-of-a-aws-bill-shock/; AWS S3 pricing, https://aws.amazon.com/s3/pricing/
- Source type: first-hand war story + official docs.
- Mechanism: public object/storage endpoint receives unexpected requests because a bucket/object name or URL is guessed/reused/misconfigured; request charges and egress can accrue even when no app code runs.
- Cloudflare checks:
  - R2 public buckets/custom domains are intentional and cache/rate-limited.
  - Large/public objects use signed URLs/auth when private or cache when public.
  - Direct origin/bucket endpoints cannot bypass Cloudflare WAF/cache for protected content.
  - Storage operation counts are monitored.
- Evidence to request: R2 bucket public access/custom domains, CORS, object lifecycle, operation counts, cache rules, WAF coverage.

### 12. Logging/observability can become the surprise bill

- Sources: GCP Logging exclusions, https://cloud.google.com/logging/docs/exclusions; Azure Application Insights sampling, https://learn.microsoft.com/en-us/azure/azure-monitor/app/sampling; AWS CloudWatch pricing/docs as applicable; Cloudflare Logs/Workers Logs docs in [`official-source-map.md`](official-source-map.md).
- Source type: official docs.
- Mechanism: error storms, high-cardinality events, request-body logging, and long retention turn observability into a metered workload.
- Cloudflare checks:
  - Workers Logs/Logpush/Analytics Engine are sampled/redacted/bounded.
  - Log destinations have lifecycle/retention rules.
  - Error storms alert on rate and log volume, not just application failures.
  - Run summaries emit counters without logging sensitive/high-cardinality payloads.
- Evidence to request: logging config, Logpush jobs/destinations, Analytics Engine schemas, retention/lifecycle settings, log volume metrics.

### 13. Deploy previews/review apps become public paid environments

- Sources: Heroku Review Apps, https://devcenter.heroku.com/articles/github-integration-review-apps; Render preview environments, https://render.com/docs/preview-environments; Pages/Workers preview docs in [`official-source-map.md`](official-source-map.md).
- Source type: official docs.
- Mechanism: PR previews and workshops create public URLs, paid databases/add-ons/bindings, queue consumers, crons, or indexed content that persists after the intended test window.
- Cloudflare checks:
  - Preview/demo/workshop environments have no production paid bindings unless explicitly needed.
  - Preview routes are not indexed and are protected when sensitive.
  - Preview resources have TTL cleanup and disabled crons/consumers by default.
  - Billing dashboards can attribute spend by env/project.
- Evidence to request: Pages/Workers previews, env bindings, routes/domains, crons, queue consumers, D1/R2/KV namespaces, cleanup policy.

## Scenario-to-check matrix

| Scenario | Cloudflare products/configs to inspect |
|---|---|
| Attack traffic to static/media assets | WAF, rate limiting, bot controls, Cache Rules, Cache Analytics, Pages/Workers routes, R2 public/custom domains, Images, Stream |
| Third-party origin denial-of-wallet | DNS, proxied/unproxied records, origin default hostnames, WAF/rate limits, Cache Rules, origin auth/firewall, provider usage dashboards |
| Recursive async work | Queues, Workflows, Cron Triggers, Worker self-fetch, service bindings, DLQs, idempotency stores |
| Hot retries | Queues retry settings, Workflows retries, fetch retry loops, D1 retry code, AI/browser/media jobs |
| Duplicate expensive generation | Workers AI, AI Gateway caching/rate limits, Vectorize embedding/query flow, Images/Stream/Browser Run jobs |
| Direct origin/bucket bypass | DNS proxy status, R2 public/custom domains, origin firewall, Authenticated Origin Pulls, cache/WAF coverage |
| Public storage/object hotlinking | R2 public buckets/custom domains, signed URLs, cache rules, object operation counts, WAF/rate limiting |
| Meter hidden behind one request | Workers CPU/subrequests, D1 rows read, R2/KV ops, DO duration/storage writes, Queue retries, AI/Vectorize units |
| Temporary env left live | Pages previews, Workers preview URLs/routes, env bindings, crons, queues, D1/R2/KV prod sharing |
| Cache layer conflict/leak | Browser cache, CDN/Cache Rules, Worker Cache API, KV/D1/R2 caches, AI Gateway cache, cache keys/TTLs/purge |
| Logging as a meter | Workers Logs, Logpush, Analytics Engine, destination retention/lifecycle, log sampling/redaction, error-storm alerts |
| Public previews/review apps | Pages previews, Workers preview URLs, preview routes/domains, paid env bindings, crons, queues, cleanup/noindex policies |

## Checks to add or strengthen

- `CFDOC-COST-ASYNC-LOOP`: Queue/Workflow/Cron/self-fetch path can recursively trigger itself without idempotency/max depth.
- `CFDOC-COST-KV-LIST-HOTPATH`: KV list/prefix scan in auth or public hot route.
- `CFDOC-COST-DO-UNBATCHED-WRITES`: Multiple DO storage writes per logical record without batching/coalescing.
- `CFDOC-COST-WEBHOOK-NO-IDEMPOTENCY`: Webhook endpoint performs side effects or queues work before signature verification and idempotency check.
- `CFDOC-COST-MEDIA-VARIANT-EXPLOSION`: Images/Stream transformation or preload settings allow unbounded paid variants/minutes.
- `CFDOC-COST-TEMP-ENV-PAID-BINDINGS`: Preview/demo/workshop env has paid/prod bindings, routes, or crons.
- `CFDOC-COST-ORIGIN-BYPASS`: R2/origin can be hit directly around Cloudflare cache/WAF/auth controls.
- `CFDOC-COST-SPEND-ALERTS-ONLY`: Billing alerts exist but no rate limit/kill switch/backpressure for expensive paths.
- `CFDOC-COST-THIRD-PARTY-ORIGIN`: Cloudflare-fronted Vercel/Netlify/Railway/Render/Fly/Heroku/AWS/GCP/Azure/Supabase/Firebase origin can still be billed through cache misses or direct default hostname access.
- `CFDOC-COST-LOG-VOLUME`: Workers Logs/Logpush/Analytics Engine or external log ingestion can spike under error/bot traffic without sampling/retention controls.
- `CFDOC-COST-PREVIEW-PUBLIC-PAID`: Preview/review/demo environment is public, indexed, or connected to paid/prod services without TTL cleanup.
