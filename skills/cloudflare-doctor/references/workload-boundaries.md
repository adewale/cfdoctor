# Workload boundaries

Read the sections that answer an evidenced question. Scanner leads locate
syntax; they do not establish deployed reachability, incoming cardinality,
helper behavior, actual token permissions or measured cost. Fetch the linked
official sources before applying mutable semantics.

## Deployment and runtime evidence

Start from the deployment workflow and the configuration it actually uses.
A checked-in Wrangler file can be a local-development example while a CLI
generates customer deployments elsewhere. Inspect generated declarations and
installed artifacts separately, preserving conditions and unresolved values.
Do not execute an installer, renderer or arbitrary target code to collect them.
An installed artifact in Git is evidence of that artifact, not live deployment
parity. List excluded large bundles and build/source parity as uninspected.

Separate Worker entrypoints and their imports, Node provisioning/CLI code,
browser bundles, tests, static-only deployments, and unresolved shared code.
A node: import can belong to a Worker using Node compatibility; it is not
sufficient to classify that entrypoint as a CLI. A local variable named window
does not establish a browser runtime. Keep configuration environments and
binding namespaces separate. Detect HTTP product dependencies as well as
Wrangler bindings. A Pipelines binding's stream field is not the Stream video
product. See [Pipelines bindings](https://developers.cloudflare.com/basin-pipelines/streams/writing-to-streams/).

For jurisdictional storage, trace bucket creation, existing-bucket lookup,
generated binding, upload and query endpoints. A creation flag does not change
an existing resource. Compare all those boundaries with
[R2 jurisdiction requirements](https://developers.cloudflare.com/r2/reference/data-location/).

For generated routes, use the actual zone name/ID. Taking the last two hostname
labels yields co.uk for analytics.example.co.uk and cannot identify delegated
subzones. Prefer explicit zone input or an authorized scoped lookup over a
hostname guess. See [Wrangler routes](https://developers.cloudflare.com/workers/wrangler/configuration/).

## D1 parameters and invocation queries

Count each statement's fixed parameters plus each spread's multiplicity.
For example, under the currently documented 100-parameter limit:

- Two fixed parameters plus N IDs permit at most 98 IDs.
- One fixed parameter plus the same IDs in three predicates permits at most 33 IDs.
- Chunking SELECTs does not bound an UPDATE built from their combined results.

Prove cardinality from callers, validation or measured inputs before calling an
overflow confirmed. A maximum supported batch that can exceed the budget is a
reproducible case even if typical requests are smaller. Chunk every affected
statement and verify complete semantics after partial failure.

Keep parameter count, individually executed queries, batch calls and billed
rows separate. A helper selecting S records and issuing two individual queries
per record can issue 1 + 2S queries before caller work. Current D1 invocation
limits are 50 Free / 1000 Paid. A db.batch call counts as one against that
invocation limit, while parameter limits still apply to each contained
statement. Batching does not by itself reduce billed rows. Refresh
[D1 limits](https://developers.cloudflare.com/d1/platform/limits/) and
[D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/).

## Cost paths for public and private work

Inventory anonymous POST uploads/flags, authenticated API/MCP/dashboard calls,
polling, cron, imports, migrations, erasure and retries when evidenced. Do not
invent a polling frequency or presume that a small number of users/databases
bounds query executions. Crawler inventories do not cover public ingestion.

For repeated D1 work, emit `Cost paths:` with this header:

`path / trigger | frequency / window | queries / execution | rows read / query | rows written / query | evidence / unknowns | first enforced bound`

Separate query shapes and data/selectivity cohorts. For each path, model reads
and writes independently as executions in window × queries/execution × measured
rows/query. Include retries, overlap and index maintenance when evidenced.
Distinguish observed totals, sampled units and hypothetical projections. A sample
is not a worst-case bound. Sum components without adding the same account total
again. Reconcile the matching product/account/plan/window. Unknown is not zero.

Use [D1 result metadata](https://developers.cloudflare.com/d1/worker-api/return-object/)
and relevant query plans. SELECT *, COUNT, OFFSET and a missing plan are leads,
not proof of a missing index or scan. Small output does not bound work read.

## Expansion, accumulated work and throughput

Trace compressed input, expanded bytes, parsed objects, retained session data,
number of keys/pages and nested fan-out separately. Check sizes while streaming
and stop before the allocation grows beyond the budget. A size test after
request.arrayBuffer(), response.text() or decompression cannot protect the
allocation that already occurred. A compressed-byte cap does not bound expanded
bytes; six concurrent fetches can still retain an arbitrarily large session.
See [Workers memory and execution limits](https://developers.cloudflare.com/workers/platform/limits/).

For jobs, compare admitted arrivals with completed work per interval and oldest
backlog age. A per-run item cap does not bound nested work per item or prove
that the queue can drain. Inspect starvation, overlap, failures, retry ownership
and resumable progress. A pre-dependency rate check is useful admission evidence;
the [Workers Rate Limiting API](https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/)
is approximate and location-local, so do not claim it enforces a worldwide
spending cap. Establish permitted degradation and acceptable overshoot before
recommending strict coordination.

## Deletion and cross-store retries

Follow the operation from its caller to completion. A helper's SQL LIMIT can
be an appropriate slice when the caller resumes it; the same helper can be
incorrect when a caller removes identity links and declares the whole erasure
complete after one call. Preserve identifiers and progress until every matching
row/object/note is accounted for. Verify more than one page/slice, invocation
budget exhaustion and restart after partial deletion. Treat data-deletion
correctness separately from legal conclusions.

Before describing a successful partial erasure, check whether the nested query,
subrequest or execution budget lets that path reach its success response. A
maximum slice may throw first. Report the earlier interruption and the missing
continuation separately rather than asserting that the caller returned success.

Trace retries across every side effect. A deterministic R2 key can overwrite
one object while an additive D1 upsert increments twice. A unique receipt guard
can suppress that narrow duplicate-counter lead, but it does not prove atomic
receipt/counter updates or recovery from a failure between R2 and D1. Check
concurrency, response loss after commit and interruption between each operation.
An R2 conditional write alone does not make a multi-store protocol complete.
Use [R2 conditional operations](https://developers.cloudflare.com/r2/api/workers/workers-api-reference/)
and [R2 operation pricing](https://developers.cloudflare.com/r2/pricing/) as the
source basis; logical deduplication does not erase every billable attempt.

## Admission and credential capabilities

Compare sibling public endpoints that accept the same project or tenant.
Check inherited middleware before calling a local policy difference a bypass.
Trace the first authentication guard and the capability it intentionally grants.
A distinct secret gate can be the intended authentication for an admin or test
operation; a holder using that capability does not demonstrate an authentication
bypass. A checked-in route also does not establish deployed activation. When its
key/configuration is unknown, keep deployment and removal questions conditional.
Confirm a bypass through an unauthorized side effect or a failed independent
expiry/ownership boundary, rather than through the presence of a powerful route.
Origin/CORS and User-Agent checks do not authenticate server senders. Preserve
intentionally public browser ingestion and verify that rejected requests stop
before storage writes. Account-level rules remain uninspected without evidence.

Follow provisioning credentials into runtime secrets. A variable named secret
or a TypeScript credential type is not committed secret material. Conversely,
placing a deployment token in secret storage does not reduce its permissions.
Separate provisioning and runtime read credentials where their capabilities
differ, and verify upgrades preserve the narrower credential. Use
[API token permissions/resources](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/).

## Cost-estimate coverage and local test contracts

Inspect the terms summed into a project's reported total, not only its price
constants. Label measured, assumed, excluded and unknown meters, including
requests rejected before event storage, dashboard/agent executions, replay reads,
retention and the estimator's own queries. Stored-event counts do not determine
query frequency, CPU or billed rows. A separate per-report read estimate does
not put those reads into the monthly overage total.

For an evidenced lake path, account for
[Pipelines transform and sink bytes](https://developers.cloudflare.com/basin-pipelines/platform/pricing/),
[Basin SQL compressed scan bytes and per-query minima](https://developers.cloudflare.com/basin-sql/platform/pricing/),
[catalog operations and enabled compaction](https://developers.cloudflare.com/basin-catalog/platform/pricing/),
plus [R2 storage/operations](https://developers.cloudflare.com/r2/pricing/).
Do not assume compaction is enabled or equate one binding call with one paid event.

Local binding doubles should test the platform contracts used by the diagnosis:
D1 parameter and invocation-query budgets, R2 cursors and truncation, duplicate
delivery and interrupted side effects. Ordinary SQLite success is not proof
of D1 limits. A list returning truncated without a cursor cannot test a second
page. State which limits the reproduction imposed and which it did not test.
