# Cyberlane private D1 bill report

Reviewed: 2026-10-18. Next review: 2026-11-17.

Canonical evidence: `CFDOC-EVD-CYBERLANE-D1-BILL` in [the incident claim ledger](incident-claim-ledger.json). Source cluster: `cyberlane-private-d1-bill-2026-10-18`. Status: **unverified**. The posts establish that an operator reported a bill and expressed a cost preference; they do not establish the invoice amount, row-meter breakdown, or database failure mechanism.

## Sources and what they establish

All four posts were published on 2026-10-18. Original post text was retrieved that day through X's syndication endpoint. The reply was also read in its expanded `note_tweet` form from `https://x.com/i/status/2111755448982315079`, because the syndication text truncates its final sentence.

| Source | Observation | Evidence limit |
|---|---|---|
| [Jay's original report](https://x.com/cyberlane/status/2111654229463146499), 03:02 UTC | Reports more than $500 in D1 reads and writes for two small databases supporting personal apps used only by him. | First-hand assertion; no invoice or meter totals attached to the inspected post. Small audience does not establish a small query workload. |
| [Jay's hosting context](https://x.com/Cyberlane/status/2111654232260784486), 03:02 UTC | Says the apps previously ran on a dedicated Hetzner server costing around EUR 30 per month. | Operator-stated comparison; does not demonstrate equivalent resource use, service scope, or total costs. |
| [Reply by @agrimkhurana](https://x.com/agrimkhurana/status/2111755448982315079), 09:45 UTC | Distinguishes scanned rows from returned rows, suggests missing indexes, `COUNT(*)`, OFFSET pagination or polling, and points to `wrangler d1 insights`. It argues the previous server absorbed the queries without an additional per-query bill. | Investigation leads from a commenter who supplies no account or application evidence. SQL syntax alone cannot establish an expensive query. |
| [Jay's follow-up](https://x.com/Cyberlane/status/2111759145720533053), 09:59 UTC | Accepts that inefficient queries or a loop are possible and emphasizes predictable costs. | An acknowledgment of possibilities and a stated product requirement; no confirmed cause or remediation result. |

These posts belong to one report cluster. The reply is not a second incident, and agreement with a hypothesis is not independent corroboration. No claim is made about incident prevalence, user error, billing accuracy, or a Cloudflare defect.

## Current semantics, checked separately

Official documentation was fetched on 2026-10-18. These sources establish product behavior, not what happened in Jay's account:

- [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/) counts rows read/scanned and rows written separately from returned rows. Writes include inserts, updates and deletes; index maintenance can add written rows, and index creation itself can consume usage. Plan allowances and current rates must be applied to the actual billing period before estimating charges.
- [D1 metrics and query insights](https://developers.cloudflare.com/d1/observability/metrics-analytics/) exposes aggregate row metrics and per-query row counts. Insights can sort by summed reads, writes, or executions; its Wrangler command is experimental, so verify options with the repository's pinned Wrangler before using it.
- [D1 index guidance](https://developers.cloudflare.com/d1/best-practices/use-indexes/) recommends checking the query plan and measuring row counts. An index can reduce reads while adding writes and storage; neither an index nor a query keyword alone determines total cost.
- [Cloudflare budget alerts](https://developers.cloudflare.com/billing/manage/budget-alerts/) are informational and do not pause or cap usage. Application-enforced work bounds require separate evidence.

The reply's conversion of a $500 bill into either a read total or a write total is not adopted as an account measurement. The operator reports both reads and writes, and no billing period, allowances, credits, taxes, or meter split is available. Its hypotheses remain separate from these official semantics.

## Implications for cfdoctor

1. Include authenticated routes, polling, scheduled jobs, syncs and migrations in cost-path analysis. Estimate executions per period multiplied by queries per execution and measured rows per query, keeping reads and writes separate. Authentication and a single user do not bound this work.
2. Diagnose a D1 bill by reconciling invoice meters, query totals, execution counts, query plans and `meta.rows_read` / `meta.rows_written` over matching windows. Rank total reads and writes alongside execution count; latency alone misses frequent queries.
3. Investigate write amplification as well as scans: repeated imports or full syncs, updates to indexed columns, and schema work on request paths. Measure both sides before recommending an index or batching change.
4. Evaluate discovery from ambiguous symptoms with synthetic workloads and safe controls. Such fixtures test investigation behavior; they are not a replay of this incident and cannot prove its mechanism. This record intentionally has no derived check or fixture links.
5. Record the operator's acceptable spend and interruption behavior as product-fit inputs. Distinguish notification thresholds from measured work limits, stopping mechanisms and the availability cost of stopping. This preference does not confirm that any particular control was missing in the reported apps.

## Review and promotion criteria

At the next review, look for an operator follow-up with an invoice/meter breakdown, named billing window, D1 insights totals, representative query plans, execution counts, or a measured remediation result. Preserve source availability and distinguish operator-provided evidence from independently verified evidence. If none appears, retain `unverified`; do not infer a missing index or loop from the bill alone.

Confidence uses the ledger's 0–2 dimensions: authenticity **2** (original source text inspected), mechanism **0** (unknown), independence **0** (one report cluster), applicability **2** (directly concerns D1/private-workload auditing), temporal **2** (same-day retrieval). Authenticity rates the provenance of the report, not the correctness of its billing claim.
