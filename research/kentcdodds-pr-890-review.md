# kentcdodds.com PR #890 Cloudflare Doctor review

Date reviewed: 2026-08-10. Method: read the merged PR
(`https://github.com/kentcdodds/kentcdodds.com/pull/890`, "fix(d1): cut
rows-read billing from PostRead aggregates (~$195/mo)", merged 2026-08-08,
authored via the repo's kody-bot agent), its diff, the review thread, and the
merged `docs/agents/data-table-conventions.md` plus
`services/site/app/utils/cache.server.ts` on `main` to confirm the caching
stack.

Use these notes as scenario discovery and mechanism evidence, not pricing
authority. Pair every recommendation with current official Cloudflare docs.
Ledger record: `CFDOC-EVD-KCD-D1-ISOLATE-CACHE` in
`research/incident-claim-ledger.json`.

## Incident summary

The August 2026 invoice (IN-74519948, $213.79 total) contained a $195.05 D1
line item for 195 billion rows read. D1 analytics attributed ~96% of it to two
full-table aggregates over an ~961K-row `PostRead` table:

| Query | Cache before | TTL before | Executions/week | Rows read (invoice window) |
|---|---|---:|---:|---:|
| `getBlogPostReadCounts` (read counts per post) | per-isolate `lruCache` | 30 min | 42,720 | 41.06B |
| `getReaderCount` (`COUNT(DISTINCT ...)`) | per-isolate `lruCache` | 5 min | 10,770 | 10.35B |

Both queries were cached — with TTLs — through `@epic-web/cachified`, but the
cache adapter was a module-scope `lru-cache` instance (max 500 entries) held in
isolate memory. The PR's stated root cause: "Every isolate churn (deploys,
eviction, the 2-minute warmup cron) re-ran a full-table scan despite 5–30 min
TTLs — ~127× more often than the TTLs imply."

The 127× figure is derivable from the PR's own numbers: a perfectly shared
30-minute TTL allows 336 refreshes/week; 42,720 observed executions ÷ 336 ≈
127. Rows-per-execution (41.06B ÷ 42,720 ≈ 961K) matches the table size, i.e.
every execution was a full scan, and both queries scanned the same table.

The fix (all four parts matter):

1. Moved `blog:post-read-counts` and `total-reader-count` from `lruCache` to
   the shared cache (`SITE_CACHE_KV` KV namespace, or a `CACHE_RPC` service
   binding when present).
2. Raised `total-reader-count` TTL from 5 minutes to 1 hour — an explicit
   freshness downgrade accepted for a vanity metric.
3. Stopped the `mark-as-read` action from force-refreshing 18 ranking queries
   (`forceFresh: true`) when `addPostRead` deduplicated a repeat read within
   the week; only genuinely new rows trigger the refresh, and tests now assert
   that billing-relevant behavior.
4. Recorded the convention in `docs/agents/data-table-conventions.md`: "D1
   bills rows scanned, not rows returned"; expensive `getFreshValue` MUST use
   the shared `cache`; reserve `lruCache` for values that are cheap to
   recompute; verify via GraphQL `d1QueriesAdaptiveGroups` ordered by rows
   read.

Expected impact stated in the PR: these paths drop from ~220B to ~2B rows
read/month, taking the line item to ~$0 inside D1's included allotment
(confirm current pricing/allotments against official docs before quoting).

## Lessons for Cloudflare Doctor

### 1. Cache-layer placement is the audit question, not cache presence

`cost-footguns.md` already flags "recomputing public query results on every
request instead of caching." This code *was* caching, with sane-looking TTLs,
using the ecosystem-default cachified pattern. A presence/TTL-level audit
passes it. The failing property was the adapter: per-isolate memory as the
*only* layer under an expensive recompute. The audit question is "what is the
worst-case recompute rate when this cache layer is cold, and who pays it?" —
per layer, not per callsite. `performance-and-reliability.md` line
"avoid assuming isolate memory is durable or globally shared" states the
premise but is not currently connected to any cost check, D1 guidance, or
check ID.

### 2. Per-isolate TTLs do not bound global recompute rate

Effective refresh rate ≈ (isolates across colos × churn events), not 1/TTL.
Deploys, evictions (no guaranteed isolate lifetime), low-traffic colos, and —
ironically — a 2-minute warmup cron each start cold isolates that re-run
`getFreshValue` immediately. The observed multiplier here was ~127× on a
30-minute TTL. Any serverful habit carried onto isolate platforms has this
shape: module-scope memoization, in-memory rate limiters, per-process OAuth
token caches. TTL math in audits must multiply by isolate churn or use a
shared layer.

### 3. The D1 meter multiplies per-execution scan size by execution count

This is the second accepted first-hand D1 rows-read incident in the ledger,
and the two factor the same product differently:

- `CFDOC-EVD-D1-134-BILL` (whatmedicaidpays, 2026-04): scan size per
  execution was the defect — missing composite indexes on hot layout queries
  (~765K rows/page view). Fix: indexes + `ANALYZE` + caching.
- This incident: execution *count* was the defect — the scans were inherent
  (whole-table aggregates), and the cache architecture failed to amortize
  them. Fix: shared cache + fewer bypasses.

An audit that only checks indexes/query shape misses the second class; one
that only checks caching misses the first. Both records currently carry no
check IDs or fixtures — together they justify a fixture-first D1 rows-read
check family (see follow-ups).

### 4. Cache-bypass paths reachable from public actions are amplifiers

The `mark-as-read` action ran 18 `forceFresh: true` ranking queries per
invocation even when the read was a duplicate no-op. Audit lead: any
`forceFresh`/cache-purge/refresh triggered by an unauthenticated or
per-request user action, not gated on "did state actually change?". Same
family as existing webhook-idempotency and KV-list-hot-path checks: work per
request must be conditional on new state, or it becomes attacker/crawler
drivable.

### 5. `forceFresh` is not recursive (invalidation review nugget)

The review thread (CodeRabbit) flagged that forcing freshness of an outer
cachified value does not propagate into nested cachified calls inside its
`getFreshValue` — inner keys can still serve stale data, and conversely
new-row creation does not invalidate the now-shared aggregate keys until TTL
expiry. When auditing layered caches, trace invalidation per key, and treat
"accepted staleness up to TTL" as a documented trade-off, not an accident.
This PR did that consciously (5 min → 1 h).

### 6. Invoice → query attribution is a reusable evidence recipe

The incident was detected by the invoice, then attributed with D1 GraphQL
analytics (`d1QueriesAdaptiveGroups` ordered by rows read), which gives
per-query-shape rows-read and execution counts — exactly the evidence the
skill's account-evidence workflow should request for any D1 cost question.
The pre-invoice smell was visible in the same data: executions ≫ TTL-implied
refresh rate, and rows-read/execution ≈ table size. Candidate addition to the
targeted-account-reads registry (hypothesis-driven, read-only, redacted).

### 7. Cost behavior can and should be unit-tested

The PR added action-level tests asserting repeat reads skip the ranking
refresh while new reads trigger it — a billing-behavior regression test.
Audits that recommend "stop doing expensive work on duplicates" should also
recommend the test that keeps it true; this matches the skill's mandatory
Verify field.

### 8. Agent-maintained repos need platform sharp edges written down

The expensive pattern is the default-looking one (cachified + lru-cache is
the library's canonical example), the fix was authored by an agent
(kody-bot), and the durable artifact is a conventions doc
(`docs/agents/data-table-conventions.md`) that future agent sessions load.
For agent-maintained Cloudflare repos, a finding's "smallest safe fix" can
legitimately include "record the convention where agents will read it" so the
class of bug stays fixed. That is also a validation of cfdoctor's own
reference-driven design.

## Derivations (implemented 2026-08-10 in the same change series)

- Scanner lead `CFDOC-COST-D1-ISOLATE-CACHE` (scanner 0.3.7, COST, medium
  severity, medium confidence). Fires on two shapes when the file has D1
  evidence and an aggregate SQL string (`COUNT`/`SUM`/`AVG`/`GROUP_CONCAT` +
  `FROM`, or `SELECT … FROM … GROUP BY`): a cachified-style call site whose
  `cache:` adapter is memory-only (`lruCache`, `memoryCache`, `new Map(`,
  `new LRUCache(`) with the aggregate inside that call site's window, or a
  module-scope `Map`/`LRUCache` memo used near the aggregate with no shared
  layer (`env.*.get/put`, `caches.*`, `KVNamespace`, `CACHE_RPC`) in the same
  window. Precision held by design and by tests: shared/KV adapters,
  L1-memory-over-L2-shared layering, and memory caching of cheap point
  queries do not fire.
- Detection fixtures: `d1-isolate-cache-rescan` (both bad shapes behind a hot
  route and a 2-minute warmup cron; must fire) and `d1-shared-cache-safe`
  (KV-backed adapter, L1-over-L2 map, cheap-value LRU; `max_findings: 0`).
  Four scanner unit tests in `tests/test_static_scan.py` cover fire and
  suppress directions.
- Runtime scenario 24 added to the war-story checklist;
  `scripts/check_claim_ledger.py` widened to scenarios 1..24; ledger record
  `CFDOC-EVD-KCD-D1-ISOLATE-CACHE` wired to the scenario, check, and both
  fixtures. Guidance added to `cost-footguns.md` (D1 section) and the layered
  cache map in `performance-and-reliability.md`.

## Remaining follow-ups (queued in TODO.md)

- The missing-index/hot-query half of the meter (grounded in
  `CFDOC-EVD-D1-134-BILL`) needs schema/index awareness the regex scanner
  lacks; it stays a skill-level question until a fixture-first heuristic
  exists.
- The `forceFresh`-from-public-action amplifier should fold into the existing
  idempotency/hot-path check family rather than a new pillar.

## Official docs to pair with these scenarios

- https://developers.cloudflare.com/d1/platform/pricing/ — rows-read billing
  unit and included allotments.
- https://developers.cloudflare.com/d1/observability/metrics-analytics/ —
  `d1QueriesAdaptiveGroups`, rows-read attribution.
- https://developers.cloudflare.com/d1/best-practices/use-indexes/ — the
  scan-size half of the meter.
- https://developers.cloudflare.com/workers/reference/how-workers-works/ —
  isolates have no guaranteed lifetime and may be evicted; global state is
  per-isolate.
- https://developers.cloudflare.com/kv/ — shared-cache backing store
  semantics (eventual consistency, read pricing) for the trade-off side.
