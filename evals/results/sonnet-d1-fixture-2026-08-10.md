# Sonnet fixture spot-check: D1 rows-read coverage (scenario #24)

- Date: 2026-08-10
- Question: do the `CFDOC-EVD-D1-134-BILL` integration changes (war-story scenario #24, scanner leads `CFDOC-COST-D1-NO-INDEXES` and `CFDOC-COST-D1-LAYOUT-HOTPATH`, reference updates in `cost-footguns.md`/`performance-and-reliability.md`) change what a model auditor actually reports?
- Verdict: **yes, on exactly the axis the change targets.** The `ANALYZE`/`sqlite_stat1` planner-statistics lesson appears in 3/3 current-skill audits of the unindexed fixture and 0/6 audits without the change (old skill and no skill). Incident-grounded source basis appears only with the current skill (3/3 vs 0/6). No precision regression on the remediated control (0 false positives in all 9 runs). Token cost is unchanged versus the old skill.

## Protocol

Matched three-way comparison in the style of the GPT-5.5 three-way eval, scoped to the two new detection fixtures, with Claude Sonnet as the auditor model (one fresh subagent per run, no shared context):

- **Cases (2):** copies of `evals/fixtures/detection/d1-unindexed-hot-queries` (bad) and `evals/fixtures/detection/d1-indexed-layout-cached` (remediated control), staged outside the repo with `README.md` and `expected.json` removed and answer-revealing comments stripped ("No secondary indexes anywhere...", "runs for every page...", the control's "Remediated twin..." banner); the table-scale hint was mirrored into both cases for symmetry.
- **Variants (3):** `current` (this branch's `skills/cloudflare-doctor`, scanner 0.3.7), `main` (`origin/main` skill tree, scanner 0.3.6), `none` (no skill). Identical base prompt for all: pre-launch audit, cite files, mechanism, smallest safe fix; ~200,000 page views/month; no network (docs-refresh skipped and disclosed equally); read only the case (and skill) directories.
- **Runs:** 3 per cell = 18 audits. Every audit produced a full report; none failed.
- **Grading:** fixed rubric, deterministic regex first pass (`grade.py` in the run workspace), then an open-label read-through of all 18 answers by the orchestrating model with every regex override checked against quoted text. Not a blind judge — see limitations.

## Results — bad case (`d1-unindexed-hot-queries`)

| Criterion (1 pt each) | current | main | none |
|---|---|---|---|
| Missing indexes tied to D1 rows-read (billed rows scanned, not returned) | 3/3 | 3/3 | 3/3 |
| Layout loader identified as an every-page-view amplifier | 3/3 | 3/3 | 3/3 |
| `ANALYZE`/`PRAGMA optimize`/`sqlite_stat1` planner statistics | **3/3** | **0/3** | **0/3** |
| Recommends caching the every-page data (KV cache-aside / CDN) | 3/3 | 3/3 | 3/3 |
| **Mean score** | **4.0 / 4** | 3.0 / 4 | 3.0 / 4 |

Secondary observations (bad case):

| Observation | current | main | none |
|---|---|---|---|
| Cites the incident as source basis (war story §24 / `CFDOC-EVD-D1-134-BILL` / 127.6B rows) | 3/3 | 0/3 | 0/3 |
| Bundled scanner result on the fixture (reported by the agents) | 2 leads (0.3.7) in 3/3 | 0 findings (0.3.6) in 3/3 | n/a |
| Names the versioned-key KV cache-aside remediation (the incident's actual fix) | 3/3 | 1/3 | 1/3 |

Sonnet is a strong baseline auditor: even with no skill it reliably derives the rows-read billing mechanism, the layout multiplier, and a caching fix from first principles, with credible order-of-magnitude math. What it does not produce without the skill is the planner-statistics step — the incident's second-order lesson ("the planner kept picking bad plans until `ANALYZE` populated `sqlite_stat1`, a further 6.7× reduction") — or any sourced grounding. Representative current-skill fix text: "run `ANALYZE` so the query planner has statistics to actually use them (an index alone doesn't guarantee plan selection until `sqlite_stat1` exists)". The old-skill runs also had to derive the index findings fully manually against a silent 0.3.6 scanner; one explicitly noted "no scanner check ID targets missing-index detection."

## Results — control case (`d1-indexed-layout-cached`)

| Criterion | current | main | none |
|---|---|---|---|
| False positive: claims the composite indexes are missing | 0/3 | 0/3 | 0/3 |
| False positive: claims the nav layout queries D1 uncached | 0/3 | 0/3 | 0/3 |
| Explicitly credits the remediation (indexes + versioned KV cache-aside) | 3/3 | 3/3 | 3/3 |
| Flags the real residual gap (`ANALYZE` documented in a comment but never executed) as a graded finding | 3/3 | 0/3 (2/3 partial, as question/next-action only) | 3/3 |
| Scanner result on the fixture (reported by the agents) | 0 findings | 0 findings | n/a |

Precision holds everywhere. Note the asymmetry on the residual `ANALYZE` gap: the control's migration comment itself names `ANALYZE`/`sqlite_stat1`, so no-skill runs could read the concept off the repo and did; the old-skill runs largely did not grade it. On the bad case — where no comment teaches it — only the current skill supplied the concept at all (3/3 vs 0/6). Current-skill runs additionally sourced the gap to §24 and used the new check IDs as verification instruments ("the scanner's `CFDOC-COST-D1-NO-INDEXES` check ... returned no finding").

## Cost

Mean subagent tokens per audit (3-run mean, from the harness usage records): current ≈137k, main ≈145k, none ≈54k. The known skill-overhead pattern (~2.5× vs no skill) is unchanged, and the scenario-24 additions add no measurable cost over the old skill. Durations 8.5–15.5 minutes per audit, similar across skill variants.

## Incidental yield

Most runs in every variant flagged two unintended fixture artifacts: route params bound to integer surrogate keys instead of joined through `hcpcs_codes`/`states` (a genuine silent-empty-result bug under SQLite type affinity), and the missing Workers Static Assets block for a SvelteKit `main`. Both were symmetric across variants and did not affect the comparison. Both were fixed in the committed fixtures after the runs (joins through the lookup natural keys, unique indexes on `hcpcs_codes.code`/`states.abbreviation` in the control's index migration, `assets` block in both configs); the detection eval remains 28/28 with the bad fixture still emitting exactly the two new leads and the control at zero.

## Limitations

- n=3 per cell; differences of one run are noise. The 3/3-vs-0/6 `ANALYZE` split on the bad case and the 0/9 false-positive rate are the only claims this run supports strongly.
- Grading was open-label by the orchestrating model (regex first pass, quoted-text adjudication), not a blind multi-judge panel like the GPT-5.5 round.
- Auditor agents ran cooperatively inside the same harness and were instructed—not sandboxed—to stay within the staged directories.
- Single auditor model (Sonnet); no cross-model replication in this round.
- Raw run workspaces and full answers stay outside the repository per the eval-artifact convention; this summary quotes only short sanitized excerpts.
