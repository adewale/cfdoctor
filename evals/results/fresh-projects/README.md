# Matched audits on fresh projects

The initial updated skill scored 93.23/100 versus 86.46/100 for pinned main on four real projects outside Dataflare and the existing fixture suite. It won nine matched pairs, lost two and tied one. This is an observed improvement under the primary judge, not a demonstrated general accuracy gain: the project-cluster interval spans zero, the secondary judge finds no mean lift, and updated audits consume more tokens.

Source inspection and the unscored pilot exposed two remaining scanner false alarms, fixed before the full round in `4f53334`. The scored round then exposed a guarded-route reporting regression. Its later correction and focused behavioral verification are reported separately below; the original full-round scores are preserved.

## Design and source pins

- Existing Skill Eval Harness integration: `abd8d7d57aae788658bc293abac1dab80dfb24ac`, the same pin used by `npm run eval:validate`.
- Old skill: `7eefbc7411b634d9a665f9f9240a761f0b2f4314`.
- Full-round candidate: `4f5333468cd853d067016b4c6ab391735ecbafb9`.
- Admission-guidance correction: `09ffa9e88acb78eabc18390902eafefd445dcd74`.
- Four project cases, three repetitions per arm: 24 final answers / 12 pairs. Both arms use native Codex `gpt-5.6-sol`, high reasoning, identical prompts/source/docs/tools, and a 480-second limit. Case/repetition and within-pair order are deterministically shuffled with seed `20261106`.
- Native harness `prepare`, answer backend, normalized traces/telemetry, judge backend and `benchmark` own the run contract. A small workspace-builder extension unpacks raw source bundles without flattening paths. No target code, installer, account command or deployed service was executed.
- Variant labels are hidden from judges. The primary judge is native Codex on the answer model; Claude Sonnet 4.6 scores the predetermined repetition-1 sample. Source-only independent agent reviews adjudicate selected disagreements. None is human validation.

| Project | Pinned revision | Inspected scope |
| --- | --- | --- |
| [llegomark/url-shortener](https://github.com/llegomark/url-shortener/tree/ab83188893cca6feac2d9e26b57ed9ba00268c35) | `ab83188893cca6feac2d9e26b57ed9ba00268c35` | KV-backed API, redirects and configuration |
| [zopiya/bytego](https://github.com/zopiya/bytego/tree/ff21c5b6de9a2b3e5f648139753a73d08ddf6f2a) | `ff21c5b6de9a2b3e5f648139753a73d08ddf6f2a` | R2 upload/delete, browser UI, utilities, tests and example configuration |
| [eidam/cf-workers-status-page](https://github.com/eidam/cf-workers-status-page/tree/f5b49dcae71e12c613b8f00094ed16b735925f64) | `f5b49dcae71e12c613b8f00094ed16b735925f64` | Scheduled checks, KV persistence, notification and cleanup paths |
| [brucehart/web-tools](https://github.com/brucehart/web-tools/tree/f1a09a2e80c9d3bc62786fe06409cad0b118a045) | `f1a09a2e80c9d3bc62786fe06409cad0b118a045` | D1 To-Do/session subsystem; other tools and webhook implementation excluded |

An independent case author selected the last two projects without reading cfdoctor's changes or earlier eval results. Source notes were frozen before answer generation and excluded from answer workspaces. The first two cases and the rubric were authored by the implementation agent. These are fresh visible iteration cases, not independently authored holdouts. Do not count repetitions as independent projects.

## Full-round results

Quality is the mean of four anchored dimensions, normalized from 1–5 to 0–100. The dimensions are primary-mechanism recall, precision, actionable fixes and evidence discipline. Literal headings and finding count earn no credit. A score of 85 is the declared qualitative threshold, not a certificate that every finding is true.

| Measure | Old skill | Initial updated skill |
| --- | ---: | ---: |
| Mean quality | 86.46 | 93.23 |
| Recall / 5 | 4.83 | 5.00 |
| Precision / 5 | 3.83 | 4.17 |
| Actionability / 5 | 4.58 | 4.92 |
| Evidence / 5 | 4.58 | 4.83 |
| Qualitative threshold passes | 10/12 | 11/12 |
| Execution failures | 0/12 | 0/12 |

| Case | Old quality | Initial updated quality | Change, percentage points |
| --- | ---: | ---: | ---: |
| ByteGo | 75.00 | 93.75 | +18.75 |
| Status page | 93.75 | 97.92 | +4.17 |
| URL shortener | 83.33 | 93.75 | +10.42 |
| Web tools | 93.75 | 87.50 | -6.25 |

The paired mean gain is **6.77 percentage points**, with an exhaustive four-project bootstrap 95% interval of **[-2.08, +15.10]** and exact two-sided project-level sign-flip **p=0.375**. Four projects cannot establish a broad benefit. The lower web-tools score triggered a correction rather than being averaged away.

The scored mechanisms include non-atomic KV counters, unpaginated KV listing/fanout, parsing before file-size admission, rejected probes skipping scheduled persistence, cleanup dereferencing a deleted monitor, and unenforced D1 session expiry. Independent ByteGo review found five explicit parse-order explanations and one implicit/partial account, so the primary judge's recall difference should not be read as a completely missed parser concern.

## Scanner corrections and remaining report errors

Across these exact source snapshots, raw scanner leads change from 24 to 12. Six false high credential leads disappear; the three remaining high leads concern KV coordination. Lead counts alone are not an audit-quality score.

The initial PR candidate still flagged a GitHub secret expression in YAML and `AUTH_KEY=replace-with-a-local-dev-key` in documentation. The correction excludes those reference/placeholder forms while retaining literal YAML/documentation credentials. Two negative tests failed before implementation; all 139 unit tests and 53 detection fixtures pass afterward.

Reports still make mistakes. Both skill versions produced an unsupported missing-ignore finding from a selected snapshot despite contrary README intent. Some reports inflated deliberately supported arbitrary-file hosting, recent local-history eviction, or deployment-dependent cache choices into defects. Neither scanner precision nor a passing qualitative score eliminates that need for source review.

## Guarded-route regression and focused verification

The initial updated reports more often presented a separately secret-gated test facility as a high-severity authentication bypass, even while admitting deployed activation was unknown. The source shows an intentional nonempty-key guard. The independent expiry defect remains valid and must be reported separately.

The correction teaches the distinction between exercising an intended capability and crossing an unauthorized boundary. It also separates checked-in route presence from deployed activation. No prompt, source, answer key or rubric was changed to make the correction pass.

The correction was frozen at `09ffa9e` and tested with **eight fresh answers**: three old/new repetitions for web-tools and one old/new ByteGo control pair. Model, reasoning, raw source, supplied docs, prompt, rubric and 480-second budget were unchanged. No previous answer was reused in this focused check.

| Focused measure | Old skill | Corrected skill |
| --- | ---: | ---: |
| Web-tools quality, three reports | 87.50 | 93.75 |
| Web-tools precision / 5 | 3.67 | 4.33 |
| Expiry mechanism detected | 3/3 | 3/3 |
| Unsupported bypass/backdoor labels, blinded source review | 2/3 | 0/3 |
| ByteGo control quality, one report | 81.25 | 100.00 |
| Execution failures | 0/4 | 0/4 |

The corrected reports retain the real expiry and schema problems while distinguishing the key's intended capability. A conditional high-priority capability concern and broad removal recommendations remain in some wording; this is not proof that every severity or remedy is correct. The single ByteGo pair is an adjacent control, not an independent estimate of lift.

This focused result supports the specific correction. **The full four-project suite was not rerun after the guidance edit.** Do not relabel the original 24-answer scores as measurements of `09ffa9e`, pool both rounds, or claim a fresh held-out replication. See `focused-regression-results.json` and the additional blinded review in `independent-adjudication.json`.

## Judge sensitivity and adjudication

On the same eight repetition-1 answers, Claude gives both arms a mean quality of **81.25/100**. Its threshold decisions agree with the primary judge on **3/8** answers; the mean absolute score difference is **12.5 points**. The initial gain is therefore not judge-robust.

Blinded source review found specific secondary-judge errors: correctly registering notifications with `waitUntil` does not disprove an independent missing-delivery-ack path; acknowledging KV consistency does not make concurrent whole-document writers safe. Both status reports supported those mechanisms and did not claim that `waitUntil` cancels main persistence. All raw scores remain unchanged. See `independent-adjudication.json` for evidence and limitations.

The pinned harness's default `compare-judges` lift is null for this old/new-only design, because it expects a with/without contrast. Its resulting `judge_sensitive: false` is not evidence of robustness. The explicit overlapping-answer comparison above and old/new project-cluster analysis are used instead.

## Efficiency and execution accounting

| Full-round measure | Old skill | Initial updated skill |
| --- | ---: | ---: |
| Mean total tokens | 755,909 | 949,195 |
| Median total tokens | 771,285 | 917,048 |
| Mean cached input tokens (subset) | 660,811 | 849,952 |
| Mean uncached input tokens | 81,671 | 85,378 |
| Mean output tokens | 13,427 | 13,865 |
| Mean seconds | 260.1 | 269.2 |
| Median seconds | 249.8 | 275.4 |
| Soft 350,000-token budget passes | 0/12 | 0/12 |

Mean total tokens are about 25.6% higher; uncached input is about 4.5% higher and output about 3.3% higher. Tokens include cached input, which is a subset and must not be added again. Shared-provider load, case ordering and the separate ByteGo correction round limit timing conclusions. Codex dollar telemetry is unavailable. This round does not establish a cost-effective improvement or dollar savings.

The initial 240-second pilot produced two answers, two timeouts and four aborted in-flight calls. It is excluded from quality scoring. The full round uses 18 unchanged answers plus six fresh ByteGo answers after restoring an omitted `cors.json`; all original ByteGo answers were excluded for both arms. This is a disclosed composite, not a fresh full-suite replication. Two unsupported-model probes and three successful adapter probes are separate. Failed/aborted complete usage is unavailable; do not treat it as zero spend.

## Receipts and reproduction

- `full-round-results.json`: all 24 per-run scores, rationales, output hashes, timing, token usage and paired project uncertainty.
- `cross-model-results.json`: the complete preselected eight-answer sensitivity sample.
- `protocol.json`, `source-index.json`, `isolation-receipt.json`: skill/project pins, source/doc hashes, corpus correction and identical prompt/input checks.
- `scanner-comparison.json`: lead counts, separate from report quality.
- `focused-regression-results.json`: eight fresh post-correction results.
- `process-audit.json`: all 24 full-round traces show skill reads and scanner execution; reviewed commands show no network/package runner or target execution.
- `independent-adjudication.json`: blinded source reviews and mappings disclosed after review.

Raw provider traces, all original final answers, invalidated runs, and frozen docs remain locally in `matched-eval-work/` outside the repository. Published run/judge hooks differ from the executed helpers only by import cleanup; the summarizer also accepts an explicit run root and derives expected repetitions from prepared tasks. No third-party project source is vendored.

To reconstruct the experiment in an empty external work directory, check out the pinned harness under `$WORK/harness`, archive each named skill commit into `$WORK/baseline` and `$WORK/candidate`, then run:

```sh
uv run --project "$WORK/harness" python evals/results/fresh-projects/prepare_inputs.py \
  --work "$WORK/round" --baseline "$WORK/baseline" --candidate "$WORK/candidate" \
  --source-cache "$FROZEN_SOURCE_BUNDLES" --docs-cache "$FROZEN_DOCS"
uv run --project "$WORK/harness" python "$WORK/harness/skill_benchmark.py" validate \
  "$WORK/round/manifest.json" --strict-leakage --leakage-min-chars 1
uv run --project "$WORK/harness" python "$WORK/harness/skill_benchmark.py" prepare \
  "$WORK/round/manifest.json" --split tune --include-old-skill --runs-per-variant 3 \
  --models gpt-5.6-sol --out "$WORK/round/tasks.jsonl"
uv run --project "$WORK/harness" python "$WORK/run_round.py" "$WORK/round"
uv run --project "$WORK/harness" python "$WORK/judge_round.py" "$WORK/round" codex
uv run --project "$WORK/harness" python "$WORK/harness/skill_benchmark.py" benchmark \
  "$WORK/round/manifest.json" --runs "$WORK/round/runs" --split tune \
  --variant with_skill --variant old_skill \
  --judge-results "$WORK/round/codex-judge-results.jsonl" --out "$WORK/round/benchmark.json"
python "$WORK/summarize_round.py" "$WORK/round"
```

Without caches, the input preparer fetches immutable public source and official docs, verifies every hash, and fails on document drift. Frozen docs are not publicly vendored; exact historical reconstruction needs the preserved cache. The focused correction uses the same harness with its separately recorded task selection. A future run is stochastic and will not reproduce answer bytes.

For the focused check, pass `--manifest-template regression-manifest-template.json` to the input preparer, prepare three repetitions, then retain all web-tools rows and only ByteGo run 1. The admission reference is the only installable-skill file changed after the full round. The published protocol verifies that the focused snapshot matches the latest installable skill byte-for-byte.
