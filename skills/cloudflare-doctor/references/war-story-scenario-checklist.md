# War-story-derived scenario checklist

Use this checklist to turn public billing/failure horror stories into concrete Cloudflare Doctor checks. War stories are not sources for current Cloudflare pricing or limits; use them to motivate scenarios, then cite current Cloudflare docs for Cloudflare-specific product facts.

The canonical source/lineage/taxonomy record is the repo-only `research/incident-claim-ledger.json` in the [cfdoctor repository](https://github.com/adewale/cfdoctor/tree/main/research). Each scenario below carries an evidence ID; aggregators, mirrors, and discussions are aliases within one source cluster rather than independent corroboration. Incident observations, operator inferences, official guidance, and current product semantics remain distinct evidence classes.

Link and claim status last verified: 2026-08-09 (`scripts/check_links.py` and `scripts/check_claim_ledger.py`).

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

- Evidence ID: `CFDOC-EVD-RETAINDB-LOOP`

- Story: RetainDB reportedly generated a large Cloudflare bill from an infinite queue loop, billions of KV reads/writes, Durable Object storage writes, and hot-path `kv.list()` scans. Source aggregator: https://serverlesshorrors.com/all/cloudflare-36k; linked original: https://www.reddit.com/r/CloudFlare/comments/1t1e8nh/i_accidentally_generated_16_billion_durable/ (archived: https://web.archive.org/web/20260506025828/https://www.reddit.com/r/CloudFlare/comments/1t1e8nh/i_accidentally_generated_16_billion_durable/)
- Source type: war story / first-hand linked via aggregator; verify original when using externally.
- Mechanism: queue message calls internal API with async mode and re-enqueues itself; repeated DO writes and KV list scans amplify work. Current billing interpretation depends on the DO storage backend and rows/units changed—multi-key batching of distinct keys does not itself reduce billed storage units.
- Cloudflare checks:
  - Queue consumers cannot enqueue the same logical job without idempotency/dedupe.
  - Queue consumers are idempotent; a DLQ/alert/replay path exists when permanent deletion after the retry limit is unacceptable.
  - Redundant DO state writes are coalesced; transactions/multi-key writes are used for correctness/latency without assuming they reduce billed rows/units.
  - KV `list()` is not on auth/request hot paths.
  - Run summary logs queue messages, retries, KV reads/writes/lists, DO writes, and logical user action IDs.
- Evidence to request: Queue config, consumer code, DLQ settings, Worker logs, GraphQL/usage metrics, code paths calling `send`, `sendBatch`, `storage.put`, `KV.list`.

### 2. Webhook/account-creation abuse triggers paid serverless functions

- Evidence ID: `CFDOC-EVD-CONVOY-WEBHOOK`

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

- Evidence ID: `CFDOC-EVD-NETLIFY-104K`

- Story: Netlify user reported a $104k bill for a simple static site after ~190TB bandwidth in 4 days; Netlify forum follow-up and Reddit post. Sources: https://answers.netlify.com/t/i-am-the-op-of-that-104k-bill-post-and-i-have-some-follow-up-questions/113472 and https://old.reddit.com/r/webdev/comments/1b14bty/netlify_just_sent_me_a_104k_bill_for_a_simple/ (archived: https://web.archive.org/web/20250908035924/https://old.reddit.com/r/webdev/comments/1b14bty/netlify_just_sent_me_a_104k_bill_for_a_simple/); ServerlessHorrors summary: https://serverlesshorrors.com/all/netlify-104k
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

- Evidence ID: `CFDOC-EVD-METACAST-IMAGE`

- Story: Metacast postmortem on LLM bots and Vercel Image API pricing. Source: “The Cost of Being Crawled: LLM Bots and Vercel Image API Pricing,” https://metacast.app/blog/engineering/postmortem-llm-bots-image-optimization (archived: https://web.archive.org/web/20260304063157/https://metacast.app/blog/engineering/postmortem-llm-bots-image-optimization); HN discussion: https://news.ycombinator.com/item?id=43687431
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

- Evidence ID: `CFDOC-EVD-FIREBASE-READS`

- Stories: “How not to get a $30k bill from Firebase,” Medium, 2019, https://medium.com/@PurpleGreenLemon/how-not-to-get-a-30k-bill-from-firebase-37a6cb3abaca (archived: https://web.archive.org/web/20200429160249/https://medium.com/@PurpleGreenLemon/how-not-to-get-a-30k-bill-from-firebase-37a6cb3abaca) (may require access); HN discussion “How we spent $30k in Firebase in less than 72 hours,” https://news.ycombinator.com/item?id=17661391; ServerlessHorrors Firebase $100k storage-origin abuse summary: https://serverlesshorrors.com/all/firebase-100k
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

- Evidence ID: `CFDOC-EVD-AWS-RECURSION`

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

- Evidence ID: `CFDOC-EVD-IDLE-SERVICES`

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

- Evidence ID: `CFDOC-EVD-FUNCTION-METERS`

- Azure docs: Azure Functions consumption costs, https://learn.microsoft.com/en-us/azure/azure-functions/functions-consumption-costs; Azure budgets, https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-acm-create-budgets; Azure Functions best practices, https://learn.microsoft.com/en-us/azure/azure-functions/functions-best-practices
- Source type: official docs.
- Mechanism: invocation count alone is incomplete; memory, execution time, storage/logging dependencies, and retries contribute.
- Cloudflare checks:
  - Workers cost analysis separates direct request/CPU meters from duration and subrequests, which are limits/amplification proxies under current Standard pricing.
  - Logs/analytics/Logpush volume is sampled/redacted/bounded.
  - External dependency retries and queue replays are counted.
  - Run summaries include cost proxy fields.
- Evidence to request: Workers analytics, logs volume, subrequests, retry counts, Logpush destination/lifecycle.

### 9. Provider spend controls are alerts, not architecture

- Evidence ID: `CFDOC-EVD-SPEND-CONTROLS`

- Official docs: Vercel Spend Management, https://vercel.com/docs/pricing/spend-management; Netlify billing/usage, https://docs.netlify.com/manage/accounts-and-billing/billing; Firebase avoid surprise bills, https://firebase.google.com/docs/projects/billing/avoid-surprise-bills; Google budgets, https://cloud.google.com/billing/docs/how-to/budgets; Azure budgets, https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-acm-create-budgets. Cloudflare-native semantics (budget alerts, billable usage dashboard/API) are tracked in `CFDOC-EVD-CF-BUDGET-ALERTS`: Cloudflare budget alerts are informational only, do not pause or cap usage, and eligible Pay-as-you-go accounts get an auto-created $10 default alert — https://developers.cloudflare.com/billing/manage/budget-alerts/ and https://developers.cloudflare.com/billing/manage/billable-usage/
- Source type: official docs.
- Mechanism: budgets/alerts may notify after spend has begun; they do not replace rate limits, kill switches, queues, idempotency, and cache controls. On Cloudflare specifically there is no hard spend cap, alert scope must match the meters in use, and delivery latency should be verified rather than assumed (see scenario 24 for a first-hand detection-at-invoice case).
- Cloudflare checks:
  - Billing alerts exist but are not the only control.
  - Budget alert thresholds are deliberate (not only the $10 auto-created default), recipients are monitored, and per-product notifications cover the meters actually in use.
  - Product-level kill switches and WAF/rate limits exist for expensive paths.
  - Quotas/backpressure are enforced in code/config before provider billing meters.
  - Billable usage (dashboard or API) is reviewed on a cadence that matches how fast a runaway meter could spend.
- Evidence to request: alert config, notification history, billable usage export, WAF/rate-limit rules, kill-switch flags, queue/backpressure implementation.

### 10. Cloudflare-fronted third-party origins still bill at the origin

- Evidence ID: `CFDOC-EVD-THIRD-PARTY-ORIGIN`

- Sources: Vercel Spend Management, https://vercel.com/docs/pricing/spend-management; Railway cost-control docs, https://docs.railway.com/pricing/cost-control.md; Render scaling docs, https://render.com/docs/scaling (billing-page candidate removed after link verification failed); Fly.io pricing/autostop docs, https://fly.io/docs/about/pricing/ and https://fly.io/docs/apps/autostart-stop/
- Source type: official docs.
- Mechanism: Cloudflare may absorb/cache some traffic, but cache misses, uncacheable requests, or direct default hostnames can still invoke paid serverless/container origins.
- Cloudflare checks:
  - DNS proxied status and origin lock-down are verified.
  - Default provider hostnames (`*.vercel.app`, `*.netlify.app`, `*.railway.app`, `*.onrender.com`, `*.fly.dev`, `*.herokuapp.com`, cloud storage endpoints) are not publicly bypassing Cloudflare controls.
  - Cache Rules cover expensive/static origin paths when safe.
  - WAF/rate-limit/bot controls run before origin-hit paths.
- Evidence to request: DNS exports, origin default URLs, origin firewall/auth settings, cache analytics, provider usage by route.

### 11. Public storage/object hotlinking creates request/egress bills

- Evidence ID: `CFDOC-EVD-AWS-S3-HOTLINK`

- Source: the unavailable 2024 S3 bill-shock candidate was marked `superseded` at its 2026-07-11 review boundary because no recoverable primary page or independent corroboration was found; current AWS S3 pricing: https://aws.amazon.com/s3/pricing/
- Source type: rejected discovery lead + current official docs. Do not cite the incident as evidence; retain only the independently testable public-storage exposure hypothesis.
- Mechanism: public object/storage endpoint receives unexpected requests because a bucket/object name or URL is guessed/reused/misconfigured; request charges and egress can accrue even when no app code runs.
- Cloudflare checks:
  - R2 public buckets/custom domains are intentional and cache/rate-limited.
  - Large/public objects use signed URLs/auth when private or cache when public.
  - Direct origin/bucket endpoints cannot bypass Cloudflare WAF/cache for protected content.
  - Storage operation counts are monitored.
- Evidence to request: R2 bucket public access/custom domains, CORS, object lifecycle, operation counts, cache rules, WAF coverage.

### 12. Logging/observability can become the surprise bill

- Evidence ID: `CFDOC-EVD-LOGGING-METER`

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

- Evidence ID: `CFDOC-EVD-PREVIEW-EXPOSURE`

- Sources: Heroku Review Apps, https://devcenter.heroku.com/articles/github-integration-review-apps; Render preview environments, https://render.com/docs/preview-environments; Pages/Workers preview docs in [`official-source-map.md`](official-source-map.md).
- Source type: official docs.
- Mechanism: PR previews and workshops create public URLs, paid databases/add-ons/bindings, queue consumers, crons, or indexed content that persists after the intended test window.
- Cloudflare checks:
  - Preview/demo/workshop environments have no production paid bindings unless explicitly needed.
  - Preview routes are not indexed and are protected when sensitive.
  - Preview resources have TTL cleanup and disabled crons/consumers by default.
  - Billing dashboards can attribute spend by env/project.
- Evidence to request: Pages/Workers previews, env bindings, routes/domains, crons, queue consumers, D1/R2/KV namespaces, cleanup policy.

## Cloudflare-native operator notes from coey.dev

These are not pricing authorities. Use them as scenario/check sources, then cite official Cloudflare docs for current product behavior, pricing, limits, and APIs.

### 14. Durable Object duration, storage, alarm, and sharding gotchas

- Evidence ID: `CFDOC-EVD-COEY-DO-GOTCHAS`

- Source: Jordan Coeyman, “Durable Objects Gotchas: The Quiz You Wish You Had,” 2025-12-22 metadata, https://coey.dev/durable-objects-gotchas; related design note “The Perfect Durable Object?,” 2025-12-23, https://coey.dev/perfect-do
- Source type: operator checklist/design note; scenario source only, not a standalone pricing/limits authority. Coey's embedded example prices must be re-verified with Cloudflare pricing docs before use.
- Mechanisms to check:
  - `DO-WEBSOCKET-DURATION`: long-lived idle WebSockets can make wall-clock duration dominate unless hibernation/cleanup fits.
  - `DO-SOCKET-CLOSE-HYGIENE`: missing close/error/timeout cleanup leaves zombie sessions or stale connection state.
  - `DO-STORAGE-LIST-HOTPATH`: `storage.list()` on every request/wake-up turns known-key reads into list/pagination work.
  - `DO-ALARM-RECURSION`: alarm handlers that always call `setAlarm()` can create recurring wake-ups when idle.
  - `DO-SHARDING-HOTSPOT`: singleton/low-cardinality objects hot-spot; over-sharding ephemeral keys multiplies objects.
  - `DO-EPHEMERAL-IDEMPOTENCY-OBJECTS`: one DO per idempotency/request key is often wasteful; prefer bounded shard/time buckets or another primitive.
  - `DO-STORAGE-BATCHING`: repeated writes need backend-aware coalescing/transaction review. Coalescing redundant state can reduce rows/units; batching distinct keys alone does not.
  - `DO-FANOUT-TAX`: one request/job calling hundreds/thousands of DO stubs needs backpressure and urgency distinction.
  - `DO-WAITUNTIL-LIFECYCLE`: DO background work should use the correct lifecycle API and be bounded; long work may belong in alarms/Queues/Workflows/Agents durable execution.
  - `KV-VS-DO-STORAGE-FIT`: read-heavy, write-rare data that tolerates eventual consistency may not need DO storage/duration.
- Cloudflare docs to pair: Durable Objects pricing, limits, WebSocket hibernation, alarms, storage access, rules of Durable Objects, metrics/analytics; KV consistency/pricing where comparing KV.
- Evidence to request: DO class code, stub routing/id naming, WebSocket handlers, alarms, storage access patterns, metrics for requests/duration/storage ops, object cardinality estimate, queue/workflow alternatives.

### 15. Cloudflare loop patterns can become self-triggering work

- Evidence ID: `CFDOC-EVD-COEY-LOOPS`

- Source: Jordan Coeyman, “Self: Two Tiny Cloudflare Loop Patterns,” 2026-03-05, https://coey.dev/self; “Loop: I'm Not in Control, I'm Just Another Iteration,” 2026-01-20, https://coey.dev/loop; “loop-demo: Dogfooding Until It Worked,” 2026-01-30, https://coey.dev/loop-demo
- Source type: operator design notes/prototypes.
- Mechanism: a Durable Object alarm or Workflow wakes, claims work from KV/state, writes progress, sleeps, and repeats. Without atomic claim, idempotency, max iterations, pause/kill switch, and run summaries, the pattern can become a runaway async loop or silent retry spend.
- Cloudflare checks:
  - DO alarms/Workflows/Cron/Agents scheduled tasks reschedule only when work remains.
  - Claim/lease logic is idempotent and at-least-once safe.
  - There is a pause/kill switch that can stop the loop without deployment.
  - Each iteration logs cost proxies and progress/error summaries without unbounded log volume.
- Evidence to request: alarm/workflow code, KV/D1/R2 work-list schema, claim/lease tests, max iteration config, pause flag, run summary logs, usage metrics.

### 16. Dynamic Workers and code-as-tool sandboxes need capability bounds

- Evidence ID: `CFDOC-EVD-COEY-DYNAMIC`

- Source: Jordan Coeyman, “Worker Loaders as a Place,” 2026-03-27, https://coey.dev/worker-loaders; “Promptlog: Dynamic Worker Loader with Sandboxed Code Execution,” 2025-10-14, https://coey.dev/promptlog; “desk and living-artifact,” 2026-05-15, https://coey.dev/built-in-reverse
- Source type: operator design notes/prototypes.
- Mechanism: Workers or Agents create isolated Dynamic Workers/Worker Loader rooms to execute user/LLM/app code; security and cost depend on egress, bindings, secrets, custom limits, code identity, and lifecycle. Artifacts-backed app/firmware loaders add repo-token, signing, and rollback risks.
- Cloudflare checks:
  - Dynamic Workers are deny-by-default for egress/bindings/secrets unless a capability is explicitly required.
  - Custom limits, timeouts, max unique Dynamic Workers, and max nested spawns are configured or enforced in code.
  - Code hash/version, input, output, logs, and capabilities are auditable and bounded.
  - Artifact repo tokens are scoped/rotatable; app/firmware artifacts are signed; rollback/A-B deploy exists for device updates.
- Evidence to request: dynamic Worker loader code/config, egress policy, bindings, custom limits, code hashing/dedupe, logs, Artifacts namespace/repo/token model, signing/rollback docs.

### 17. Cloudflare Agents and browser/session tools hide long-running cost

- Evidence ID: `CFDOC-EVD-COEY-AGENTS`

- Source: Jordan Coeyman, “Cloudflare Agents Patterns: Using the Agents SDK,” 2025-11-29, https://coey.dev/agents-patterns; “AgentCast: Live browser sessions for AI agents,” 2025-12-08, https://coey.dev/agentcast; “Parley: Two AIs Debate Until They Agree,” 2026-02-02, https://coey.dev/parley
- Source type: operator design notes/prototypes.
- Mechanism: Agents are long-lived Durable Objects with state, scheduling, tools, browser/sandbox sessions, and streaming. Planning/debate/browser loops can keep sessions alive or repeat model/tool work without proving improved outcome.
- Cloudflare checks:
  - Agents have max steps, cancellation, retry/backoff, idempotency, and per-run model/tool/browser cost proxies.
  - Browser sessions close in `finally`, have timeouts, and are only used when fetch/API/static parsing is insufficient.
  - Streaming/SSE/WebSocket connections have disconnect cleanup and hibernation/lifecycle posture.
  - Scheduled/autonomous responses cannot loop indefinitely or spam external/webhook targets.
- Evidence to request: Agent classes, scheduled tasks, queue tasks, sub-agents, browser/sandbox tool calls, session close paths, usage dashboards, run summaries.

### 18. Real-time logging sidecars can solve UX while adding meters

- Evidence ID: `CFDOC-EVD-COEY-REALTIME-LOGS`

- Source: Jordan Coeyman, “Real-Time Logging on Cloudflare,” 2025-09-15, https://coey.dev/real-time-logging; related “Checkout Reality: Playwright + Gateproof,” 2026-01-28, https://coey.dev/checkout-reality
- Source type: operator pattern notes.
- Mechanism: a Durable Object/WebSocket/LRU layer can provide instant logs while Analytics Engine/Logpush stores queryable history. This helps verification but can add DO duration/fanout/log-volume cost and privacy risk if retention/sampling is absent.
- Cloudflare checks:
  - Separate realtime window from long-term history; define TTL/retention and high-cardinality limits.
  - Do not log secrets, payment tokens, request bodies, or tenant-private data unnecessarily.
  - Logging is sampled/bounded under error storms and can answer backend-reality questions, not just DOM success.
- Evidence to request: Workers Logs/Analytics Engine/Logpush config, DO logging room code, WebSocket fanout, event schema, retention/lifecycle, log-volume metrics.

### 19. Worker security controls for OAuth/webhooks deserve source-backed review

- Evidence ID: `CFDOC-EVD-COEY-SECURITY`

- Source: Jordan Coeyman, “How we passed Google CASA Tier 2 on a Cloudflare Worker,” 2025-06-24, https://coey.dev/casa-tier-2; “Bio: Single-button WebAuthn auth on Cloudflare,” 2025-11-21, https://coey.dev/bio
- Source type: first-hand security implementation note.
- Mechanism: Cloudflare Workers can host sensitive OAuth/WebAuthn/webhook surfaces, but controls must be explicit: security headers, sanitized errors, timing-safe comparisons, encryption of tokens, redirect URI allowlists, rate limiting, webhook verification, and idempotency.
- Cloudflare checks:
  - Auth/webhook endpoints verify signatures/timestamps before expensive work or state mutation.
  - OAuth callback redirect URIs are allowlisted; tokens/secrets are encrypted or stored in appropriate secrets/storage; errors do not leak stack traces/secrets.
  - Rate limits/Turnstile/WAF/Access protect sensitive and expensive paths before storage/AI/Queues.
- Evidence to request: auth/callback/webhook code, token storage schema, secrets inventory, WAF/rate-limit rules, tests for replay/idempotency/error sanitization.

### 20. Workers-to-database/TCP paths need pooling, TLS, and regional thinking

- Evidence ID: `CFDOC-EVD-COEY-TCP`

- Source: Jordan Coeyman, “Edgewire: Node.js TCP libraries in Cloudflare Workers,” 2025-12-09, https://coey.dev/edgewire
- Source type: operator implementation note.
- Mechanism: Workers can connect to external TCP databases/libraries, but direct sockets can expose connection churn, TLS, unsupported database, latency, and retry/fanout risks. Hyperdrive may fit supported databases; unsupported protocols need explicit controls.
- Cloudflare checks:
  - Verify whether Hyperdrive or Cloudflare-native storage fits before hand-rolled TCP adapters.
  - External DB connections use TLS, timeouts, bounded concurrency, backoff, and close/reuse semantics suitable for Workers.
  - Query counts/latency from global edge locations are measured and not hidden behind one request.
- Evidence to request: TCP socket code, database driver config, TLS options, pooling strategy, query logs, timeouts, retry/backoff, Hyperdrive fit analysis.

### 21. Correctness, preflight, and adversarial gates improve audit quality

- Evidence ID: `CFDOC-EVD-COEY-EVAL-GATES`

- Source: Jordan Coeyman, “Prompts Are Wishes,” 2026-03-04, https://coey.dev/prompts-are-wishes; “gate-review: Red-Team Your Tests,” 2026-01-30, https://coey.dev/gate-review; “preflight: The Agent That Learned to Slow Down,” 2026-01-30, https://coey.dev/preflight; “Compaction,” 2026-02-23, https://coey.dev/compaction; “Cursing Agents,” 2026-05-23, https://coey.dev/cursing-agents
- Source type: agent/audit process notes.
- Mechanism: natural-language prompts and self-written tests can produce fake-green results. For Cloudflare Doctor, this motivates executable checks, adversarial review, explicit source provenance, and externalized run summaries after context compaction.
- Cloudflare checks:
  - Recommendations are backed by official docs or accepted war stories, not prompt confidence.
  - Tests/gates include hidden/adversarial cases for cache/auth/billing paths, not only happy-path UI assertions.
  - Audit output records docs refreshed, cost proxies, cache maps, and evidence gaps so future turns do not infer missing dashboard state.
- Evidence to request: tests/gates, CI checks, audit artifacts, run summaries, docs URLs fetched.

### 22. Dead public cross-boundary RPC methods evade generic linters

- Evidence ID: `CFDOC-EVD-DEADLINT-RPC`

- Source: Jordan Coeyman X post, 2026-05-13, https://x.com/acoyfellow/status/2054685542369952158; `deadlint` repository, https://github.com/acoyfellow/deadlint
- Source type: operator tooling note; scenario source only. Pair with current Cloudflare Workers RPC, Durable Objects, and Agents docs before making platform/API claims.
- Mechanism: public methods on `DurableObject`, `WorkerEntrypoint`, `WorkflowEntrypoint`, `RpcTarget`, and `Agent` subclasses look like live API surface to generic linters (`knip`, `oxlint`, ESLint), so stale methods can accumulate. Some may still be callable by stubs, service bindings, frontend RPC proxies, old deployed clients, or cross-repo callers.
- Cloudflare checks:
  - Inventory public non-runtime methods on cross-boundary classes separately from platform hooks (`fetch`, `alarm`, `run`, WebSocket callbacks, Agent lifecycle hooks).
  - Before deleting, check TypeScript references, `.method()` / `["method"]()` calls, `.call("method", ...)` string dispatch, companion frontend files, API docs, old versions, and cross-repo clients.
  - Optional tool path: with explicit approval or pinned repo tooling, run `npx @acoyfellow/deadlint . --check dead-rpc --json` and treat output as leads, not proof.
- Evidence to request: boundary class code, TypeScript config(s), generated/typed RPC stubs, frontend companion files, service bindings, public client/API docs, and evidence of external callers.

### 23. Enabling Workers Cache changes the billing surface and can bypass auth

- Evidence ID: `CFDOC-EVD-WORKERS-CACHE-LAUNCH`

- Source: Cloudflare blog, "Your Worker can now have its own cache in front of it," 2026-07-06, https://blog.cloudflare.com/workers-cache/; official docs https://developers.cloudflare.com/workers/cache/ and https://developers.cloudflare.com/workers/cache/limitations/
- Source type: official product announcement + docs. Verify pricing/limits against current docs before quoting numbers.
- Mechanism: Workers Cache (`cache.enabled`) puts a tiered cache in front of the Worker. A cache hit skips Worker execution — saving CPU but still billing a request — and, because it skips execution, it also skips any auth/gateway logic on that entrypoint. Enabling it also bills requests that are normally free (static assets and worker-to-worker invocations via service bindings / `ctx.exports`), so a static-heavy or fan-out-heavy Worker can get *more* expensive even though per-request CPU drops.
- Cloudflare checks:
  - Auth/gateway entrypoints set `cache.enabled = false`; only inner, safely cacheable entrypoints are cached. Automatic bypass for `Set-Cookie`/`Authorization` is a backstop, not the authorization boundary.
  - Multi-tenant separation is carried by `ctx.props` in the cache key (not hostname/cookies); callers over service bindings set distinct `ctx.props`.
  - Billing-surface change is modeled: hits still bill a request, and normally-free static-asset and worker-to-worker traffic becomes billed at the standard request rate.
  - `Cache-Control`/TTL, `Vary`, and `ctx.cache.purge()` ownership are intentional; only `GET`/`HEAD` are cached (`206`, `520`–`526`, WebSocket upgrades, and custom RPC methods bypass).
- Evidence to request: Wrangler `cache`/`exports[*].cache` config, entrypoint layout (which entrypoint authenticates), `Cache-Control` headers set in code, `ctx.props`/cache-key composition, purge call sites, and request/CPU metrics before vs after enabling.

### 24. Two Durable Objects re-trigger each other; the rows-read meter dominates; budget alerts arrive too late

- Evidence ID: `CFDOC-EVD-STDAGENTS-DO-LOOP`

- Story: StandardAgents reported an $8,846.78 Cloudflare cycle (2026-07-09 to 2026-08-09) after "2 Durable Objects deep in our stack infinite looped." The attached spend breakdown shows Durable Objects Storage Rows Read at $8,710.39 (98.5%) versus under $50 each for DO compute requests, duration, and rows written; daily spend ramped from ~$40 to ~$600 within a week, ran ~3 weeks, stopped around 2026-07-30, and the team learned of it from the cycle-end bill on 2026-08-08. Their auto-created $10 default budget alert reported "88468% of $10.00 budget" at cycle close, and their pre-existing Workers-scoped usage notifications could not see the DO storage meter. Sources: Justin Schroeder, 2026-08-08, https://x.com/jpschroeder/status/2086144942657712500; Boyd thread, 2026-08-08, https://x.com/0xboyd/status/2086136894803279932 and https://x.com/0xboyd/status/2086143037042749480
- Source type: first-hand operator posts with billing screenshots, one source cluster; scenario source only. Cite current Cloudflare docs for pricing, alert semantics, and limits.
- Mechanism: two DO classes hand work to each other through stubs, and the chain detaches via `waitUntil`/alarms/queued work, so per-invocation subrequest limits reset on every hop and nothing platform-side stops the loop. When each hop re-reads growing state (`storage.sql.exec` SELECT without bounds, or `storage.list()`), SQLite-backed rows read compound roughly quadratically — the bill signature is rows read >> rows written with small request/duration meters. Cloudflare budget alerts are informational only (no pause/cap), so detection defaults to the invoice unless the team watches daily billable usage.
- Cloudflare checks:
  - `DO-STUB-CALL-CYCLE`: no DO-to-DO stub-call cycles without an explicit per-hop depth/budget guard, idempotency/turn key, and kill-switch check inside the loop step.
  - `DO-SQL-SCAN-HOTPATH`: hot-path `storage.sql.exec` SELECTs carry WHERE/LIMIT bounds backed by indexes; growing tables are not re-scanned per hop.
  - `CFDOC-COST-SPEND-ALERTS-ONLY`: a budget alert exists beyond the $10 auto-created default, thresholds match expected daily burn, recipients are monitored, the team knows alerts are informational only and may lag, and per-product notifications cover the meters actually in use (DO storage, not just Workers requests).
  - Billable usage (dashboard/API) is reviewed daily, or polled with an anomaly threshold, so a runaway meter is caught in hours-to-days rather than at invoice time.
  - A kill switch (config/KV/DO-storage flag checked inside every hop, plus `deleteAlarm()`/queue-pause/rollback paths) can stop detached loops without a deploy.
- Evidence to request: Wrangler `durable_objects` bindings and migrations, DO class code and stub call graph, alarm/`waitUntil` usage, SQL/storage access patterns, budget alert configuration and notification history, billable usage export or API output for the affected cycle, and DO metrics (requests, duration, storage rows) for the loop window.

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
| Meter hidden behind one request | Workers CPU/subrequests, D1 rows read, R2/KV ops, DO duration/requests, DO storage rows read/written (SQLite), Queue retries, AI/Vectorize units |
| DO-to-DO loop / detached re-trigger | `durable_objects` bindings, DO class stub call graph, `waitUntil`/alarm chains, hop budgets, idempotency keys, kill-switch flags, DO rows-read/request metrics |
| Budget alerts / spend detection latency | Budget alert config and thresholds (incl. the $10 auto-created default), notification history, per-product usage notifications vs meters in use, billable usage dashboard/API cadence |
| Temporary env left live | Pages previews, Workers preview URLs/routes, env bindings, crons, queues, D1/R2/KV prod sharing |
| Cache layer conflict/leak | Browser cache, CDN/Cache Rules, Workers Cache (`cache.enabled`), Worker Cache API, KV/D1/R2 caches, AI Gateway cache, cache keys/TTLs/purge |
| Workers Cache billing/auth surface | Wrangler `cache`/`exports[*].cache`, auth/gateway entrypoint exclusion, `ctx.props` cache-key separation, `Cache-Control`/`Vary`, `ctx.cache.purge()`, request/CPU metrics before vs after |
| Logging as a meter | Workers Logs, Logpush, Analytics Engine, destination retention/lifecycle, log sampling/redaction, error-storm alerts |
| Public previews/review apps | Pages previews, Workers preview URLs, preview routes/domains, paid env bindings, crons, queues, cleanup/noindex policies |
| Durable Object billing/lifecycle gotchas | DO WebSockets, hibernation, alarms, storage list/get/put patterns, shard keys, object cardinality, stub fanout, idempotency design, metrics |
| Dynamic Worker/code-as-tool sandbox | Dynamic Worker Loader, egress control, bindings/secrets, custom limits, code hashes, nested spawns, logs, Dynamic Workers pricing/usage |
| Agents SDK autonomous loops/tools | Agent classes, scheduled tasks, queue tasks, sub-agents, retries, browser/sandbox tools, WebSockets/SSE, cancellation, observability |
| Artifacts-backed app/firmware loaders | Artifacts namespaces/repos/tokens, signed releases, A-B/rollback flow, device/app update channels, token rotation |
| Workers TCP/external database | TCP sockets, Node `net`, Hyperdrive fit, TLS, pooling/reuse, timeouts, bounded concurrency, DB region/query metrics |
| Dead cross-boundary RPC methods | `DurableObject`, `WorkerEntrypoint`, `WorkflowEntrypoint`, `RpcTarget`, `Agent` classes, public methods, TS references, stub calls, `.call("method")`, companion frontend files, cross-repo clients |
| OAuth/WebAuthn/webhook security | Workers handlers, headers, CORS, token encryption, redirect allowlists, timing-safe compares, webhook signatures/idempotency, WAF/rate limits |

## Checks to add or strengthen

- `CFDOC-COST-ASYNC-LOOP`: Queue/Workflow/Cron/self-fetch path can recursively trigger itself without idempotency/max depth.
- `CFDOC-COST-KV-LIST-HOTPATH`: KV list/prefix scan in auth or public hot route.
- `CFDOC-COST-DO-UNBATCHED-WRITES`: Duplicate alias of the backend-aware DO coalescing/transaction review; do not infer billing savings from batching distinct keys.
- `CFDOC-COST-WEBHOOK-NO-IDEMPOTENCY`: Webhook endpoint performs side effects or queues work before signature verification and idempotency check.
- `CFDOC-COST-MEDIA-VARIANT-EXPLOSION`: Images/Stream transformation or preload settings allow unbounded paid variants/minutes.
- `CFDOC-COST-TEMP-ENV-PAID-BINDINGS`: Preview/demo/workshop env has paid/prod bindings, routes, or crons.
- `CFDOC-COST-ORIGIN-BYPASS`: R2/origin can be hit directly around Cloudflare cache/WAF/auth controls.
- `CFDOC-COST-SPEND-ALERTS-ONLY`: Billing alerts exist but no rate limit/kill switch/backpressure for expensive paths.
- `CFDOC-COST-THIRD-PARTY-ORIGIN`: Cloudflare-fronted Vercel/Netlify/Railway/Render/Fly/Heroku/AWS/GCP/Azure/Supabase/Firebase origin can still be billed through cache misses or direct default hostname access.
- `CFDOC-COST-LOG-VOLUME`: Workers Logs/Logpush/Analytics Engine or external log ingestion can spike under error/bot traffic without sampling/retention controls.
- `CFDOC-COST-WORKERS-CACHE-BILLING`: Workers Cache (`cache.enabled`) is on; verify hits still bill a request, that normally-free static-asset and worker-to-worker traffic becoming billed is intended, and that auth/gateway entrypoints set `cache.enabled = false`.
- `CFDOC-COST-PREVIEW-PUBLIC-PAID`: Preview/review/demo environment is public, indexed, or connected to paid/prod services without TTL cleanup.
- `DO-WEBSOCKET-DURATION`: Long-lived DO WebSocket lacks hibernation/close strategy and duration observability.
- `DO-STORAGE-LIST-HOTPATH`: DO storage list/prefix scan appears on request, alarm, or wake-up path.
- `DO-ALARM-RECURSION`: DO alarm reschedules itself unconditionally or without max/backoff/idle checks.
- `DO-SOCKET-CLOSE-HYGIENE`: WebSocket path lacks obvious close/error/timeout cleanup.
- `DO-SHARDING-HOTSPOT`: DO IDs use singleton/low-cardinality keys or unbounded high-cardinality ephemeral keys.
- `DO-EPHEMERAL-IDEMPOTENCY-OBJECTS`: One DO per idempotency/request key instead of bounded shard/time bucket/TTL store.
- `DO-STORAGE-BATCHING`: Repeated DO writes need coalescing/transaction review; verify backend and rows/units changed before making a cost claim.
- `DO-STUB-CALL-CYCLE`: DO classes call each other's stubs (or their own binding) in a cycle without a per-hop depth/budget guard, idempotency key, or in-loop kill switch.
- `DO-SQL-SCAN-HOTPATH`: `storage.sql.exec` SELECT without WHERE/LIMIT on a request/alarm/loop path; SQLite-backed rows read compound with table growth.
- `DO-FANOUT-TAX`: One request/job fans out to many DO stubs without backpressure or urgency/cost budget.
- `DO-WAITUNTIL-LIFECYCLE`: DO uses background lifecycle work without clear bounded duration, retries, or better Queue/Workflow/Agent fit.
- `KV-VS-DO-STORAGE-FIT`: DO storage used for read-heavy/write-rare data that may fit KV/D1/R2 once consistency/query needs are known.
- `DYNAMIC-WORKER-SANDBOX-CAPABILITIES`: Dynamic Workers execute user/LLM code without explicit egress, binding, secret, limit, and audit posture.
- `AGENT-AUTONOMOUS-LOOP-COST`: Agents SDK loops/tools/schedules lack max steps, cancellation, retry/backoff, idempotency, and cost proxies.
- `ARTIFACTS-UPDATE-SUPPLY-CHAIN`: Artifacts-backed app/firmware update path lacks token scope, signing, rollback, or namespace separation.
- `WORKER-TCP-DB-FIT`: Worker TCP/external DB path lacks Hyperdrive/product-fit review, TLS, pooling, timeouts, or fanout limits.
- `CFDOC-REL-CROSS-BOUNDARY-RPC-DEAD`: Cross-boundary public RPC methods need reachability review; optional deadlint/human review verifies deadness before deletion.
