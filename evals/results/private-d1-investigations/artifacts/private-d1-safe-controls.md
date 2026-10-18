The supplied evidence does **not establish the same D1 cost problem**. The reason is the bounded query work and supplied server-side admission contract, rather than having only one user. This is a synthetic, evidence-only conclusion; it does not establish the live application's safety or explain an actual bill.

Scope inspected: `README.md:1–5`, `wrangler.jsonc:1–8`, `index.js:1–47`, and `evidence.txt:1–34` in the supplied `private-d1-safe` directory; the Cloudflare Doctor skill and its D1 bill-diagnosis reference. No queries or application code were executed.

Scope not inspected: deployed routes, the imaginary gate's implementation or deployment, session issuance, account plan and allowances, usage totals, invoices, storage bytes, other databases, or other application/background/admin paths. No production/account calls, installs, or implementation changes.

Docs refreshed: [official D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/), fetched 2026-10-18. No documentation-access limitation encountered. D1 meters rows read and rows written, with storage separately; query count and returned-row count do not substitute for these meters. The account's applicable allowance and billing window are unknown.

Cost paths:

| path / trigger | frequency / window | queries / execution | rows read / query | rows written / query | evidence / unknowns | first enforced bound |
| --- | --- | --- | --- | --- | --- | --- |
| Admitted `GET /dashboard`: summary count | Client polls immediately, then every 60 seconds while visible; at most 60 client calls and a one-hour local stop. Contract admits at most 60 calls per session lifetime across clients. | 1 | 1, supplied sample | 0, supplied sample | `index.js:2–18,43`; `evidence.txt:5–13,19–34`. `SCAN` covers a table constrained to at most one row; it is not a scan of all notes. | Before D1: authenticated owner admission, atomic 60-slot quota and fixed session expiry, **under the supplied test-double contract**. |
| Same admitted request: note lookup for fixed `id=1` | At most once after the summary query completes, within the same admissions | 1 | 1, supplied sample | 0, supplied sample | `index.js:44`; `evidence.txt:7–8,15–17`. Supplied plan uses the integer primary key despite 50,000 notes. Samples are not formal future row maxima. | Same pre-D1 admission; then fixed-key primary-key lookup. |
| Missing credentials, rejected/expired/exhausted session, gate failure, wrong method/path | Incoming attempt count unknown | 0 D1 queries | 0 | 0 | `index.js:23–42`; gate semantics supplied at `evidence.txt:19–28`. Gate/Worker charges are unknown and are not included in the D1 row model. | Route/header checks or fail-closed gate rejection, before either SQL statement. |

For `A` admitted requests where both queries complete at the supplied sample costs:

- Read exposure = `A × 1 × 1 + A × 1 × 1 = 2A` rows.
- Write exposure = `A × 1 × 0 + A × 1 × 0 = 0` rows.
- At 60 admissions, that models **120 rows read and zero rows written per session**, across at most 120 statement executions. This is a sample-based projection, not observed account usage or a guaranteed future row ceiling.

The server contract supplies the meaningful admission bound. Client visibility and timers alone would not bound direct requests or multiple tabs. Calls can overlap because polling does not await completion, but the supplied atomic cross-client quota still caps admissions for that session. No explicit retry loop is supplied. New sessions can multiply lifetime work: for `S` sessions, the same full-session sample scenario is `120S` read rows; `S` and the account-window total are unknown. Rejected attempts can still invoke the gate. Neither a service binding nor the fixture name proves a deployed quota or any particular gate billing behavior.

No anonymous D1 execution path is evidenced, so a public-route release verdict is not applicable. `workers_dev: false` is not evidence of deployed hostnames or account access policy.

**No confirmed findings.** No query, index, cache, or product change is justified by these supplied plans, schema, samples, and contract. To reassess a real usage anomaly, the smallest useful evidence would be the deployed gate's enforcement/session-issuance evidence, admitted execution counts and D1 row totals for the relevant database/window, plus the matching redacted invoice meters and plan. The synthetic evidence cannot identify a historical bill's cause.
