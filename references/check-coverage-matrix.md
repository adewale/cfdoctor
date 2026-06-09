# Check coverage matrix

This matrix is the single source of truth for how every Cloudflare Doctor check ID is covered. It lists one row for every check ID registered in the static scanner (`scripts/cfdoctor_static_scan.py --list-checks`) and every check ID proposed in the "Checks to add or strengthen" section of [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md), so the gap between proposed and implemented checks stays visible.

`scripts/check_coverage.py` enforces consistency between this matrix and the scanner registry in CI: every registered scanner ID must have exactly one `scanner-lead` row here, and every `scanner-lead` row must exist in the registry. If the scanner registry and this document drift, CI fails.

## Status values

The checker parses the Status column; use these exact spellings:

- `scanner-lead` — a heuristic LEAD exists in the static scanner registry. This is not proof and not full detection: the scanner surfaces candidates for human/skill review, with the confidence recorded in the registry.
- `skill-prompt-only` — covered by SKILL.md/reference guidance (the Notes column says which reference section), but no scanner heuristic exists, usually because the check needs account/dashboard evidence or semantic judgment a regex cannot provide.
- `not-implemented` — proposed (e.g., in the war-story checklist) with no scanner heuristic and no dedicated guidance yet. This is the future-work list.
- `folded-into:<CHECK-ID>` — the ID is a duplicate/alias of a registered scanner check and is intentionally not registered separately; its coverage status is that of the named canonical check.

For `scanner-lead` rows, Pillar and Severity come from `--list-checks`. For checklist-derived rows without a scanner heuristic, Pillar is inferred from the ID prefix and Severity is `—`; the Source/motivation column links the war-story checklist section that motivated the proposal.

## Matrix

| Check ID | Status | Pillar | Severity | Source/motivation | Notes |
| --- | --- | --- | --- | --- | --- |
| AGENT-AUTONOMOUS-LOOP-COST | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §17; proposed in §"Checks to add or strengthen" | Cloudflare Agent loop/tool path lacks obvious bounds or cancellation. |
| ARTIFACTS-UPDATE-SUPPLY-CHAIN | scanner-lead | SEC | low | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) scenario-to-check matrix (Artifacts-backed loaders); proposed in §"Checks to add or strengthen" | Artifacts-backed loader/update path needs token, signing, and rollback review. |
| CFDOC-CONFIG-COMPAT-DATE-FORMAT | scanner-lead | CONFIG | medium | [`config-and-security-checks.md`](config-and-security-checks.md) (Wrangler config hygiene) | compatibility_date is not ISO formatted. |
| CFDOC-CONFIG-COMPAT-DATE-FUTURE | scanner-lead | CONFIG | high | [`config-and-security-checks.md`](config-and-security-checks.md) (Wrangler config hygiene) | compatibility_date is in the future. |
| CFDOC-CONFIG-COMPAT-DATE-OLD | scanner-lead | CONFIG | low | [`config-and-security-checks.md`](config-and-security-checks.md) (Wrangler config hygiene) | compatibility_date is old. |
| CFDOC-CONFIG-D1-NO-MIGRATIONS | scanner-lead | CONFIG | medium | [`config-and-security-checks.md`](config-and-security-checks.md) (bindings/migrations) | D1 binding without local migration files detected. |
| CFDOC-CONFIG-DO-NO-MIGRATIONS | scanner-lead | CONFIG | high | [`config-and-security-checks.md`](config-and-security-checks.md) (bindings/migrations) | Durable Object bindings without migrations in same config scope. |
| CFDOC-CONFIG-ENV-BINDING-PARITY | scanner-lead | CONFIG | low | [`config-and-security-checks.md`](config-and-security-checks.md) (environment parity) | Environment binding parity needs verification. |
| CFDOC-CONFIG-NO-COMPAT-DATE | scanner-lead | CONFIG | medium | [`config-and-security-checks.md`](config-and-security-checks.md) (Wrangler config hygiene) | Missing compatibility_date in Wrangler config. |
| CFDOC-CONFIG-NO-OBSERVABILITY | scanner-lead | CONFIG | low | [`config-and-security-checks.md`](config-and-security-checks.md) (observability) | Wrangler observability not configured in this scope. |
| CFDOC-CONFIG-NODEJS-COMPAT | scanner-lead | CONFIG | low | [`config-and-security-checks.md`](config-and-security-checks.md) (compat flags) | nodejs_compat enabled; confirm it is required. |
| CFDOC-CONFIG-PROCESS-ENV | scanner-lead | CONFIG | low | [`config-and-security-checks.md`](config-and-security-checks.md) (Workers env model) | process.env reference in Worker-adjacent code. |
| CFDOC-CONFIG-UNPARSEABLE | scanner-lead | CONFIG | medium | [`config-and-security-checks.md`](config-and-security-checks.md) (Wrangler config hygiene) | Could not parse Wrangler config and no compatibility_date text found. |
| CFDOC-COST-AI-NO-IDEMPOTENCY | scanner-lead | COST | medium | [`cost-footguns.md`](cost-footguns.md) (AI idempotency/anti-rework) | Workers AI call lacks obvious idempotency/cache or is inside retry/loop-shaped code. |
| CFDOC-COST-ASYNC-LOOP | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §1, §6, §15; proposed in §"Checks to add or strengthen" | Scanner heuristic covers the self-fetch shape only; generic retry-without-backoff is tracked separately as CFDOC-COST-RETRY-AMPLIFY. |
| CFDOC-COST-BROAD-ROUTE | scanner-lead | COST | medium | [`config-and-security-checks.md`](config-and-security-checks.md) (routes); [`cost-footguns.md`](cost-footguns.md) | Broad Worker route should be verified. |
| CFDOC-COST-BROWSER-NO-CLOSE | scanner-lead | COST | high | [`cost-footguns.md`](cost-footguns.md) (Browser Run); [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §17 | Browser Run session is opened without an obvious close path. |
| CFDOC-COST-CRON-EVERY-MINUTE | scanner-lead | COST | medium | [`cost-footguns.md`](cost-footguns.md) (background job volume) | Cron trigger runs every minute. |
| CFDOC-COST-D1-ORDER-RANDOM | scanner-lead | COST | high | [`cost-footguns.md`](cost-footguns.md) (D1 rows-read meter) | D1 query orders by RANDOM(). |
| CFDOC-COST-DO-FRONT-DOOR | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §14; [`cost-footguns.md`](cost-footguns.md) (DO request/duration meters) | Durable Object call path lacks obvious front-door validation. |
| CFDOC-COST-DO-UNBATCHED-WRITES | folded-into:DO-STORAGE-BATCHING | COST | — | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §"Checks to add or strengthen" (§1, §14) | Duplicate/alias of DO-STORAGE-BATCHING; intentionally not registered as a separate scanner ID. |
| CFDOC-COST-DYNAMIC-WORKER-DEDUPE | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §16; [`cost-footguns.md`](cost-footguns.md) | Dynamic Worker load path lacks obvious stable ID/dedupe. |
| CFDOC-COST-KV-LIST-HOTPATH | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §1; proposed in §"Checks to add or strengthen" | KV list operation appears in application code. |
| CFDOC-COST-LOG-VOLUME | skill-prompt-only | COST | — | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §12; proposed in §"Checks to add or strengthen" | Covered by [`cost-footguns.md`](cost-footguns.md) "Logging as a meter" guidance and war-story §12; needs Logpush/Analytics Engine dashboard evidence a repo regex cannot see. |
| CFDOC-COST-MEDIA-VARIANT-EXPLOSION | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §4; proposed in §"Checks to add or strengthen" | Emitted by two scanner heuristics: image transform variants and Stream preload. |
| CFDOC-COST-ORIGIN-BYPASS | skill-prompt-only | COST | — | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §5, §11; proposed in §"Checks to add or strengthen" | Covered by [`config-and-security-checks.md`](config-and-security-checks.md) DNS/origin-exposure checks and [`cost-footguns.md`](cost-footguns.md); needs DNS proxy status, R2 public-bucket, and origin-firewall account evidence. |
| CFDOC-COST-PAGES-FUNCTION-ROUTES | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §3; [`cost-footguns.md`](cost-footguns.md) | Pages _routes.json broadly invokes Functions without obvious static exclusions. |
| CFDOC-COST-PREVIEW-PUBLIC-PAID | skill-prompt-only | COST | — | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §13; proposed in §"Checks to add or strengthen" | Covered by [`config-and-security-checks.md`](config-and-security-checks.md) preview/temporary-environment checks; public/indexed status and TTL cleanup need dashboard evidence. Repo-visible paid bindings in preview envs are caught by CFDOC-COST-TEMP-ENV-PAID-BINDINGS. |
| CFDOC-COST-R2-LIST-HOTPATH | scanner-lead | COST | medium | [`cost-footguns.md`](cost-footguns.md) (R2 operation meters) | R2 bucket list appears in application code. |
| CFDOC-COST-RETRY-AMPLIFY | scanner-lead | COST | medium | [`cost-footguns.md`](cost-footguns.md) (retry storms); [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §1 | Covers generic retry-without-backoff/circuit-breaker; distinct from the self-fetch-only CFDOC-COST-ASYNC-LOOP. |
| CFDOC-COST-SPEND-ALERTS-ONLY | skill-prompt-only | COST | — | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §9; proposed in §"Checks to add or strengthen" | Covered by [`performance-and-reliability.md`](performance-and-reliability.md) "Resilience controls" (kill switches, circuit breakers) and [`cost-footguns.md`](cost-footguns.md); whether alerts are the only control is account-level semantic judgment. |
| CFDOC-COST-TEMP-ENV-PAID-BINDINGS | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §7, §13; proposed in §"Checks to add or strengthen" | Temporary/preview environment is connected to paid or stateful Cloudflare services. |
| CFDOC-COST-THIRD-PARTY-ORIGIN | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §10; proposed in §"Checks to add or strengthen" | Worker fetches a public third-party/serverless origin hostname. |
| CFDOC-COST-UNBOUNDED-FANOUT | scanner-lead | COST | medium | [`cost-footguns.md`](cost-footguns.md) (bounded fanout) | Promise.all map fanout lacks an obvious concurrency cap. |
| CFDOC-COST-VECTORIZE-DIMENSIONS | scanner-lead | COST | medium | [`cost-footguns.md`](cost-footguns.md) (Vectorize meters) | Vectorize query path should account for queried dimensions and fan-out. |
| CFDOC-COST-WEBHOOK-NO-IDEMPOTENCY | skill-prompt-only | COST | — | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §2, §19; proposed in §"Checks to add or strengthen" | Covered by [`cost-footguns.md`](cost-footguns.md) idempotency/anti-rework guidance and war-story §2/§19; "side effects before signature verification" ordering needs semantic judgment a regex cannot provide. |
| CFDOC-FIT-KV-COORDINATION | scanner-lead | FIT | high | [`product-fit-rubric.md`](product-fit-rubric.md) (KV consistency limits) | KV read-modify-write smell for coordination/counters. |
| CFDOC-PERF-AWAITED-CACHE-PUT | scanner-lead | PERF | low | [`performance-and-reliability.md`](performance-and-reliability.md) | Cache put awaited in request path. |
| CFDOC-PERF-D1-N-PLUS-ONE | scanner-lead | PERF | low | [`performance-and-reliability.md`](performance-and-reliability.md) | Many D1 prepared statements in one file; check for N+1 queries. |
| CFDOC-PERF-D1-SELECT-STAR | scanner-lead | PERF | medium | [`performance-and-reliability.md`](performance-and-reliability.md) | D1 query uses SELECT *. |
| CFDOC-PERF-PUBLIC-SERVICE-URL | scanner-lead | PERF | medium | [`performance-and-reliability.md`](performance-and-reliability.md) (service bindings) | Public Cloudflare service URL fetch; consider service bindings. |
| CFDOC-PERF-R2-BUFFERING | scanner-lead | PERF | medium | [`performance-and-reliability.md`](performance-and-reliability.md) (streaming) | R2 object may be buffered instead of streamed. |
| CFDOC-REL-QUEUE-NO-DLQ | scanner-lead | REL | medium | [`performance-and-reliability.md`](performance-and-reliability.md); [`cost-footguns.md`](cost-footguns.md) (retry storms) | Queue consumer lacks explicit retry or dead-letter configuration. |
| CFDOC-SEC-CORS-WILDCARD-CREDS | scanner-lead | SEC | high | [`config-and-security-checks.md`](config-and-security-checks.md) (CORS) | Wildcard CORS appears near credentialed responses. |
| CFDOC-SEC-DNS-UNPROXIED | scanner-lead | SEC | medium | [`config-and-security-checks.md`](config-and-security-checks.md) (DNS/origin exposure) | Terraform has unproxied DNS record; verify origin exposure. |
| CFDOC-SEC-SECRET-ASSIGNMENT | scanner-lead | SEC | high | [`config-and-security-checks.md`](config-and-security-checks.md) (secret handling) | Credential-like assignment appears in repository text. |
| CFDOC-SEC-SECRET-IN-CONFIG | scanner-lead | SEC | high | [`config-and-security-checks.md`](config-and-security-checks.md) (secret handling) | Possible secret stored in Wrangler vars. |
| CFDOC-SEC-SECRET-VALUE | scanner-lead | SEC | critical | [`config-and-security-checks.md`](config-and-security-checks.md) (secret handling) | Credential-shaped value appears in repository text. |
| CFDOC-SEC-SPOOFABLE-IP-HEADER | scanner-lead | SEC | medium | [`config-and-security-checks.md`](config-and-security-checks.md) (ingress trust) | Code reads spoofable client-IP header. |
| CFDOC-SEC-TLS-FLEXIBLE | scanner-lead | SEC | high | [`config-and-security-checks.md`](config-and-security-checks.md) (SSL/TLS mode) | Terraform sets SSL/TLS mode to Flexible. |
| DO-ALARM-RECURSION | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §14, §15; proposed in §"Checks to add or strengthen" | Alarm handler reschedules without obvious idle guard. |
| DO-EPHEMERAL-IDEMPOTENCY-OBJECTS | scanner-lead | FIT | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §14; proposed in §"Checks to add or strengthen" | Durable Object key appears tied to an ephemeral id/request. |
| DO-FANOUT-TAX | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §14; proposed in §"Checks to add or strengthen" | Fan-out to Durable Objects lacks obvious backpressure. |
| DO-SHARDING-HOTSPOT | scanner-lead | COST | high | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §14; proposed in §"Checks to add or strengthen" | Durable Object idFromName uses a global/singleton key. |
| DO-SOCKET-CLOSE-HYGIENE | scanner-lead | REL | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §14; proposed in §"Checks to add or strengthen" | WebSocket path lacks obvious close/error cleanup. |
| DO-STORAGE-BATCHING | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §14; proposed in §"Checks to add or strengthen" | Canonical ID for unbatched DO writes; the checklist's CFDOC-COST-DO-UNBATCHED-WRITES is a duplicate folded into this check. |
| DO-STORAGE-LIST-HOTPATH | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §14; proposed in §"Checks to add or strengthen" | Durable Object storage.list appears in code. |
| DO-WAITUNTIL-LIFECYCLE | scanner-lead | REL | low | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §14; proposed in §"Checks to add or strengthen" | Durable Object background work should be bounded and API-correct. |
| DO-WEBSOCKET-DURATION | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §14; proposed in §"Checks to add or strengthen" | WebSocket handling may not use Durable Object hibernation. |
| DYNAMIC-WORKER-SANDBOX-CAPABILITIES | scanner-lead | SEC | high | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §16; proposed in §"Checks to add or strengthen" | Dynamic Worker/code execution lacks obvious capability or resource bounds. |
| KV-VS-DO-STORAGE-FIT | scanner-lead | FIT | low | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §14; proposed in §"Checks to add or strengthen" | Durable Object storage used for possibly read-heavy data. |
| WORKER-TCP-DB-FIT | scanner-lead | REL | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §20; proposed in §"Checks to add or strengthen" | Worker TCP/external database path lacks obvious pooling/TLS/timeout controls. |

## How to update

- Adding a check to the scanner registry requires adding a `scanner-lead` row to this table in the same change; `scripts/check_coverage.py` fails CI otherwise.
- Removing or renaming a scanner check requires updating its row here (rename, or change the status to `skill-prompt-only`/`not-implemented` if the heuristic is dropped but the check idea remains).
- Proposing a new check in the war-story checklist requires a `not-implemented` (or `skill-prompt-only`, if reference guidance already covers it) row here.
- Run `python3 scripts/check_coverage.py` locally to verify before pushing; it exits 0 when the matrix and registry are consistent.

## Known false-negative leads (found while building detection fixtures, 2026-06-09)

Realistic code shapes the current heuristics miss. These are scanner
improvement leads, not reasons to trust a quiet scan:

- `DO-SHARDING-HOTSPOT` only matches literal singleton strings in
  `idFromName("global"|"singleton"|...)`; hotspots via variables or
  constants (`idFromName(env.REGION)`) are invisible.
- `CFDOC-REL-QUEUE-NO-DLQ` is config-only; consumers defined solely in the
  dashboard are out of static reach (expected, but worth stating).
- `CFDOC-COST-ASYNC-LOOP` catches `fetch(request.url)` / `fetch(request.clone())`
  but not the common `fetch(new URL(path, request.url))` self-fetch shape.
- `DO-ALARM-RECURSION` is suppressed by any `if (` near the `alarm()` body, so
  an unconditional reschedule containing an unrelated guard is missed.
- `CFDOC-COST-MEDIA-VARIANT-EXPLOSION`'s Stream arm requires the Stream
  hostname and `preload="auto"` in the same file; config-imported URLs evade it.
