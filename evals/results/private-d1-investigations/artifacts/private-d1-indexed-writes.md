# Cloudflare Doctor — focused D1 triage

Scope inspected: Supplied `README.md`, `wrangler.jsonc`, `index.js`, and `evidence.txt` in `private-d1-indexed-writes`; the Cloudflare Doctor skill and its D1 bill-diagnosis reference. Read-only source review; no scanner or database queries run.

Scope not inspected: Deployed configuration, actual task attempts, production query metadata, account usage/bill, plan/allowance, other database workloads, and consumers of the three secondary indexes. No production/account calls, installs, or implementation changes.

Docs refreshed: [Cloudflare D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/), fetched 2026-10-18. No docs access limitation encountered.

The supplied model explains how writes can grow despite one user and modest reads: the scheduled job updates 1,000 rows every 15 minutes, and each sampled update reports **1 row read and 4 rows written**. The three indexes containing the changed column explain the write amplification. This confirms a mechanism in the synthetic evidence, **not the cause or amount of a historical production bill**; no actual usage totals or attempts were supplied (`README.md:3–5`, `evidence.txt:1–2,14–24,27`).

Cost paths:

| path / trigger | frequency / window | queries / execution | rows read / query | rows written / query | evidence / unknowns | first enforced bound |
|---|---|---|---|---|---|---|
| Scheduled refresh; `*/15 * * * *` | 96 nominal slots/day; actual attempts/completions unknown | 1,000 individual UPDATEs on a complete run | 1 in supplied modeled run | 4 in supplied modeled run | `wrangler.jsonc:6`; `index.js:12–16`; `evidence.txt:10–15,26–27`. Partial runs, overlapping invocations, and repeated attempts are unmeasured. No application retry loop is present. | Fixed IDs 1–1,000 limit one invocation to 1,000 application statements; no daily work stop or cross-invocation bound is supplied. |
| Fetch: authenticated `/status`, authentication failures, and unsupported requests | Request volume unknown | 0 D1 statements | N/A; 0 per request | N/A; 0 per request | `index.js:3–10`; no fetch branch accesses D1 | All branches return without database work. |

There is no anonymous D1 request path in the supplied code, so the public-route release gate does not apply.

For **A complete executions**, using the supplied samples:

- Reads: `A × 1,000 × 1 = 1,000A`.
- Writes: `A × 1,000 × 4 = 4,000A`.
- At exactly one complete execution per slot: **96,000 reads/day and 384,000 writes/day**; an illustrative 30-day window gives **2.88 million reads and 11.52 million writes**.

These are projections, not observed totals or guaranteed bounds. Failed partial runs require actual statement counts; overlap or extra attempts require additional execution terms. The fixed ID range bounds this handler's per-invocation target set even if the database grows. Samples do not establish costs for other statements, schemas, or future states. No aggregate telemetry was supplied to add to these terms.

### Severity: medium — scheduled indexed updates amplify the write meter

- **Category:** cost footgun.
- **Evidence:** `index.js:13–15` changes `sync_state` for every fixed ID. `evidence.txt:5–9` defines three secondary indexes containing `sync_state`. The primary-key lookup plan and current-schema sample are `rows_read=1`, `rows_written=4` (`evidence.txt:12–15`). The hypothetical clone without those indexes retains the same primary-key plan and reports `1` read / `1` write (`evidence.txt:17–24`).
- **Why it matters:** D1 meters reads and writes separately. Updating indexed columns adds index writes. Low interactive traffic does not reduce this scheduled workload, and the supplied plan does not support a missing-index or full-scan diagnosis for this UPDATE.
- **Fix:** Investigate actual attribution before selecting an implementation change. Match this UPDATE's execution count and row meters to the same database and billing window, then establish which queries need each index. The clone comparison alone does not justify dropping all three indexes.
- **Cost / trade-off:** In the comparison model, writes fall from 4,000 to 1,000 per complete run: **3,000 fewer writes/run, or 75% of this UPDATE workload**. Under the daily scenario that is 288,000 fewer writes/day; reads remain 96,000/day for this handler. Other queries could incur more reads or latency without the indexes, and their consumers are unknown. This is neither a measured production saving nor a whole-bill saving. Batching the same statements is not evidence of fewer billed rows. A routine unchanged-value filter also has no demonstrated benefit for consecutive runs: the scheduled input deliberately alternates state.
- **Verify:** Use existing, redacted evidence for actual invocations, completed UPDATE executions, and `rows_read`/`rows_written` totals over one matching window. Compare equivalent data and inputs in an isolated clone while retaining the consumer queries and their plans; measure both row meters and execution counts before evaluating any index or refresh change. Do not replay writes against production to measure them.
- **Source basis:** [Current official D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/) documents separate row meters, additional writes for indexed columns, and query `meta` row counters. The supplied plans and samples establish this fixture's 4-to-1 comparison; the docs do not prove its production attribution.
- **Confidence:** High for the supplied synthetic mechanism and arithmetic; unknown for actual billing attribution and safe index removal.

The smallest missing evidence is: (1) this database's actual task/statement counts and read/write totals for the reported window, including failures or repeated attempts; (2) the corresponding redacted D1 bill/usage excerpt with account scope, plan, allowance, meter quantities, and period/timezone; and (3) the query templates and measured read benefit of each named secondary index. Account-wide allowance arithmetic needs matching account totals, not just this database. No dollar estimate or schema change is supported yet.
