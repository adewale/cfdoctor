# Private archive pagination audit

The smallest supported change is to replace offset pagination with a cursor over `(created_at, id)`, retaining D1, the existing covering index, and the 20-row page size. The supplied deep-page sample reads **501×** as many rows as the first-page sample while returning the same 20 rows. This confirms a per-request read-cost mechanism; it does not establish total usage, charges, or a measured latency problem.

Scope inspected: Only the supplied `README.md`, `wrangler.jsonc`, `index.js`, and `evidence.txt` under `private-d1-offset`; Cloudflare Doctor guidance and its D1 diagnosis reference; environment networking guidance; the two official pages below. Static, read-only review; no scanner, D1 execution, account calls, installs, or implementation changes.

Scope not inspected: Deployment/account settings, production traffic, billing plan/window, invocation counts, actual latency, other databases, and historical invoices. The supplied archive is synthetic and undeployed. Authentication precedes database work; the anonymous public-route release gate does not apply.

Docs refreshed: 2026-10-18 — [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/) and [Use indexes](https://developers.cloudflare.com/d1/best-practices/use-indexes/), successfully retrieved through the web tool. No remaining docs-access limitation.

Cost paths:

| path / trigger | frequency / window | queries / execution | rows read / query | rows written / query | evidence / unknowns | first enforced bound |
| --- | --- | --- | --- | --- | --- | --- |
| Authenticated `GET /archive?offset=0`, explicit click | Unknown in any period | 1 | 20, supplied sample | 0, supplied sample | `index.js:13`; `evidence.txt:14,17–20` | Authentication and offset validation before D1; no period/request-count bound supplied |
| Same route, `offset=10000`, explicit click | Unknown in any period | 1 | 10,020, supplied sample | 0, supplied sample | `evidence.txt:10–15`; same covering-index plan | Offset capped at 10,000 before D1; `LIMIT 20` bounds returned rows, not reads to 20 |
| Same route, other accepted offsets | Unknown in any period | 1 | Unknown; no samples for these offsets | 0 for this read-only statement | `index.js:9–14`; do not extrapolate exact measured units | Same authentication/offset cap; repeat requests remain possible |
| Missing/invalid credentials, wrong method/path, malformed/negative/excessive offset | Unknown in any period | 0 | 0 | 0 | `index.js:4–12`; `evidence.txt:18–19` | Rejected before D1 |

There is no evidenced background loop, cron, or retry path. For a matching period and unchanged sampled query/data conditions, the sample-based read model is `N₀ × 1 × 20 + N₁₀₀₀₀ × 1 × 10,020 + Σ(other-offset executions × 1 × their measured rows_read)`. Every invocation count and the other-offset measurements are unknown, so aggregate reads are unknown. This SELECT contributes zero row writes; unrelated writes and storage are outside scope. Samples are not future worst-case bounds. One owner and the offset cap do not bound total executions.

## Severity: Medium — Deep OFFSET pages amplify D1 reads

- **Category:** Cost footgun.
- **Evidence:** [index.js:13](/workspace/cfdoctor/evals/fixtures/benchmark/private-d1-offset/index.js:13) executes one `LIMIT 20 OFFSET ?` query per accepted request. [evidence.txt:5](/workspace/cfdoctor/evals/fixtures/benchmark/private-d1-offset/evidence.txt:5) supplies the existing `(owner_id, created_at DESC, id DESC)` covering index; lines 10–15 show `SEARCH ... USING COVERING INDEX`, 10,020 reads at offset 10,000 versus 20 at offset zero, and zero writes in both samples. This is indexed prefix skipping, not evidence of a missing index or full-table scan.
- **Why it matters:** D1 meters rows read, rather than rows returned. Advancing the offset makes this evidenced query consume more read units even with a fixed page size and a single authenticated user. The samples explain why older-page browsing can raise usage; absent matching request counts and billing evidence, they cannot identify the historical bill's cause or quantify a charge.
- **Fix:** Use the last displayed row's **both** `created_at` and unique `id` as the next cursor. Keep `owner_id` derived from the authenticated owner. For subsequent pages, use the candidate query below; omit the cursor predicate on the first page. Bind and validate cursor values before querying. Return a cursor from the last displayed row; stop on an empty/short page. Preserve the existing traversal-depth policy with a separate validated page/depth guard if that cap is intentional. Keep the existing index; no schema migration is supported by this evidence.

  ```sql
  SELECT id, created_at
  FROM archive
  WHERE owner_id = ? AND (created_at, id) < (?, ?)
  ORDER BY created_at DESC, id DESC
  LIMIT 20;
  ```

  The strict composite cursor preserves the descending tie-break order when timestamps repeat. The seek predicate is the proposed optimization; its actual D1 read units still require verification.

- **Cost / trade-off:** Expected benefit is avoiding repeated reads of earlier index entries. This is a small query/response/client-navigation change with no additional index-write or storage overhead. Numeric-offset links must change; direct page-number jumps become less convenient. Cursor pagination does not provide a frozen snapshot under arbitrary record edits. No dollar savings or exact post-change read bound can be claimed from these samples.
- **Verify:** On equivalent local/staging data, compare first and deep-page `EXPLAIN QUERY PLAN` output and D1 `meta.rows_read`/`meta.rows_written` before and after. Confirm the new plan seeks through the existing index, deep-page reads stay near the returned-page scale rather than following prior depth, and writes stay zero. Check tied timestamps, empty/final pages, invalid cursors, and insert/delete behavior between clicks. Local SQLite plans alone cannot establish D1 billed-row units. To attribute the reported period, the smallest additional evidence is page-depth/request counts and matching database read totals for that window; charges additionally require plan/allowance and billing-window details. No production replay is requested.
- **Source basis:** [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/) establishes row-read/write meters, `meta` measurement, index-write overhead, and plan-dependent billing windows. [Use indexes](https://developers.cloudflare.com/d1/best-practices/use-indexes/) supports filtering through the existing multi-column index and verifying the plan and measured units. The exact composite seek query is a recommendation derived from the supplied schema and ordering, pending that verification.
- **Confidence:** High in the sampled OFFSET read amplification and the minimal query-level direction; aggregate impact and post-change D1 units remain unmeasured.
