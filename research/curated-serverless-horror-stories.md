# Curated serverless horror-story sources

This is the parent-agent research pass. A separate subagent research run may add more examples in `research/serverless-horror-stories.md`.

Link status last verified: 2026-06-09 (scripts/check_links.py; report in evals/results/).

## Cloudflare

### RetainDB / Cloudflare KV + Durable Objects + Queues runaway bill

- Source aggregator: https://serverlesshorrors.com/all/cloudflare-36k
- Linked original: https://www.reddit.com/r/CloudFlare/comments/1t1e8nh/i_accidentally_generated_16_billion_durable/ (archived: https://web.archive.org/web/20260506025828/https://www.reddit.com/r/CloudFlare/comments/1t1e8nh/i_accidentally_generated_16_billion_durable/)
- Type: war story / first-hand linked via aggregator; verify original before external publishing.
- Claimed mechanism: infinite Queue loop, unbatched Durable Object storage writes, and KV `list()` scans on auth requests produced billions of operations.
- Scenarios to check: recursive async work, idempotency/dedupe, DLQ/retry caps, DO write batching, KV list hot paths, per-run cost proxies.

## Vercel

### Stripe webhook DoS caused large Vercel bill

- Source: Convoy blog, “Stripe webhooks DoS caused $23k Vercel bills,” 2024-02-15, https://getconvoy.io/blog/stripe-webhook-delivery-failure
- Related aggregator: https://serverlesshorrors.com/all/vercel-23k
- Type: first-party blog / war story.
- Mechanism: mass account/trial creation triggered large webhook volume and serverless invocations.
- Scenarios to check: webhook signature verification before expensive work, idempotency by event ID, rate limiting/account creation abuse controls, bounded async work.

### LLM bots and Vercel Image API pricing

- Source: Metacast engineering postmortem, “The Cost of Being Crawled: LLM Bots and Vercel Image API Pricing,” https://metacast.app/blog/engineering/postmortem-llm-bots-image-optimization (archived: https://web.archive.org/web/20260304063157/https://metacast.app/blog/engineering/postmortem-llm-bots-image-optimization)
- HN discussion: https://news.ycombinator.com/item?id=43687431
- Type: first-hand engineering postmortem.
- Mechanism: crawlers/bots request image optimization URLs and trigger metered image transformations.
- Scenarios to check: bounded image variants, normalized cache keys, bot controls before paid transforms, top transformed URLs.

## Netlify

### $104k static-site bandwidth bill after abnormal traffic

- Forum follow-up: https://answers.netlify.com/t/i-am-the-op-of-that-104k-bill-post-and-i-have-some-follow-up-questions/113472
- Original Reddit post: https://old.reddit.com/r/webdev/comments/1b14bty/netlify_just_sent_me_a_104k_bill_for_a_simple/ (archived: https://web.archive.org/web/20250908035924/https://old.reddit.com/r/webdev/comments/1b14bty/netlify_just_sent_me_a_104k_bill_for_a_simple/)
- Aggregator: https://serverlesshorrors.com/all/netlify-104k
- Type: first-hand forum/reddit + aggregator.
- Mechanism: abnormal traffic / likely DDoS consumed massive bandwidth on a static site.
- Scenarios to check: WAF/rate limiting/bot controls, cache hit ratio, static routes not proxied through paid compute, plan overage behavior, usage alerts.

## Firebase / GCP

### Firebase reads/usage surprise bills

- Medium article: “How not to get a $30k bill from Firebase,” https://medium.com/@PurpleGreenLemon/how-not-to-get-a-30k-bill-from-firebase-37a6cb3abaca (archived: https://web.archive.org/web/20200429160249/https://medium.com/@PurpleGreenLemon/how-not-to-get-a-30k-bill-from-firebase-37a6cb3abaca) (access may be restricted)
- HN discussion: https://news.ycombinator.com/item?id=17661391
- Official Firebase docs: “Avoid surprise bills,” https://firebase.google.com/docs/projects/billing/avoid-surprise-bills
- Official GCP budgets: https://cloud.google.com/billing/docs/how-to/budgets
- Type: war story + official docs.
- Mechanism: per-read/per-operation billing and lack of cost guardrails.
- Scenarios to check: D1 rows read, KV/R2 ops, query loops, public object hot paths, budgets/alerts plus product-level controls.

### Firebase/Cloud Storage direct-origin abuse

- Aggregator: https://serverlesshorrors.com/all/firebase-100k
- Type: war story aggregator linked to Reddit.
- Mechanism: attacker found uncached object and direct origin bucket; Cloudflare in front did not protect direct bucket access.
- Scenarios to check: R2/origin direct bypass, public bucket/custom domain settings, WAF/cache coverage, signed URLs/auth, origin restrictions.

## AWS

### Recursive Lambda/serverless invocation risk

- Official AWS docs: Lambda recursive loop detection, https://docs.aws.amazon.com/lambda/latest/dg/invocation-recursion.html
- AWS Budgets: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html
- AWS Cost Anomaly Detection: https://docs.aws.amazon.com/cost-management/latest/userguide/getting-started-ad.html
- Type: official docs.
- Mechanism: function writes to an event source that invokes the function again; retries and event sources amplify compute.
- Scenarios to check: Queue/Workflow/Cron recursive triggers, max depth, idempotency, kill switches, DLQs, anomaly detection.

## Railway

### Usage-based resources and idle services

- Official plans/pricing: https://docs.railway.com/pricing/plans.md
- Understanding your bill: https://docs.railway.com/pricing/understanding-your-bill.md
- Cost control: https://docs.railway.com/pricing/cost-control.md
- Serverless mode: https://docs.railway.com/deployments/serverless.md
- Type: official docs.
- Mechanism: users pay for consumed CPU/memory/egress/resources; services may be billable while idle unless serverless/cost controls are configured.
- Scenarios to check: temporary envs, idle paid resources, serverless/scale-to-zero settings, usage caps, cost dashboard review.

## Heroku

### Accidental Heroku bill / idle dynos and add-ons

- HN war story: “Tell HN: I accidentally ran up a $1000 Heroku bill,” https://news.ycombinator.com/item?id=1688904
- Heroku usage and billing docs: https://devcenter.heroku.com/articles/usage-and-billing
- Heroku limits: https://devcenter.heroku.com/articles/limits
- Type: war story + official docs.
- Mechanism: resources/add-ons/dynos can keep billing outside intended usage.
- Scenarios to check: preview/demo envs, crons, live services, add-on equivalents, paid bindings in non-production.

## Azure

### Consumption-based function costs and budgets

- Azure Functions consumption costs: https://learn.microsoft.com/en-us/azure/azure-functions/functions-consumption-costs
- Azure budgets: https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-acm-create-budgets
- Azure Functions best practices: https://learn.microsoft.com/en-us/azure/azure-functions/functions-best-practices
- Type: official docs.
- Mechanism: functions cost depends on executions, memory/duration, and dependencies, not just requests; budgets/alerts are needed.
- Scenarios to check: Workers CPU/subrequests, retry amplification, logs/analytics volume, product-level kill switches.

## Cross-story lessons

- Bills blow up from multiplication factors: retries × fanout × per-operation meters × missing cache × attack traffic.
- Alerts are not controls. Rate limits, idempotency, kill switches, DLQs, and cache keys must exist before the meter.
- Repo config is insufficient: dashboards, billing pages, usage analytics, and provider APIs are necessary to confirm live risk.
- Every finding should include a source basis, evidence source, and confidence; war stories motivate scenario checks but official docs establish current product behavior.
