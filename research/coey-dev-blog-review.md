# coey.dev Cloudflare Doctor review

Date reviewed: 2026-06-04. Method: fetched `https://coey.dev/sitemap.xml`, reviewed the non-`/projects/` and non-`/prompts/` blog URLs, extracted SSR `<main>` content plus client-rendered Durable Object quiz answers from the Svelte chunk. Project pages and prompt-library pages were not treated as blog posts.

Use these notes as scenario discovery, not pricing/limits authority. Pair every Cloudflare-specific recommendation with current official Cloudflare docs.

## Highest-signal additions captured in the skill

- Durable Objects gotchas: duration/WebSockets/hibernation, close hygiene, storage list hot paths, alarm recursion, sharding, ephemeral idempotency objects, storage batching, fanout tax, DO `waitUntil` lifecycle, KV-vs-DO-storage fit.
- Dynamic Workers / Worker Loader: untrusted or LLM-written code needs explicit egress, bindings, secrets, custom limits, stable code identity, audit logs, and nested-spawn caps.
- Cloudflare Agents SDK: long-lived DO-backed agents, schedules, sub-agents, retries, browser/sandbox tools, and streaming need max steps, cancellation, idempotency, and cost proxies.
- Artifacts-backed app/firmware flows: repo-token scope, namespace separation, signed releases, rollback/A-B updates, and cleanup matter.
- Real-time logging: DO/WebSocket/LRU realtime layer plus Analytics Engine/Logpush history needs retention, high-cardinality caps, privacy redaction, and log-volume budget.
- Worker security: OAuth/WebAuthn/webhooks need headers, sanitized errors, timing-safe compares, encrypted token storage, redirect allowlists, signature verification, idempotency, and rate limits.
- Workers TCP/external DB: check Hyperdrive/product fit, TLS, pooling/reuse, regional latency, timeouts, retries, and bounded concurrency.
- Audit-process lessons: prompts are not proof; use executable/adversarial gates, source provenance, run summaries, cost proxies, and externalized state after compaction.

## Post-by-post relevance table

| URL | Date metadata | Cloudflare Doctor relevance |
|---|---:|---|
| https://coey.dev/built-in-reverse | 2026-05-15 | Cloudflare-backed devices use Artifacts repo, Dynamic Worker Loader isolates, per-app DO Facets, signed firmware releases, A/B rollback. Captured as Artifacts/update supply-chain and dynamic sandbox checks. |
| https://coey.dev/worker-loaders | 2026-03-27 | Dynamic Workers as short-lived rooms for untrusted/agent code. Key checks: no inherited network/secrets by accident, explicit bindings/capabilities, limits, nested spawn caps, code hash audit. |
| https://coey.dev/constraint-theory | 2026-03-13 | General agent-constraint note. Low Cloudflare-specific relevance; supports bounded-loop mindset only. |
| https://coey.dev/correctness | none found | Correctness-tool landscape. Low direct Cloudflare relevance; supports recommending stronger verification only when high-risk behavior merits it. |
| https://coey.dev/self | 2026-03-05 | Minimal Cloudflare loop: DO alarm re-enters Worker, Workflow drains KV queue. Captured as async-loop/DO-alarm/workflow claim/idempotency/kill-switch scenario. |
| https://coey.dev/prompts-are-wishes | 2026-03-04 | Gate passed while behavior was broken. Captured as “prompts are not proof”; require executable checks and source-backed findings. |
| https://coey.dev/taste | 2026-03-04 | Design/meta. No direct Cloudflare audit addition. |
| https://coey.dev/liquid-primitives | 2026-06-02 | Stable behavior/tests while runners/implementations change. Supports auditing for tests, contracts, and deployment target over implementation fashion. |
| https://coey.dev/ego-less | 2026-02-28 | Review/craft process. No direct Cloudflare check beyond outcome evaluation. |
| https://coey.dev/compaction | 2026-02-23 | Goals/files survive; conventions/reasoning degrade. Captured as externalized run summaries, docs refreshed, cost proxies, evidence gaps, and not inferring dashboard state after compaction. |
| https://coey.dev/effect-first | 2026-02-23 | Curated, token-efficient guidance outperformed raw source. Supports skill’s reference-map/docs-first workflow. |
| https://coey.dev/cursing-agents | 2026-05-23 | Verification-focused instructions beat hostile/direct prompts in an agent experiment. Captured as adversarial gates and executable checks. |
| https://coey.dev/context-cues | 2026-02-22 | Memory/compaction notes. Supports concise source maps and external state; no new Cloudflare product check. |
| https://coey.dev/deja-research | 2026-02-22 | Agent-memory interface ideation; not evidence. No Cloudflare recommendation beyond treating ideation as hypothesis. |
| https://coey.dev/puzzle | 2026-02-12 | Algorithm essay. No Cloudflare Doctor addition. |
| https://coey.dev/show-me | 2026-02-07 | Dashboard audience framing. Supports outputting both executive risk and engineer evidence/caveats. |
| https://coey.dev/spread | 2026-02-07 | Information propagation essay. Minor relevance to self-replication/loop risk only. |
| https://coey.dev/patience | 2026-02-07 | General constraints/patience essay. No product check. |
| https://coey.dev/campfire | 2026-02-06 | Notes that observation/logs/gates matter; mentions Workers Logs/Analytics Engine. Captured under audit-process and observability checks. |
| https://coey.dev/worms-history | 2026-02-05 | Self-replicating code history. Low direct relevance; reinforces guarding auto-deploy/agent loops and propagation boundaries. |
| https://coey.dev/parley | 2026-02-02 | Two-model planning loop on Cloudflare Workers/SSE/OpenRouter; author notes success/cost not measured. Captured as AI/planning loops need outcome and cost metrics. |
| https://coey.dev/vm-api | 2026-02-01 | Agent steering another agent via API. Mostly off-Cloudflare; supports kill/cancel/status controls for autonomous workers. |
| https://coey.dev/casa-tier-2 | 2025-06-24 | First-hand Cloudflare Worker security controls: security headers, CORS, error sanitization, timing-safe secret compare, AES-GCM token encryption, redirect URI allowlist, KV rate limiting, webhook verification/idempotency. Captured in security checks. |
| https://coey.dev/loop-demo | 2026-01-30 | Auto-heal loop with PAUSED kill switch. Captured as kill-switch/run-summary controls for loops. |
| https://coey.dev/preflight | 2026-01-30 | Slow down before acting; approach log prevents loops. Captured as preflight/evidence inventory before findings. |
| https://coey.dev/gate-review | 2026-01-30 | Red-team tests: ask what bad implementation passes. Captured as adversarial gates for cache/auth/billing paths. |
| https://coey.dev/deja | 2026-01-30 | Cloudflare Workers + D1 + Vectorize memory store; gates initially weak, semantic indexing needs retry. Captured as Vectorize/query/retry and gate-quality note. |
| https://coey.dev/real-time-logging | 2025-09-15 | DO + WebSocket realtime log room, Analytics Engine delayed history, LRU cache to prevent explosion. Captured in logging/observability cost checks. |
| https://coey.dev/userdo | 2025-09-15 | Per-user Durable Objects as data pods. Captured as valid DO fit when ownership/consistency/live-update need is natural, but audit object cardinality/read-heavy fit. |
| https://coey.dev/fleet-pattern | 2025-09-15 | Hierarchical DO manager/agent fan-out. Captured as DO chain/fanout/cascade/backpressure checks. |
| https://coey.dev/promptlog | 2025-10-14 | Dynamic Worker Loader POC for sandboxed code execution with DO history. Captured as dynamic sandbox capability/audit checks. |
| https://coey.dev/bio | 2025-11-21 | WebAuthn auth on Cloudflare. Limited content; supports auth/session review. |
| https://coey.dev/agents-patterns | 2025-11-29 | Agents SDK patterns; Agents are long-lived Durable Objects with state/scheduling/database access. Captured under Agents SDK loop/retry/scheduling/state checks. |
| https://coey.dev/agentcast | 2025-12-08 | Live Chrome session attached to a Cloudflare Agent; open questions about session cost. Captured as Browser Run/session close/timeout/cost-proxy checks. |
| https://coey.dev/edgewire | 2025-12-09 | Node.js TCP libraries in Workers using `cloudflare:sockets`; Hyperdrive not for MSSQL. Captured as Worker TCP/DB product-fit, TLS, pooling, timeout, regional latency checks. |
| https://coey.dev/firestore-agents | 2025-12-16 | Non-Cloudflare Firestore workflow patterns; at-least-once triggers require status/transaction claim. Translated to Queues/Workflows/DO idempotency/claim checks. |
| https://coey.dev/cf-tutorial | 2025-12-16 | Cloudflare quiz categories; broad product inventory reminder. No new check beyond trigger coverage. |
| https://coey.dev/durable-objects-gotchas | 2025-12-22 | Highest-signal DO checklist; captured as named DO checks. Embedded price examples are not authority. |
| https://coey.dev/algorithmic-press | 2025-12-22 | Cloudflare Pages/browser surveillance demo. Captured as privacy/data-minimization/log-retention check for geolocation/device/IP/fingerprinting analytics. |
| https://coey.dev/perfect-do | 2025-12-23 | DO mental models: night watchman/safety deposit box/database row that can think; DO not general DB/cache/blockConcurrencyEverywhere. Captured in DO product-fit rubric. |
| https://coey.dev/effect-taggederror | 2025-12-24 | Explicit error types. Minor relevance: classify expected failures/retries instead of catch-all loops. |
| https://coey.dev/video-to-ascii | 2025-12-25 | Browser-only media processing avoids upload/server work; long clips expose client memory tradeoff. Captured as “do expensive media client-side when safe” consideration, not a Cloudflare-specific check. |
| https://coey.dev/loop | 2026-01-20 | Agent loop with guardrails, progress/errors, PAUSED kill switch, context cost. Captured in loop controls. |
| https://coey.dev/checkout-reality | 2026-01-28 | Playwright DOM success must be paired with backend reality/log checks. Captured as verification of side effects for payments/webhooks and log redaction/retention. |

## Official docs to pair with the new scenarios

- Durable Objects: pricing, limits, WebSocket hibernation, alarms, storage access, rules, metrics/analytics.
- KV/D1/R2: consistency, pricing, query/indexing, object/list/lifecycle docs as fit comparisons.
- Dynamic Workers: loader API, egress control, custom limits, bindings, pricing.
- Agents SDK: long-running agents, retries, scheduled tasks, queue tasks, sub-agents, browser/sandbox tools, limits, observability.
- Artifacts: best practices, authentication, namespaces/repos/tokens, limits/pricing.
- Workers observability/logging: Workers Logs, real-time logs, Tail Workers, Logpush, Analytics Engine sampling/pricing.
- Workers TCP/DB: TCP sockets, Node `net`, Hyperdrive.
- Security: WAF/rate limiting, Turnstile, Access/Zero Trust, Workers secrets, account/domain best practices.
