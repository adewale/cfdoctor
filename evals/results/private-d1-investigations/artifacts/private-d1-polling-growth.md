# Cloudflare Doctor: private dashboard D1 usage

The supplied evidence supports one cost finding: a visible dashboard polls a list query that scans the notes collection. A single owner can therefore generate substantial row reads, and each refresh becomes more expensive as that collection grows. This establishes a mechanism in the synthetic evidence, not the cause or amount of a real bill.

Scope inspected: Only supplied `README.md`, `wrangler.jsonc`, `index.js`, and `evidence.txt` in `private-d1-polling`, plus the Cloudflare Doctor skill, its D1 diagnosis reference, runtime networking instructions, and the two official pages below. Static inspection only; no application or D1 execution.

Scope not inspected: Deployed configuration, account settings, actual traffic, query execution counts, billing/usage exports, other databases, imports, migrations, background jobs, and production schema. These are unavailable, rather than proven absent. No production/account calls or installs were made.

Docs refreshed: 2026-10-18 — [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/) and [D1 indexes](https://developers.cloudflare.com/d1/best-practices/use-indexes/). Both were accessible.

The anonymous public-route gate does not apply: authentication rejects requests before database access (`index.js:15–17`, `evidence.txt:28`). No public-route release verdict is needed. Authentication is an effective rejection boundary, but it does not limit an authorized owner's repeated work.

Cost paths:

| path / trigger | frequency / window | queries / execution | rows read / query | rows written / query | evidence / unknowns | first enforced bound |
| --- | --- | --- | --- | --- | --- | --- |
| `/notes`, visible dashboard polling | Nominally every 10 seconds per polling instance while visible; actual executions/window unknown | 1 list query | Supplied sample: 50,000 at 50,000 notes; future values unknown | Sample: 0 | `index.js:2–10,20–22`; `evidence.txt:10–17,29–31`; active duration, tabs, successful arrivals/completions unknown | Auth before DB; visibility/abort limit this client timer; no authenticated per-period DB work cap |
| `/notes`, direct authenticated request | Unknown; route can be called independently of the timer | 1 same list query | Same supplied sample: 50,000 | Sample: 0 | `index.js:19–22`; no direct-call counts supplied | Auth; `LIMIT 20` bounds returned rows, not this demonstrated scan |
| `/diagnostics`, manual invocation: summary count | Manual; executions/window unknown | 1 count query | Sample: 1; summary table contains at most one row | Sample: 0 | `README.md:3`; `index.js:24–25`; `evidence.txt:8–9,19–23` | Auth, then schema cardinality bound |
| `/diagnostics`, same invocation: note lookup | Same manual invocations; do not count as a separate route invocation | 1 primary-key lookup | Sample: 1 | Sample: 0 | `index.js:26`; `evidence.txt:24–26` shows primary-key SEARCH | Auth, then primary-key lookup |
| Invalid credentials, non-GET, or unmatched route | Unknown | 0 | 0 from supplied handler | 0 from supplied handler | `index.js:15–19,29` | Rejected before DB access |

Let `P` and `U` be actual list-query executions from polling and other authenticated calls, and `D` be completed diagnostic executions running both statements, in the same window. At the supplied sample costs, read exposure is **`(P + U) × 1 × 50,000 + D × 1 × 1 + D × 1 × 1`**; sampled write exposure is **`(P + U) × 1 × 0 + D × 1 × 0 + D × 1 × 0 = 0`**. This is not an observed period total. Actual accounting must sum each execution's row metadata when costs vary; partial/failed diagnostic executions must be counted by the statements actually executed.

A hypothetical continuously visible hour with one timer and all 360 scheduled requests executing would read **18 million rows**, at the 50,000-note sample cost. If the same scan plan persists as the corpus grows to `N` notes, that scenario grows approximately as **`360 × N` reads/hour**; 100,000 notes would imply 36 million. These are projections, not measured usage or worst-case bounds. Multiple timers/tabs and direct calls add executions. The interval does not wait for the previous fetch, so requests can overlap when slow; no application retry policy or work cap is supplied. Platform retry behavior and real execution totals remain unmeasured.

### Severity: medium — repeated scans amplify private dashboard reads

- Category: cost footgun / missed optimization.
- Evidence: `index.js:2–10,20–22` links the ten-second polling timer directly to the list query. `evidence.txt:11–17` supplies the missing relevant indexes, `SCAN notes`, temporary sorting, and synthetic `rows_read=50000` despite only 20 returned rows. `README.md:3` identifies a growing collection. This is supported by the plan and row sample, not by SQL syntax alone.
- Why it matters: D1 accounts for rows read and written, rather than returned-row count or owner count. Repeated scans multiply that unit by execution frequency; corpus growth raises the per-execution term. The evidence supports read amplification, not unexplained writes or storage charges.
- Fix: First test a composite index aligned with this filter and ordering, such as `CREATE INDEX idx_notes_archived_updated ON notes(is_archived, updated_at DESC)`, as a one-time schema change outside the request handler. Validate before applying it to a real database. Also reduce needless executions through refresh-on-change/manual refresh or a longer interval acceptable to the owner; prevent overlapping refreshes. Reducing frequency alone leaves growth in scan cost, while indexing alone leaves unnecessary polling. No evidence requires replacing D1.
- Cost / trade-off: Expected read savings require before/after measurements; do not promise exactly 20 billed reads. Index construction has a one-time usage cost, the index occupies storage, and writes affecting indexed columns add index-maintenance writes. Write frequency is unknown. Less frequent refreshes trade freshness for fewer executions.
- Verify: On equivalent local/staging data, compare the identical bound query before/after using `EXPLAIN QUERY PLAN` and `meta.rows_read`/`meta.rows_written`; check index use and whether temporary sorting disappears. Follow the index guidance on `PRAGMA optimize`. Repeat at a larger representative corpus to test growth. Separately compare actual execution counts and total row meters over equivalent active-use windows after changing the refresh policy. No such verification was run here.
- Source basis: [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/) establishes row meters, metadata measurement, index write/storage costs, and plan-dependent allowances/windows. [D1 indexes](https://developers.cloudflare.com/d1/best-practices/use-indexes/) supports multi-column index candidates, plan verification, and measuring index benefits.
- Confidence: High for the supplied scan-and-poll mechanism; unknown for historical bill attribution and unmeasured post-fix savings.

The manual diagnostics are not a second confirmed cost problem: the summary `COUNT(*)` is constrained to at most one row, and `SELECT *` uses an integer primary-key lookup with one sampled read. They contribute two sampled reads per complete manual invocation, not two extra queries on every dashboard poll.

To reconcile a real bill, the smallest missing package is actual list/diagnostic execution counts and row totals for the affected database and billing window, plus a redacted D1 meter excerpt showing plan, allowance scope, window/timezone, reads, writes, storage, and charges. Query samples cannot establish those totals, and one database's data cannot reconstruct an account-wide invoice. No exact dollar estimate is justified by the supplied evidence.
