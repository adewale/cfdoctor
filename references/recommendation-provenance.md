# Recommendation provenance requirements

Every Cloudflare Doctor recommendation must be source-backed. The skill may use local repo/config evidence to prove the project has a problem, but the recommendation itself needs a source basis.

## Hard rule

For every confirmed finding and recommended action, include a `Source basis` field with at least one of:

1. **Official current Cloudflare source** — docs, pricing, limits, best-practices docs, API reference, changelog, or Cloudflare dashboard/API evidence fetched during the audit.
2. **War story** — a public, dated, first-hand incident report, engineering postmortem, maintainer issue, or operator write-up where someone used the wrong primitive/configuration, hit the failure/cost/security issue, and documented the lesson.

If neither exists, do not present the item as a recommendation. Put it under **Questions / evidence needed** or label it as an **unsourced hypothesis**.

## Source hierarchy

- **Pricing, limits, plan behavior, billing meters**: official current Cloudflare docs/pricing only. War stories can motivate severity but cannot establish current price/limit facts.
- **Product behavior and configuration semantics**: official current Cloudflare docs first. War stories can supplement practical risk.
- **Operational patterns** such as circuit breakers, kill switches, anti-rework caches, and bounded fanout: cite the closest official Cloudflare primitive docs for the concrete mechanism being recommended (Queues retries/DLQ, Workflows retries, AI Gateway rate limiting/caching, Workers rollbacks, etc.) or cite a war story.
- **Security findings**: official docs or well-documented first-hand incident/write-up; avoid anonymous lore.

## War story acceptance criteria

A war story is acceptable only if it has:

- URL and author/org.
- Date or approximate date.
- First-hand operational context (not a generic SEO/blog summary).
- Mistake → consequence → lesson/fix chain.
- Clear mapping from that lesson to the audited Cloudflare project.

Output format:

```markdown
- Source basis: War story — <title>, <org/author>, <date>, <URL>; lesson: <one sentence>; maps because <project evidence>
```

## Finding output requirement

Add this line to every finding:

```markdown
- Source basis: <Official Cloudflare docs URL(s) fetched this audit and/or accepted war story URL(s)>
```

If the finding includes both product facts and operational advice, include both kinds of source when needed.

## Official source map by recommendation family

Use these as starting points, then fetch the current Markdown pages at audit time via `llms.txt` or `Accept: text/markdown`.

### Current docs discovery

- Cloudflare docs directory: https://developers.cloudflare.com/llms.txt
- Product-specific `llms.txt`: `https://developers.cloudflare.com/<product>/llms.txt`
- Verified best-practices list in this skill: [`cloudflare-best-practices-docs.md`](cloudflare-best-practices-docs.md)
- General source map: [`official-source-map.md`](official-source-map.md)

### Workers cost is not just request count

- Workers pricing: https://developers.cloudflare.com/workers/platform/pricing/
- Workers limits: https://developers.cloudflare.com/workers/platform/limits/
- Workers CPU profiling: https://developers.cloudflare.com/workers/observability/dev-tools/cpu-usage/
- Workers metrics/analytics: https://developers.cloudflare.com/workers/observability/metrics-and-analytics/

### Free-to-Paid plan changes and overage risk

- Workers pricing: https://developers.cloudflare.com/workers/platform/pricing/
- Product pricing pages for each detected binding: D1, R2, KV, Durable Objects, Queues, Workers AI, Vectorize, Images, Stream, Browser Run.
- Cloudflare public plans: https://www.cloudflare.com/plans/

### D1 rows read, full scans, N+1, indexes

- D1 pricing: https://developers.cloudflare.com/d1/platform/pricing/
- D1 query best practices: https://developers.cloudflare.com/d1/best-practices/query-d1/
- D1 use indexes: https://developers.cloudflare.com/d1/best-practices/use-indexes/
- D1 billing observability: https://developers.cloudflare.com/d1/observability/billing/
- D1 metrics/analytics: https://developers.cloudflare.com/d1/observability/metrics-analytics/

### Durable Objects validation, hot shards, hibernation, and errors

- Durable Objects rules/best practices: https://developers.cloudflare.com/durable-objects/best-practices/rules-of-durable-objects/
- Durable Objects WebSocket hibernation: https://developers.cloudflare.com/durable-objects/best-practices/websockets/
- Durable Objects error handling: https://developers.cloudflare.com/durable-objects/best-practices/error-handling/
- Durable Objects limits: https://developers.cloudflare.com/durable-objects/platform/limits/
- Durable Objects pricing: https://developers.cloudflare.com/durable-objects/platform/pricing/
- Durable Objects metrics/analytics: https://developers.cloudflare.com/durable-objects/observability/metrics-and-analytics/

### Queues, hot retries, DLQs, poison messages, and rate limits

- Queues delivery guarantees: https://developers.cloudflare.com/queues/configuration/delivery-guarantees/
- Queues batching/retries: https://developers.cloudflare.com/queues/configuration/batching-retries/
- Queues dead-letter queues: https://developers.cloudflare.com/queues/configuration/dead-letter-queues/
- Queues metrics: https://developers.cloudflare.com/queues/observability/metrics/
- Queues pricing: https://developers.cloudflare.com/queues/platform/pricing/
- Queues tutorial for rate limits: https://developers.cloudflare.com/queues/tutorials/handle-rate-limits/

### Idempotency, anti-rework caching, retries, and Workflows

- Workflows rules: https://developers.cloudflare.com/workflows/build/rules-of-workflows/
- Workflows sleeping/retrying: https://developers.cloudflare.com/workflows/build/sleeping-and-retrying/
- Workflows limits: https://developers.cloudflare.com/workflows/reference/limits/
- D1 retry queries: https://developers.cloudflare.com/d1/best-practices/retry-queries/
- Queues delivery/retry/DLQ docs above.
- AI Gateway caching: https://developers.cloudflare.com/ai-gateway/features/caching/
- AI Gateway rate limiting: https://developers.cloudflare.com/ai-gateway/features/rate-limiting/

### Workers AI loops, duplicate generation, and cost controls

- Workers AI pricing: https://developers.cloudflare.com/workers-ai/platform/pricing/
- Workers AI limits: https://developers.cloudflare.com/workers-ai/platform/limits/
- Workers AI prompt caching: https://developers.cloudflare.com/workers-ai/features/prompt-caching/
- AI Gateway caching: https://developers.cloudflare.com/ai-gateway/features/caching/
- AI Gateway costs: https://developers.cloudflare.com/ai-gateway/observability/costs/
- AI Gateway rate limiting: https://developers.cloudflare.com/ai-gateway/features/rate-limiting/

### Vectorize dimensions, fanout, and query economics

- Vectorize pricing: https://developers.cloudflare.com/vectorize/platform/pricing/
- Vectorize limits: https://developers.cloudflare.com/vectorize/platform/limits/
- Vectorize create indexes: https://developers.cloudflare.com/vectorize/best-practices/create-indexes/
- Vectorize query vectors: https://developers.cloudflare.com/vectorize/best-practices/query-vectors/

### R2 “no egress fees” is not “no bill”

- R2 pricing: https://developers.cloudflare.com/r2/pricing/
- R2 limits: https://developers.cloudflare.com/r2/platform/limits/
- R2 object lifecycles: https://developers.cloudflare.com/r2/buckets/object-lifecycles/
- Cache + R2 interaction: https://developers.cloudflare.com/cache/interaction-cloudflare-products/r2/

### Images transformations and variants

- Images pricing: https://developers.cloudflare.com/images/pricing/
- Images key concepts / variants: https://developers.cloudflare.com/images/get-started/key-concepts/
- Images limits/formats: https://developers.cloudflare.com/images/get-started/limits/
- Image transformations overview: https://developers.cloudflare.com/images/optimization/transformations/overview/
- Transform via Workers: https://developers.cloudflare.com/images/optimization/transformations/transform-via-workers/

### Stream delivered minutes and preload/buffering

- Stream pricing: https://developers.cloudflare.com/stream/pricing/
- Stream Player API: https://developers.cloudflare.com/stream/viewing-videos/using-the-stream-player/using-the-player-api/
- Stream analytics: https://developers.cloudflare.com/stream/getting-analytics/

### Browser Run sessions and retries

- Browser Run pricing: https://developers.cloudflare.com/browser-run/pricing/
- Browser Run limits: https://developers.cloudflare.com/browser-run/limits/
- Browser Run session management: https://developers.cloudflare.com/browser-run/cdp/session-management/
- Browser Run timeouts: https://developers.cloudflare.com/browser-run/reference/timeouts/
- Browser Run close reasons: https://developers.cloudflare.com/browser-run/reference/browser-close-reasons/

### Preview, demo, workshop, cron, and temporary deployments

- Pages preview deployments: https://developers.cloudflare.com/pages/configuration/preview-deployments/
- Workers preview URLs: https://developers.cloudflare.com/workers/configuration/previews/
- Workers cron triggers: https://developers.cloudflare.com/workers/configuration/cron-triggers/
- Workers versions/deployments: https://developers.cloudflare.com/workers/configuration/versions-and-deployments/
- Workers rollbacks: https://developers.cloudflare.com/workers/configuration/versions-and-deployments/rollbacks/
- Gradual deployments: https://developers.cloudflare.com/workers/configuration/versions-and-deployments/gradual-deployments/

### Circuit breakers, kill switches, bounded fanout, and run summaries

Official Cloudflare docs rarely use all of these generic architecture terms directly. Anchor recommendations to concrete Cloudflare mechanisms and/or war stories:

- Workers rollbacks: https://developers.cloudflare.com/workers/configuration/versions-and-deployments/rollbacks/
- Gradual deployments: https://developers.cloudflare.com/workers/configuration/versions-and-deployments/gradual-deployments/
- Workers observability: https://developers.cloudflare.com/workers/observability/
- Workers traces/spans: https://developers.cloudflare.com/workers/observability/traces/spans-and-attributes/
- AI Gateway rate limiting: https://developers.cloudflare.com/ai-gateway/features/rate-limiting/
- AI Gateway analytics/costs: https://developers.cloudflare.com/ai-gateway/observability/costs/
- Queues retries/DLQ/rate-limit docs above.
- Workflows retry/limits docs above.

If recommending a specific circuit-breaker or kill-switch pattern beyond these docs, include an accepted war story source.

### Layered caching across Cloudflare primitives

- Cache docs: https://developers.cloudflare.com/cache/
- Cache interaction with Cloudflare products: https://developers.cloudflare.com/cache/interaction-cloudflare-products/
- Workers + Cache Rules interaction: https://developers.cloudflare.com/cache/interaction-cloudflare-products/workers-cache-rules/
- Workers Cache API: https://developers.cloudflare.com/workers/runtime-apis/cache/
- How Workers cache works: https://developers.cloudflare.com/workers/reference/how-the-cache-works/
- Cache-Control: https://developers.cloudflare.com/cache/concepts/cache-control/
- Cache keys: https://developers.cloudflare.com/cache/how-to/cache-keys/
- Cache purge: https://developers.cloudflare.com/cache/how-to/purge-cache/
- KV how it works: https://developers.cloudflare.com/kv/concepts/how-kv-works/
- AI Gateway caching: https://developers.cloudflare.com/ai-gateway/features/caching/

## Audit-time source checklist

Before final answer:

- [ ] Every finding has `Source basis`.
- [ ] Every pricing/limit claim uses current official Cloudflare docs.
- [ ] Every generic ops recommendation has either a concrete Cloudflare mechanism source or an accepted war story.
- [ ] War stories include URL/date/lesson/mapping.
- [ ] Unsourced ideas are moved to `Questions / evidence needed` or explicitly labelled hypotheses.
