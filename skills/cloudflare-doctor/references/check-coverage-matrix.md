# Check coverage matrix

This matrix is the single source of truth for how every Cloudflare Doctor check ID is covered. It lists one row for every check ID registered in the static scanner (`skills/cloudflare-doctor/scripts/cfdoctor_static_scan.py --list-checks`) and every check ID proposed in the "Checks to add or strengthen" section of [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md), so the gap between proposed and implemented checks stays visible.

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
| CFDOC-CONFIG-DO-NEW-KV-RESTRICTED | skill-prompt-only | CONFIG | — | [`config-and-security-checks.md`](config-and-security-checks.md) (bindings/migrations); current DO migration docs | New `new_classes` may fail for accounts without an existing KV-backed namespace; account/deployment history is required because applied migrations must not be rewritten. |
| CFDOC-CONFIG-ENV-BINDING-PARITY | scanner-lead | CONFIG | low | [`config-and-security-checks.md`](config-and-security-checks.md) (environment parity) | Environment binding parity needs verification. |
| CFDOC-CONFIG-NO-COMPAT-DATE | scanner-lead | CONFIG | medium | [`config-and-security-checks.md`](config-and-security-checks.md) (Wrangler config hygiene) | Missing compatibility_date in Wrangler config. |
| CFDOC-CONFIG-NO-OBSERVABILITY | scanner-lead | CONFIG | low | [`config-and-security-checks.md`](config-and-security-checks.md) (observability) | Wrangler observability not configured in this scope. |
| CFDOC-CONFIG-NODEJS-COMPAT | scanner-lead | CONFIG | low | [`config-and-security-checks.md`](config-and-security-checks.md) (compat flags) | nodejs_compat enabled; confirm it is required. |
| CFDOC-CONFIG-PROCESS-ENV | scanner-lead | CONFIG | low | [`config-and-security-checks.md`](config-and-security-checks.md) (Workers env model) | process.env reference in Worker-adjacent code. |
| CFDOC-CONFIG-UNPARSEABLE | scanner-lead | CONFIG | medium | [`config-and-security-checks.md`](config-and-security-checks.md) (Wrangler config hygiene) | Parse failure is always surfaced with diagnostics; valid JSONC comments/trailing commas and valid empty configs are distinct from failure. |
| CFDOC-COST-AI-NO-IDEMPOTENCY | scanner-lead | COST | medium | [`cost-footguns.md`](cost-footguns.md) (AI idempotency/anti-rework) | Workers AI call lacks obvious idempotency/cache or is inside retry/loop-shaped code. |
| CFDOC-COST-ASYNC-LOOP | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §1, §6, §15; proposed in §"Checks to add or strengthen" | Scanner heuristic covers the self-fetch shape only; generic retry-without-backoff is tracked separately as CFDOC-COST-RETRY-AMPLIFY. |
| CFDOC-COST-BROAD-ROUTE | scanner-lead | COST | medium | [`config-and-security-checks.md`](config-and-security-checks.md) (routes); [`cost-footguns.md`](cost-footguns.md) | Broad Worker route should be verified. |
| CFDOC-COST-BROWSER-NO-CLOSE | scanner-lead | COST | high | [`cost-footguns.md`](cost-footguns.md) (Browser Run); [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §17 | Browser Run session is opened without an obvious close path. |
| CFDOC-COST-CRON-EVERY-MINUTE | scanner-lead | COST | medium | [`cost-footguns.md`](cost-footguns.md) (background job volume) | Cron trigger runs every minute. |
| CFDOC-COST-D1-LAYOUT-HOTPATH | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §24; [`cost-footguns.md`](cost-footguns.md) (D1 rows-read meter) | Layout/root loaders run on every page view; an uncached D1 query there multiplies billed rows read by sitewide traffic. |
| CFDOC-COST-D1-NO-INDEXES | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §24; [`cost-footguns.md`](cost-footguns.md) (D1 rows-read meter) | Schema SQL creates tables with no secondary index anywhere while code runs filtered/aggregate queries; ANALYZE/EXPLAIN QUERY PLAN guidance rides on the fix text. |
| CFDOC-COST-D1-ORDER-RANDOM | scanner-lead | COST | high | [`cost-footguns.md`](cost-footguns.md) (D1 rows-read meter) | D1 query orders by RANDOM(). |
| CFDOC-COST-DO-FRONT-DOOR | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §14; [`cost-footguns.md`](cost-footguns.md) (DO request/duration meters) | Durable Object call path lacks obvious front-door validation. |
| CFDOC-COST-DO-UNBATCHED-WRITES | folded-into:DO-STORAGE-BATCHING | COST | — | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §"Checks to add or strengthen" (§1, §14) | Duplicate/alias of DO-STORAGE-BATCHING; intentionally not registered as a separate scanner ID. |
| CFDOC-COST-DYNAMIC-WORKER-DEDUPE | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §16; [`cost-footguns.md`](cost-footguns.md) | Dynamic Worker load path lacks obvious stable ID/dedupe. |
| CFDOC-COST-KV-LIST-HOTPATH | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §1; proposed in §"Checks to add or strengthen" | KV list operation appears in application code. |
| CFDOC-COST-LOG-VOLUME | scanner-lead | COST | low | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §12; proposed in §"Checks to add or strengthen" | Explicit `head_sampling_rate = 1` produces a high-confidence volume-multiplier lead; traffic, retention, plan, and billing evidence are still required for materiality. |
| CFDOC-COST-MEDIA-VARIANT-EXPLOSION | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §4; proposed in §"Checks to add or strengthen" | Emitted by two scanner heuristics: image transform variants and Stream preload. |
| CFDOC-COST-ORIGIN-BYPASS | skill-prompt-only | COST | — | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §5, §11; proposed in §"Checks to add or strengthen" | Reassessed in 0.3.5: Terraform DNS-only records are already surfaced by `CFDOC-SEC-DNS-UNPROXIED` and public third-party origins by `CFDOC-COST-THIRD-PARTY-ORIGIN`; effective DNS proxy status, R2 public access, and origin-firewall state still require targeted account evidence. |
| CFDOC-COST-PAGES-FUNCTION-ROUTES | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §3; [`cost-footguns.md`](cost-footguns.md) | Pages _routes.json broadly invokes Functions without obvious static exclusions. |
| CFDOC-COST-PREVIEW-PUBLIC-PAID | skill-prompt-only | COST | — | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §13; proposed in §"Checks to add or strengthen" | Reassessed in 0.3.5: repo-visible preview paid bindings are already caught by `CFDOC-COST-TEMP-ENV-PAID-BINDINGS`; public/indexed status and lifecycle cleanup remain targeted account-evidence questions. |
| CFDOC-COST-R2-LIST-HOTPATH | scanner-lead | COST | medium | [`cost-footguns.md`](cost-footguns.md) (R2 operation meters) | R2 bucket list appears in application code. |
| CFDOC-COST-RETRY-AMPLIFY | scanner-lead | COST | medium | [`cost-footguns.md`](cost-footguns.md) (retry storms); [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §1 | Covers generic retry-without-backoff/circuit-breaker; distinct from the self-fetch-only CFDOC-COST-ASYNC-LOOP. |
| CFDOC-COST-SPEND-ALERTS-ONLY | skill-prompt-only | COST | — | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §9; proposed in §"Checks to add or strengthen" | Reassessed in 0.3.5: code-level bounds/circuit breakers are covered by mechanism-specific leads, but proving alerts are the only effective control requires account alerting plus runtime-control evidence. |
| CFDOC-COST-TEMP-ENV-PAID-BINDINGS | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §7, §13; proposed in §"Checks to add or strengthen" | Temporary/preview environment is connected to paid or stateful Cloudflare services. |
| CFDOC-COST-THIRD-PARTY-ORIGIN | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §10; proposed in §"Checks to add or strengthen" | Worker fetches a public third-party/serverless origin hostname. |
| CFDOC-COST-UNBOUNDED-FANOUT | scanner-lead | COST | medium | [`cost-footguns.md`](cost-footguns.md) (bounded fanout) | Promise.all map fanout lacks an obvious concurrency cap. |
| CFDOC-COST-VECTORIZE-DIMENSIONS | scanner-lead | COST | medium | [`cost-footguns.md`](cost-footguns.md) (Vectorize meters) | Vectorize query path should account for queried dimensions and fan-out. |
| CFDOC-COST-WORKERS-CACHE-BILLING | scanner-lead | COST | low | [`cost-footguns.md`](cost-footguns.md) (Workers Cache) and [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §23; proposed in §"Checks to add or strengthen" | Wrangler config enables Workers Cache (`cache.enabled`); billing surface changes and auth/gateway entrypoints must be excluded. |
| CFDOC-COST-WORKFLOW-STEPS | skill-prompt-only | COST | — | [`cost-footguns.md`](cost-footguns.md) and [`performance-and-reliability.md`](performance-and-reliability.md) (Workflows) | Review step count, state retention, retries, and child fan-out using code plus Workflow analytics; raw `step.do` counts are not sufficient for a static finding. |
| CFDOC-COST-WEBHOOK-NO-IDEMPOTENCY | scanner-lead | COST | medium | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §2, §19; proposed in §"Checks to add or strengthen" | Webhook-shaped projects with side effects and no repo-visible delivery/event dedupe key produce a low-confidence lead. Signature-verification ordering remains semantic review work. |
| CFDOC-FIT-KV-COORDINATION | scanner-lead | FIT | high | [`product-fit-rubric.md`](product-fit-rubric.md) (KV consistency limits) | KV read-modify-write smell for coordination/counters. |
| CFDOC-PERF-AWAITED-CACHE-PUT | scanner-lead | PERF | low | [`performance-and-reliability.md`](performance-and-reliability.md) | Cache put awaited in request path. |
| CFDOC-PERF-D1-N-PLUS-ONE | scanner-lead | PERF | low | [`performance-and-reliability.md`](performance-and-reliability.md) | Many D1 prepared statements in one file; check for N+1 queries. |
| CFDOC-PERF-D1-SELECT-STAR | scanner-lead | PERF | low | [`performance-and-reliability.md`](performance-and-reliability.md) | Projection/schema-coupling review only; `SELECT *` does not itself prove a full scan or extra billed rows. |
| CFDOC-PERF-PUBLIC-SERVICE-URL | scanner-lead | PERF | medium | [`performance-and-reliability.md`](performance-and-reliability.md) (service bindings) | Public Cloudflare service URL fetch; consider service bindings. |
| CFDOC-PERF-R2-BUFFERING | scanner-lead | PERF | medium | [`performance-and-reliability.md`](performance-and-reliability.md) (streaming) | R2 object may be buffered instead of streamed. |
| CFDOC-REL-QUEUE-NO-DLQ | scanner-lead | REL | medium | [`performance-and-reliability.md`](performance-and-reliability.md); current Queues retry/DLQ docs | No DLQ means permanent deletion after the configured limit (currently three retries by default), not unbounded platform retries. |
| CFDOC-REL-CROSS-BOUNDARY-RPC-DEAD | scanner-lead | REL | low | [`performance-and-reliability.md`](performance-and-reliability.md) (cross-boundary RPC); [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §22 | Cross-boundary public RPC methods need reachability review; scanner only detects the review surface, not deadness. |
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
| DO-STORAGE-BATCHING | scanner-lead | COST | low | [`war-story-scenario-checklist.md`](war-story-scenario-checklist.md) §14; current DO pricing/storage docs | Review repeated writes for coalescing/transaction latency. Batching distinct keys does not itself reduce billed rows/units; backend and rows changed matter. |
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

## False-negative leads found while building detection fixtures

Five gaps were found on 2026-06-09 and fixed in scanner 0.3.0, each with a
`gap-*` fixture under `evals/fixtures/detection/` that failed before the fix
and passes after:

- `DO-SHARDING-HOTSPOT` now also matches a singleton name held in a same-file
  string constant (`idFromName(COORDINATOR_KEY)`) or a per-deployment env var
  (`idFromName(env.REGION)`), not just literal singleton strings.
- `CFDOC-REL-QUEUE-NO-DLQ` gained a code arm: a `queue()` consumer handler
  with no consumer config anywhere in the repo (dashboard-managed consumer)
  is flagged as unreviewable retry/DLQ posture.
- `CFDOC-COST-ASYNC-LOOP` now also matches the
  `fetch(new URL(path, request.url))` self-fetch shape.
- `DO-ALARM-RECURSION` now only treats guards *between* the alarm declaration
  and the `setAlarm()` call as idle checks; an unrelated `if (` after the
  reschedule no longer suppresses the finding.
- `CFDOC-COST-MEDIA-VARIANT-EXPLOSION`'s Stream arm now fires when
  `preload="auto"` and the Stream hostname are in different files of the same
  project.

The five follow-up gaps were hardened in scanner 0.3.5:

- `DO-SHARDING-HOTSPOT` resolves bounded repo-visible string constants,
  imports/aliases, and concatenation chains. Arbitrary helper-function or
  runtime data flow remains outside static reach.
- `CFDOC-REL-QUEUE-NO-DLQ` compares literal `batch.queue`/`queueName` branches
  with every configured consumer, so one safe consumer cannot mask a second
  code-referenced queue. Dynamic queue names still require review.
- `DO-ALARM-RECURSION` requires guard terms inside an actual condition;
  ordinary variables named `nextRun` or `maxDelay` no longer suppress it.
  Guards hidden in helper functions remain semantic review work.
- The Stream preload arm now requires a same-file Stream marker or a reference
  to a symbol exported by a file containing a Stream host. This preserves the
  split-config fixture while suppressing unrelated local-video preload.
- `CFDOC-COST-ASYNC-LOOP` follows bounded same-file URL aliases derived from
  the incoming request. Cross-module/runtime URL construction remains outside
  static reach.
