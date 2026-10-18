# Cyberlane private D1 bill report

Reviewed: 2026-10-18. Next review: 2026-11-17.

Canonical evidence: `CFDOC-EVD-CYBERLANE-D1-BILL` in [the incident claim ledger](incident-claim-ledger.json). Source cluster: `cyberlane-private-d1-bill-2026-10-18`. Status: **unverified**. The posts establish an operator's report, including invoice quantities, charges, and period in a later follow-up. The original invoice was not attached to the inspected posts or independently inspected; billing reconciliation and the application mechanism remain unverified.

## Sources and what they establish

All five posts were published on 2026-10-18. Original post text was retrieved that day through X's syndication endpoint. The reply was also read in its expanded `note_tweet` form from `https://x.com/i/status/2111755448982315079`, because the syndication text truncates its final sentence.

| Source | Observation | Evidence limit |
|---|---|---|
| [Jay's original report](https://x.com/cyberlane/status/2111654229463146499), 03:02 UTC | Reports more than $500 in D1 reads and writes for two small databases supporting personal apps used only by him. | First-hand assertion; no invoice or meter totals attached to the inspected post. Small audience does not establish a small query workload. |
| [Jay's hosting context](https://x.com/Cyberlane/status/2111654232260784486), 03:02 UTC | Says the apps previously ran on a dedicated Hetzner server costing around EUR 30 per month. | Operator-stated comparison; does not demonstrate equivalent resource use, service scope, or total costs. |
| [Reply by @agrimkhurana](https://x.com/agrimkhurana/status/2111755448982315079), 09:45 UTC | Distinguishes scanned rows from returned rows, suggests missing indexes, `COUNT(*)`, OFFSET pagination or polling, and points to `wrangler d1 insights`. It argues the previous server absorbed the queries without an additional per-query bill. | Investigation leads from a commenter who supplies no account or application evidence. SQL syntax alone cannot establish an expensive query. |
| [Jay's follow-up](https://x.com/Cyberlane/status/2111759145720533053), 09:59 UTC | Accepts that inefficient queries or a loop are possible and emphasizes predictable costs. | An acknowledgment of possibilities and a stated product requirement; no confirmed cause or remediation result. |
| [Jay's invoice-detail follow-up](https://x.com/cyberlane/status/2111798271861833740), 12:35 UTC | Reports invoice quantities, separate read/write charges, and a September 17–October 16 billing period; details below. | Operator-reported invoice details, without an invoice attachment. The post explicitly leaves the usage cause unresolved. |

These posts belong to one report cluster. The reply is not a second incident, and agreement with a hypothesis is not independent corroboration. No claim is made about incident prevalence, user error, billing accuracy, or a Cloudflare defect.

## Operator-reported invoice details

The 12:35 UTC follow-up states these quantities and charges for September 17–October 16:

| Meter | Reported invoice quantity | Reported charge |
|---|---:|---:|
| Rows written | 452,256,462 | $453.00 |
| Rows read | 60,197,421,138 | $60.20 |

The reported total is **$513.20 before tax**. Writes account for approximately **88.3%** of that charge, calculated from the stated dollar amounts. This identifies the dominant reported cost meter, not the query or caller responsible. Read-only scan improvements would address the smaller reported charge; write execution counts, sync/retry behavior, imports, and index maintenance are higher-priority investigation leads, not established causes.

Preserve these as invoice quantities rather than relabeling them total raw usage. The original invoice's rate units, allowance treatment, rounding, and credits remain unavailable. Do not subtract an allowance again without establishing whether a quantity is gross usage or already billable, or replace the stated $453 with a reconstructed charge. The updated report strengthens the billing detail while leaving mechanism confidence at zero.

## Current semantics, checked separately

Official documentation was fetched on 2026-10-18. These sources establish product behavior, not what happened in Jay's account:

- [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/) counts rows read/scanned and rows written separately from returned rows. Writes include inserts, updates and deletes; index maintenance can add written rows, and index creation itself can consume usage. Plan allowances and current rates must be applied to the actual billing period before estimating charges.
- [D1 metrics and query insights](https://developers.cloudflare.com/d1/observability/metrics-analytics/) exposes aggregate row metrics and per-query row counts. Insights can sort by summed reads, writes, or executions; its Wrangler command is experimental, so verify options with the repository's pinned Wrangler before using it.
- [D1 index guidance](https://developers.cloudflare.com/d1/best-practices/use-indexes/) recommends checking the query plan and measuring row counts. An index can reduce reads while adding writes and storage; neither an index nor a query keyword alone determines total cost.
- [Cloudflare budget alerts](https://developers.cloudflare.com/billing/manage/budget-alerts/) are informational and do not pause or cap usage. Application-enforced work bounds require separate evidence.

The reply's conversion of a $500 bill into either a read total or a write total is not adopted as an account measurement. The later operator post supplies a mixed-meter invoice report and billing period; it does not supply allowance treatment, rate/rounding details, credits, query plans, or execution attribution. The commenter's hypotheses remain separate from these official semantics and the operator-reported quantities.

## Implications for cfdoctor

1. Include authenticated routes, polling, scheduled jobs, syncs and migrations in cost-path analysis. Estimate executions per period multiplied by queries per execution and measured rows per query, keeping reads and writes separate. Authentication and a single user do not bound this work.
2. Diagnose a D1 bill by reconciling invoice meters, query totals, execution counts, query plans and `meta.rows_read` / `meta.rows_written` over matching windows. Rank total reads and writes alongside execution count; latency alone misses frequent queries.
3. Prioritize the largest reported charge: writes are about 88.3% here despite many more read rows. Investigate write execution frequency and amplification, including repeated imports or full syncs, indexed updates, retries, and schema work. Retain separate read attribution and measure both sides before recommending an index or batching change.
4. Evaluate discovery from ambiguous symptoms with synthetic workloads and safe controls. Such fixtures test investigation behavior; they are not a replay of this incident and cannot prove its mechanism. This record intentionally has no derived check or fixture links.
5. Record the operator's acceptable spend and interruption behavior as product-fit inputs. Distinguish notification thresholds from measured work limits, stopping mechanisms and the availability cost of stopping. This preference does not confirm that any particular control was missing in the reported apps.

## Review and promotion criteria

At the next review, look for the underlying invoice lines and their rate/allowance/rounding treatment, database attribution, write-query insights and execution counts, representative plans, application code, or a measured remediation result. The operator has now supplied a reported meter breakdown and window; that is progress in billing evidence, not confirmation of a missing index, loop, or other application mechanism. Preserve source availability and distinguish operator-provided evidence from independently verified evidence; retain `unverified` while the underlying evidence remains absent.

Confidence uses the ledger's 0–2 dimensions: authenticity **2** (original source text inspected), mechanism **0** (unknown), independence **0** (one report cluster), applicability **2** (directly concerns D1/private-workload auditing), temporal **2** (same-day retrieval). Authenticity rates the provenance of the report, not the correctness of its billing claim.
