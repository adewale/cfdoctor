# D1 bill diagnosis

Use for a concrete D1 bill or usage anomaly after inspecting the supplied repository and billing evidence. Small user counts, authentication, and low public traffic do not bound database work. Diagnose the read, write, and storage meters separately.

## Use the smallest official source set

Normal bill diagnosis needs [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/) for meter definitions/rates and [D1 metrics and analytics](https://developers.cloudflare.com/d1/observability/metrics-analytics/) for measurement/insights. Fetch only the pages needed for the unresolved claims; supplied-artifact triage may need fewer. Record the observation date. Those pages were checked on 2026-10-18; this file is navigation, not frozen pricing authority. For a narrow task, use at most two direct official pages unless a documented conflict requires more. Replace an irrelevant page with one that resolves the actual question rather than expanding the bundle.

## 1. Establish what was billed

Request the smallest redacted D1 invoice/export excerpt: account alias, billing period with timezone, plan/contract, each meter's quantity and unit, included allowance, rate, and charge. Keep reads, writes, and storage separate; query count and latency are not row meters. Keep account allowances separate from per-database usage: do not subtract the same included allowance for every database. If entitlement scope is absent, mark it unknown rather than inventing a charge.

Match the usage window to the invoice window, including subscription renewal boundaries. Record discounts, credits, and known missing databases without requesting an entire account inventory. Supplied account totals can establish the allowance calculation while investigation remains scoped to one suspect database. Do not extrapolate an old invoice from a recent rolling window or treat storage snapshots as a full storage-month bill.

## 2. Trace execution frequency before collecting more

Map suspect query templates to callers in code: private dashboards, open-tab polling, scheduled jobs, alarms, queues/retries, syncs, imports, and migrations as well as public requests. Record:

```text
origin/caller | database | executions per period | queries per execution | measured rows read/query | measured rows written/query | evidence/window
```

Multiply frequency, queries, and measured row counts for each meter separately; label assumptions and ranges. The same SQL template can have different costs by parameter selectivity, page depth, and dataset state: separate materially different input/cardinality cohorts or preserve a measured distribution/range. A sampled average is not a guaranteed upper bound and cannot stand in for every execution or future data growth. Count actual statement executions, including batch members and retries, without double-counting them in both multipliers. Table size, returned rows, user count, and query duration alone do not establish scanned rows or billed cost.

## 3. Collect only the missing measurements

Prefer supplied exports and existing `meta.rows_read` / `meta.rows_written` observations. Before any new account read, state the hypothesis, why supplied evidence is insufficient, exact account/database/window, read-only command shape, retained fields, redactions, and stop condition. Obtain explicit approval for that scope and keep every authenticated command pending until then. This matches the [targeted account-read boundary](targeted-account-reads.md); no additional reference read is needed for this recipe. No deploy, schema change, production query replay, or tool installation belongs in collection.

Use an already installed, project-pinned executable directly. First inspect local availability and help:

```bash
./node_modules/.bin/wrangler --version
./node_modules/.bin/wrangler d1 insights --help
```

The command is experimental. As of the check above, the [Wrangler command reference](https://developers.cloudflare.com/d1/wrangler-commands/#d1-insights) documents `--time-period`, while the metrics page's older examples use `--timePeriod`. Resolve that documented conflict with the pinned executable's help; do not assume either spelling is universal. If the executable/command/options are absent, stop and request an exact dashboard export or separately reviewed scoped analytics query. Do not install or upgrade Wrangler, or invoke a package runner to gain the command.

Review these shapes with the exact database, config/environment selectors, lookback, retained fields, and limit before approval. Only use options confirmed by that executable's help:

```bash
./node_modules/.bin/wrangler d1 insights "<DATABASE>" --time-period="<LOOKBACK>" --sort-type=sum --sort-by=reads --sort-direction=DESC --limit=10 --json
./node_modules/.bin/wrangler d1 insights "<DATABASE>" --time-period="<LOOKBACK>" --sort-type=sum --sort-by=writes --sort-direction=DESC --limit=10 --json
./node_modules/.bin/wrangler d1 insights "<DATABASE>" --time-period="<LOOKBACK>" --sort-type=sum --sort-by=count --sort-direction=DESC --limit=10 --json
```

Use all three rankings when both usage and frequency remain unresolved; omit a read that cannot change the diagnosis. The documented defaults are a one-day rolling window, total-time ranking, and five queries; none establishes total billed rows. Retain query-template aliases/redacted SQL, `totalRowsRead`, `totalRowsWritten`, `numberOfTimesRun`, useful per-execution averages, window, observation timestamp, and collection limits. Query text can contain literal secrets or personal data even when bound values are omitted. Keep raw results outside Git, redact literals and identifiers while preserving nonsensitive selectivity/cardinality evidence, hash the retained evidence, and remove raw results after review.

A limited insights result is a lead list, not complete invoice reconciliation. Record truncation, retention, aggregation/sampling caveats, window mismatch, and uninspected databases; missing queries or fields are unknown. Request exact database/window row totals only if they would resolve the remaining gap. Do not silently widen the database set, time range, or limit.

## 4. Verify the mechanism and stop

For a candidate, correlate execution counts with its caller/frequency and inspect the SQL, schema/index definitions, representative parameters, query plan, and existing row metadata. Label local/staging measurements separately from observed production usage. `COUNT(*)`, `SELECT *`, polling, deep `OFFSET`, a low returned/read ratio, or an absent plan cannot by themselves prove a missing index or an expensive scan. A bounded indexed query or small infrequent workload may need no change.

For writes, inspect repeated full syncs, unchanged-row rewrites, retries/idempotency, imports, migrations, and index maintenance. An index recommendation needs a measured read benefit and write trade-off. Validate the smallest fix against equivalent data/query inputs and comparable workload windows, including both row meters and execution counts; do not replay production writes to measure them.

Report the confirmed mechanism, evidence and coverage, smallest proposed fix, validation, current official Source basis, and any unreconciled bill remainder. If attribution is incomplete, preserve the hypothesis and name the smallest missing evidence instead of declaring a guaranteed culprit.
