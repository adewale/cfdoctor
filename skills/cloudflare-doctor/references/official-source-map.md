# Official Cloudflare source map

Use official Cloudflare docs/pricing/limits when making Cloudflare-specific claims. Product limits, quotas, plan entitlements, prices, and best practices are date-sensitive; fetch current docs before quoting numbers or presenting guidance as verified. Start with `https://developers.cloudflare.com/llms.txt`, then fetch the relevant product `llms.txt` and page Markdown. See [`recommendation-provenance.md`](recommendation-provenance.md) for source requirements and [`cloudflare-best-practices-docs.md`](cloudflare-best-practices-docs.md) for the verified best-practices source list.

## Core compute/deploy

- Workers docs: https://developers.cloudflare.com/workers/
- Workers limits: https://developers.cloudflare.com/workers/platform/limits/
- Workers pricing: https://developers.cloudflare.com/workers/platform/pricing/
- Workers CPU profiling: https://developers.cloudflare.com/workers/observability/dev-tools/cpu-usage/
- Workers metrics and analytics: https://developers.cloudflare.com/workers/observability/metrics-and-analytics/
- Wrangler configuration: https://developers.cloudflare.com/workers/wrangler/configuration/
- Workers secrets: https://developers.cloudflare.com/workers/configuration/secrets/
- Compatibility dates: https://developers.cloudflare.com/workers/configuration/compatibility-dates/
- `ExecutionContext.waitUntil`: https://developers.cloudflare.com/workers/runtime-apis/context/#waituntil
- Service bindings: https://developers.cloudflare.com/workers/runtime-apis/bindings/service-bindings/
- Workers RPC overview: https://developers.cloudflare.com/workers/runtime-apis/rpc/
- Workers RPC TypeScript: https://developers.cloudflare.com/workers/runtime-apis/rpc/typescript/
- Workers RPC visibility/security model: https://developers.cloudflare.com/workers/runtime-apis/rpc/visibility/
- Service binding RPC (`WorkerEntrypoint`): https://developers.cloudflare.com/workers/runtime-apis/bindings/service-bindings/rpc/
- Smart Placement: https://developers.cloudflare.com/workers/configuration/smart-placement/
- Pages docs: https://developers.cloudflare.com/pages/
- Pages limits: https://developers.cloudflare.com/pages/platform/limits/
- Pages Functions limits: https://developers.cloudflare.com/pages/platform/limits/
- Pages preview deployments: https://developers.cloudflare.com/pages/configuration/preview-deployments/
- Workers preview URLs: https://developers.cloudflare.com/workers/configuration/previews/
- Workers cron triggers: https://developers.cloudflare.com/workers/configuration/cron-triggers/
- Workers versions and deployments: https://developers.cloudflare.com/workers/configuration/versions-and-deployments/
- Workers rollbacks: https://developers.cloudflare.com/workers/configuration/versions-and-deployments/rollbacks/
- Workers gradual deployments: https://developers.cloudflare.com/workers/configuration/versions-and-deployments/gradual-deployments/
- Dynamic Workers docs: https://developers.cloudflare.com/dynamic-workers/
- Dynamic Workers API reference: https://developers.cloudflare.com/dynamic-workers/api-reference/
- Dynamic Workers egress control: https://developers.cloudflare.com/dynamic-workers/usage/egress-control/
- Dynamic Workers custom limits: https://developers.cloudflare.com/dynamic-workers/usage/limits/
- Dynamic Workers pricing: https://developers.cloudflare.com/dynamic-workers/pricing/
- Artifacts docs: https://developers.cloudflare.com/artifacts/
- Artifacts best practices: https://developers.cloudflare.com/artifacts/concepts/best-practices/
- Artifacts authentication: https://developers.cloudflare.com/artifacts/guides/authentication/
- Artifacts pricing/limits: https://developers.cloudflare.com/artifacts/platform/pricing/ and https://developers.cloudflare.com/artifacts/platform/limits/

## Storage/data primitives

- KV docs: https://developers.cloudflare.com/kv/
- KV consistency/how it works: https://developers.cloudflare.com/kv/concepts/how-kv-works/
- KV limits: https://developers.cloudflare.com/kv/platform/limits/
- KV pricing: https://developers.cloudflare.com/kv/platform/pricing/
- D1 docs: https://developers.cloudflare.com/d1/
- D1 query best practices: https://developers.cloudflare.com/d1/best-practices/query-d1/
- D1 migrations: https://developers.cloudflare.com/d1/reference/migrations/
- D1 limits: https://developers.cloudflare.com/d1/platform/limits/
- D1 pricing: https://developers.cloudflare.com/d1/platform/pricing/
- D1 billing observability: https://developers.cloudflare.com/d1/observability/billing/
- D1 metrics and analytics: https://developers.cloudflare.com/d1/observability/metrics-analytics/
- R2 docs: https://developers.cloudflare.com/r2/
- R2 public buckets: https://developers.cloudflare.com/r2/buckets/public-buckets/
- R2 CORS: https://developers.cloudflare.com/r2/buckets/cors/
- R2 object lifecycles: https://developers.cloudflare.com/r2/buckets/object-lifecycles/
- R2 multipart uploads: https://developers.cloudflare.com/r2/objects/multipart-objects/
- R2 limits: https://developers.cloudflare.com/r2/platform/limits/
- R2 pricing: https://developers.cloudflare.com/r2/pricing/

## Coordination and async

- Durable Objects docs: https://developers.cloudflare.com/durable-objects/
- Durable Object invoke methods/RPC: https://developers.cloudflare.com/durable-objects/best-practices/create-durable-object-stubs-and-send-requests/
- Durable Object migrations: https://developers.cloudflare.com/durable-objects/reference/durable-objects-migrations/
- Durable Object WebSocket hibernation: https://developers.cloudflare.com/durable-objects/best-practices/websockets/
- Durable Object alarms: https://developers.cloudflare.com/durable-objects/api/alarms/
- Durable Object limits: https://developers.cloudflare.com/durable-objects/platform/limits/
- Durable Object pricing: https://developers.cloudflare.com/durable-objects/platform/pricing/
- Durable Object error handling: https://developers.cloudflare.com/durable-objects/best-practices/error-handling/
- Durable Object metrics and analytics: https://developers.cloudflare.com/durable-objects/observability/metrics-and-analytics/
- Queues docs: https://developers.cloudflare.com/queues/
- Queues delivery guarantees: https://developers.cloudflare.com/queues/reference/delivery-guarantees/
- Queues batching/retries: https://developers.cloudflare.com/queues/configuration/batching-retries/
- Queues dead-letter queues: https://developers.cloudflare.com/queues/configuration/dead-letter-queues/
- Queues observability: https://developers.cloudflare.com/queues/observability/
- Queues limits: https://developers.cloudflare.com/queues/platform/limits/
- Queues pricing: https://developers.cloudflare.com/queues/platform/pricing/
- Queues rate-limit tutorial: https://developers.cloudflare.com/queues/tutorials/handle-rate-limits/
- Workflows docs: https://developers.cloudflare.com/workflows/
- Workflows rules: https://developers.cloudflare.com/workflows/build/rules-of-workflows/
- Workflows sleeping and retrying: https://developers.cloudflare.com/workflows/build/sleeping-and-retrying/
- Workflows limits: https://developers.cloudflare.com/workflows/reference/limits/
- Agents SDK docs: https://developers.cloudflare.com/agents/
- Agents long-running agents: https://developers.cloudflare.com/agents/concepts/agentic-patterns/long-running-agents/
- Agents tools/browser/sandbox: https://developers.cloudflare.com/agents/tools/browser/ and https://developers.cloudflare.com/agents/tools/sandbox/
- Agents retries/queue/scheduling/durable execution: https://developers.cloudflare.com/agents/runtime/execution/retries/, https://developers.cloudflare.com/agents/runtime/execution/queue-tasks/, https://developers.cloudflare.com/agents/runtime/execution/schedule-tasks/, https://developers.cloudflare.com/agents/runtime/execution/durable-execution/
- Agents limits/observability: https://developers.cloudflare.com/agents/platform/limits/ and https://developers.cloudflare.com/agents/runtime/operations/observability/
- Workers TCP sockets: https://developers.cloudflare.com/workers/runtime-apis/tcp-sockets/
- Node.js `net` in Workers: https://developers.cloudflare.com/workers/runtime-apis/nodejs/net/
- Hyperdrive docs: https://developers.cloudflare.com/hyperdrive/
- Workers AI docs: https://developers.cloudflare.com/workers-ai/
- Workers AI limits: https://developers.cloudflare.com/workers-ai/platform/limits/
- Workers AI pricing: https://developers.cloudflare.com/workers-ai/platform/pricing/
- Workers AI prompt caching: https://developers.cloudflare.com/workers-ai/features/prompt-caching/
- AI Gateway docs: https://developers.cloudflare.com/ai-gateway/
- AI Gateway caching: https://developers.cloudflare.com/ai-gateway/features/caching/
- AI Gateway rate limiting: https://developers.cloudflare.com/ai-gateway/features/rate-limiting/
- AI Gateway costs: https://developers.cloudflare.com/ai-gateway/observability/costs/
- Vectorize docs: https://developers.cloudflare.com/vectorize/
- Vectorize limits: https://developers.cloudflare.com/vectorize/platform/limits/
- Vectorize pricing: https://developers.cloudflare.com/vectorize/platform/pricing/
- Vectorize create indexes: https://developers.cloudflare.com/vectorize/best-practices/create-indexes/
- Vectorize query vectors: https://developers.cloudflare.com/vectorize/best-practices/query-vectors/

## Cache/CDN/rules/media/browser

- Cache docs: https://developers.cloudflare.com/cache/
- Cache interaction with Cloudflare products: https://developers.cloudflare.com/cache/interaction-cloudflare-products/
- Workers and Cache Rules interaction: https://developers.cloudflare.com/cache/interaction-cloudflare-products/workers-cache-rules/
- R2 and cache interaction: https://developers.cloudflare.com/cache/interaction-cloudflare-products/r2/
- Default cache behavior: https://developers.cloudflare.com/cache/concepts/default-cache-behavior/
- Cache-Control: https://developers.cloudflare.com/cache/concepts/cache-control/
- Cache keys: https://developers.cloudflare.com/cache/how-to/cache-keys/
- Cache Rules: https://developers.cloudflare.com/cache/how-to/cache-rules/
- Purge cache: https://developers.cloudflare.com/cache/how-to/purge-cache/
- Tiered Cache: https://developers.cloudflare.com/cache/how-to/tiered-cache/
- Cache Reserve: https://developers.cloudflare.com/cache/advanced-configuration/cache-reserve/
- Cache Analytics: https://developers.cloudflare.com/cache/performance-review/cache-analytics/
- Cloudflare Rules: https://developers.cloudflare.com/rules/
- Images pricing: https://developers.cloudflare.com/images/pricing/
- Images key concepts / variants: https://developers.cloudflare.com/images/get-started/key-concepts/
- Images transformations overview: https://developers.cloudflare.com/images/optimization/transformations/overview/
- Stream pricing: https://developers.cloudflare.com/stream/pricing/
- Stream Player API: https://developers.cloudflare.com/stream/viewing-videos/using-the-stream-player/using-the-player-api/
- Browser Run docs: https://developers.cloudflare.com/browser-run/
- Browser Run pricing: https://developers.cloudflare.com/browser-run/pricing/
- Browser Run limits: https://developers.cloudflare.com/browser-run/limits/
- Browser Run session management: https://developers.cloudflare.com/browser-run/cdp/session-management/
- Browser Run timeouts: https://developers.cloudflare.com/browser-run/reference/timeouts/
- Browser Run close reasons: https://developers.cloudflare.com/browser-run/reference/browser-close-reasons/

## Security, DNS, Access

- WAF docs: https://developers.cloudflare.com/waf/
- WAF managed rules: https://developers.cloudflare.com/waf/managed-rules/
- WAF custom rules: https://developers.cloudflare.com/waf/custom-rules/
- Rate limiting rules: https://developers.cloudflare.com/waf/rate-limiting-rules/
- WAF security events: https://developers.cloudflare.com/waf/analytics/security-events/
- Turnstile: https://developers.cloudflare.com/turnstile/
- Bot Management / bot products: https://developers.cloudflare.com/bots/
- API Shield: https://developers.cloudflare.com/api-shield/
- API Shield mTLS: https://developers.cloudflare.com/api-shield/security/mtls/
- DNS proxied records: https://developers.cloudflare.com/dns/manage-dns-records/reference/proxied-dns-records/
- DNS TTL: https://developers.cloudflare.com/dns/manage-dns-records/reference/ttl/
- DNSSEC: https://developers.cloudflare.com/dns/dnssec/
- CAA records: https://developers.cloudflare.com/ssl/edge-certificates/caa-records/
- Wildcard DNS records: https://developers.cloudflare.com/dns/manage-dns-records/reference/wildcard-dns-records/
- Authenticated Origin Pulls: https://developers.cloudflare.com/ssl/origin-configuration/authenticated-origin-pull/
- Cloudflare IP/origin protection concepts: https://developers.cloudflare.com/fundamentals/concepts/cloudflare-ip-addresses/
- Access applications: https://developers.cloudflare.com/cloudflare-one/applications/configure-apps/self-hosted-apps/
- Access policies: https://developers.cloudflare.com/cloudflare-one/policies/access/
- Access service tokens: https://developers.cloudflare.com/cloudflare-one/identity/service-tokens/
- Access session management: https://developers.cloudflare.com/cloudflare-one/identity/users/session-management/
- Zero Trust logs: https://developers.cloudflare.com/cloudflare-one/insights/logs/
- Zero Trust plans: https://www.cloudflare.com/plans/zero-trust-services/

## Observability and pricing entry points

- Workers observability: https://developers.cloudflare.com/workers/observability/
- Workers Logs: https://developers.cloudflare.com/workers/observability/logs/workers-logs/
- Workers real-time logs: https://developers.cloudflare.com/workers/observability/logs/real-time-logs/
- Tail Workers: https://developers.cloudflare.com/workers/observability/logs/tail-workers/
- Logpush: https://developers.cloudflare.com/logs/
- Analytics Engine: https://developers.cloudflare.com/analytics/analytics-engine/
- Analytics Engine pricing: https://developers.cloudflare.com/analytics/analytics-engine/pricing/
- Analytics Engine sampling: https://developers.cloudflare.com/analytics/analytics-engine/sampling/
- R2 metrics: https://developers.cloudflare.com/r2/platform/metrics-analytics/
- Cloudflare public plans: https://www.cloudflare.com/plans/
