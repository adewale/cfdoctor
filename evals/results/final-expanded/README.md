# Final skill: expanded matched evaluation

This round tests the installable skill at `769182a23e5acb67369dc240a88c54e75d2f9477` against baseline `7eefbc7411b634d9a665f9f9240a761f0b2f4314`. All reports are freshly generated; none is reused from the earlier mixed-version or focused rounds. Later evidence-only commits preserve this tested skill tree byte-for-byte.

## Result

Hold PR #36. The scanner has a verified improvement, but the expanded matched run does not establish better audits with the whole skill. Codex scores old/final at 82.42/81.77; Claude scores 71.09/76.56. Both score recall higher, while precision and evidence move in opposite directions across judges. The fresh-project slice does not resolve the disagreement. Required code checks pass.

This is an assessment of the unchanged final skill, not another tuning iteration. No installed skill or scanner changed during this round. The next change should address the reporting errors verified against source below and be evaluated against new source cases before declaring an audit-quality improvement.

## What was tested

Eight pinned public source projects, three paired repetitions each, yield 24 old/final pairs and 48 reports. Four projects were used in the earlier evaluation and tuning. Four new projects were selected and annotated by independent authors who had not read cfdoctor, its patch or prior audit reports. New source and non-exhaustive ground truth were frozen before generation. No target code, installer, test suite, deployed endpoint or account was executed.

| Slice | Project | Added coverage |
|---|---|---|
| Previously evaluated | llegomark/url-shortener | KV counters, rate limits, enumeration |
| Previously evaluated | zopiya/bytego | R2 upload/body limits, guarded writes |
| Previously evaluated | eidam/cf-workers-status-page | scheduled KV state, failure handling |
| Previously evaluated | brucehart/web-tools | D1 sessions/expiry, owner-scoped To-Do API |
| New | grunt-it/hookrelay | Queues, KV visibility, ingress recovery, DO circuit state |
| New | cloudflare/workers-chat-demo | WebSocket hibernation, lifecycle, capability controls |
| New | A-Archives-and-Forks/pastebin-worker-d1 | D1/KV migration and administrator tooling |
| New | Quaint-Studios/reia-lfs-cloudflare-worker | R2 content integrity, Git LFS Batch protocol |

Pins, delivered scope and SHA-256 hashes are in `source-index.json` and `protocol.json`. The chat and webhook snapshots are complete repositories. Pastebin excludes standalone client scripts and its dependency lockfile; supplied frontend styling/TOS files are delivery context outside the audit scope. Web-tools remains an explicitly scoped subsystem snapshot. Missing files outside those scopes are not defects.

Answers use the existing Skill Eval Harness native Codex adapter, pinned at `abd8d7d57aae788658bc293abac1dab80dfb24ac`, with `gpt-5.6-sol`, high reasoning, 480 seconds per report. The adapter uses ephemeral Codex homes, ignores ambient user config/rules and runs the selected skill read-only. Six pair workers run in randomized order with seed 20261107; arm order is randomized within each pair. This is a concurrency 6 evaluation, so elapsed comparisons with earlier concurrency 4 runs are descriptive.

Each workspace contains one selected skill, raw `project/`, pin metadata, and identical frozen official documentation for that case. Expected answers and scoring notes are not mounted. The old/final rendered prompts match byte-for-byte for all 24 pairs. `isolation-receipt.json` records the preflight check; it does not prove provider cache independence or OS-level read confinement.

A protocol correction removes the serialized `.project.json` fixture after unpacking it. The earlier workspace exposed that bundle and the raw source simultaneously, and traces show both were read. The new raw-only mount is applied to both arms. Comparisons with historical token totals therefore combine a mounting change, a skill change, a different sample and fresh provider state; they cannot isolate a causal saving from the mount correction.

## Quality and disagreement

The Claude judging pool increased from 2 to 4 after 30 answers to reduce queueing; active calls finished unchanged, Codex stayed at 2, and prompts/models/rubrics/sample did not change. `judge-scheduling-change.json` records the only source difference.

Both the native Codex judge (`gpt-5.6-sol`) and Claude judge (`claude-sonnet-4-6`) score every report with strict native JSON schemas. Variant labels, repeat numbers and run directories are hidden; raw source, the same official snapshots and non-exhaustive author notes are supplied. Report content itself can disclose scanner versions or style, so this is label blinding rather than proof of perfect anonymity.

The four anchored 1–5 dimensions are recall of primary source mechanisms, precision, actionability and evidence. The reported 0–100 score is their mean after mapping each dimension with `(score-1)/4`. It is a rubric score, not a percentage of project bugs found. More findings, longer reports and labels do not earn credit. Additional source-supported findings are accepted; control notes establish only the invariant they discuss. A 0.85 quality threshold and 480-second/350,000-token budgets remain soft assertions.

| Judge | Old | Final | Change | 95% case interval | Pair wins/losses/ties | Quality passes old/final |
|---|---:|---:|---:|---|---|---|
| Codex | 82.42 | 81.77 | -0.65 | [-5.99, +4.30] | 9/11/4 | 13/24 → 12/24 |
| Claude | 71.09 | 76.56 | +5.47 | [+0.00, +10.68] | 13/5/6 | 6/24 → 8/24 |

| Project | Codex change | Claude change |
|---|---:|---:|
| url-shortener | -14.58 | +0.00 |
| bytego | +10.42 | +16.67 |
| status-page | +6.25 | +8.33 |
| web-tools | -2.08 | +4.17 |
| hookrelay | +5.21 | -8.33 |
| workers-chat-demo | -2.08 | +2.08 |
| pastebin-d1 | -4.17 | +6.25 |
| reia-lfs-r2 | -4.17 | +14.58 |

| Slice | Codex old → final | Claude old → final |
|---|---:|---:|
| Previously evaluated four | 90.10 → 90.10 | 76.04 → 83.33 |
| New four | 74.74 → 73.44 | 66.15 → 69.79 |

The exact two-sided case sign-flip p-values are 0.852 for Codex and 0.125 for Claude. The Claude interval touches zero; neither result establishes a general improvement. Threshold agreement is 29/48 reports; mean absolute score disagreement is 13.35 points. These numbers describe this curated sample, not a bug-detection accuracy rate.

Recall rises 4.31→4.58 for Codex and 3.92→4.17 for Claude. Codex precision falls 4.00→3.79 and evidence falls 4.33→4.13; Claude precision rises 3.63→3.88 and evidence rises 3.96→4.25. Judge disagreement prevents a single confident quality claim.

Statistics pair reports by project/repetition. Project means are the uncertainty unit; repetitions do not count as 24 independent projects. The report includes 50,000 fixed-seed case-cluster bootstrap samples and an exact two-sided sign-flip test. Eight selected projects are too few to establish broad general accuracy. Previously evaluated and new projects are reported separately; the new cases are independently authored evidence, not an unseen independent grader or a permanent holdout.

Independent authors reviewed all 48 opaque reports against pinned source before receiving arm identities. Report hashes match the executed outputs. Their full notes, controls, quoted errors, additional valid findings and explicit author erratum are in `independent-source-review.json`. These are agent source reviews, not maintainer approval or runtime proof.

- Every chat report misses the pending unnamed socket losing initial history/roster on hibernation. Other valid memory/timer/admission findings do not substitute for that mechanism. This is a shared blind spot: 0/3 old and 0/3 final.
- Hookrelay ingress deduplication, failed enqueue recovery and half-open probe defects are found in all six reports. The stale-KV-miss/final-ack loss is found in 2/3 per arm. The final version retains those source mechanisms overall.
- URL-shortener reports from both arms confuse Free external-subrequest and internal KV budgets, or report 500 where the redirect catch returns 404. Auth/rate-limit/metadata ordering and conditional cache hits also need exact tracing.
- Policy and deployment overreach remains: optional public uploads, manual configuration, documented retention and powerful secret-gated operations need their stated contract before being called security defects. Proposed fixes/tests sometimes change that contract.
- Several status-page diagnoses are correct while literal `continue` patches inside `.map()` callbacks are invalid. One report misses the cleanup dereference itself. Good diagnosis and valid remediation are separate checks.

The judges also make factual mistakes. For example, Codex gives all three old URL-shortener reports perfect scores even though independent source review identifies status/budget errors; Claude rationales sometimes repeat those errors. The point scores are therefore secondary evidence alongside source adjudication. No manual score replacements were made.

Two source-only clarifications were applied uniformly to both arms: the Pastebin API/README deletion-contract conflict and the status-page callback remedy. All 12 affected reports were rejudged by both backends, preserving 24 initial judgments. Before these corrections, Codex lift was −1.69 points and Claude lift +4.69; after correction they are −0.65 and +5.47. The disagreement is present in both analyses. See `oracle-corrections.json` and `oracle-correction-sensitivity.json`. Additional valid expiry-authentication findings remain in source review; they do not turn an unmeasured deployment consequence into proof.

A manifest authoring error also used 0.85 where anchored dimensions expect a raw 1–5 threshold. Native merging clipped it to 0. The intended normalized 0.85 gate is raw 4.4. This metadata was corrected and native aggregation rerun; the reported dimension scores, quality means and deltas never depended on those original pass labels and do not change. The corrected native gate exactly matches the independently computed threshold counts above. `harness-threshold-correction.json` preserves the error and correction; judge dimension ratings were not regenerated for this metadata fix.

## Token overhead

| Per-report mean | Old | Final | Change |
|---|---:|---:|---:|
| Total tokens | 717,983 | 660,147 | -8.06% |
| Cached input | 631,493 | 572,160 | -9.40% |
| Uncached input | 72,584 | 74,435 | +2.55% |
| Output | 13,905 | 13,552 | -2.54% |
| Elapsed seconds | 267.82 | 259.55 | -3.09% |
| Commands | 25.17 | 27.50 | +9.27% |
| Returned command characters | 370,701 | 406,799 | +9.74% |

The earlier 25.6% total-token overhead did not reproduce. The final matched estimate is −8.06% total tokens, with a descriptive 95% case-cluster interval of [−23.29%,+8.12%]. Uncached input rises 2.55% (interval [−1.54%,+6.83%]); elapsed falls 3.09% (interval [−6.66%,+0.81%]). The data do not establish a stable reduction or increase in cost. Provider caching is not independently controlled.

All 48 reports exceed the original soft 350,000-token budget; all 48 meet the 480-second budget. Execution success is not an overall eval pass. Resource totals cover answer generation only; judge calls are separate. Input is cumulative across model/tool turns, not one context window. `overhead-uncertainty.json` and `final-population-review.json` contain case/slice details and independent accounting.

Native `turn.completed` usage is checked against run metadata. Every accepted report must have exactly one terminal usage record, a nonempty final answer and successful status; the population must match all 48 prepared identities. Cached input is a subset of input. Reasoning output is a subset of output. Neither is added a second time. Codex supplies no dollar-cost telemetry here.

The prior 24-report comparison showed total tokens +25.57%, uncached input +4.54%, output +3.26%, elapsed +3.52%. Cached input accounted for 98.08% of the additional input. Candidate command count fell 27.5% and returned command characters fell 3.43%, so the aggregate traces do not support attributing the input increase to a particular reference. They lack per-call effective context and file-level token attribution. The final main skill is 1,419 bytes larger; references are 13,450 bytes larger in total, including the new 10,484-byte workload reference. Those byte counts do not explain cumulative model input by themselves.

Independent overhead validation found a historical diagnostic error: a loose `truncat` search counted ordinary R2 `truncated` properties and prose as clipped output (10 baseline/29 candidate hits). Strict observable clipping-marker counts are 0/0. The original result is retained with this correction; zero markers do not prove there was no hidden transport/context clipping.

## Scanner and required checks

The rerun preserves 30/30 legacy fixtures in both versions and improves workload fixtures 10/23→23/23: 40/53→53/53 total. All 139 unit tests, 43 trigger cases, self-scan, coverage/claim-ledger/link-policy/install-boundary checks and pinned harness validation pass. Final packaging checks are recorded in `required-checks.json`.

Across the eight raw snapshots the scanner emits 42→24 leads, high severity 12→4. Source inspection confirms eight removed high credential alarms were type/computed/CI/example values rather than usable credentials. Three retained high KV-coordination leads are real source patterns; the remaining high lead is a synthetic form-data-test secret, scoped as test code. A terminal-DLQ consumer still triggers a shared no-DLQ lead. These residuals require source review; lead counts are not report precision.

Observable command review finds skill reads and no candidate target-execution, network-command or external-home-path commands in all 48 traces. Heuristic command screening does not prove OS confinement. Target applications were not run.

Scanner lead counts are unadjudicated heuristic output, not an audit score. The expanded comparison preserves per-project IDs/counts so reductions can be checked against source. Shared blind spots and pre-existing false leads are named explicitly in the findings review rather than treated as final-skill regressions.

## Reproduce

Use the repository's existing shared-harness hooks and pinned native adapters. `prepare_inputs.py` fetches immutable source and verifies recorded hashes; frozen source/docs caches avoid network access. Live docs drift fails closed. Do not substitute changed docs and call it the same evaluation.

```sh
# Provide immutable old/final checkouts with the skill trees recorded in protocol.json.
python3 evals/results/final-expanded/prepare_inputs.py \
  --work /tmp/cfdoctor-final-eval \
  --baseline /path/to/old-checkout --candidate /path/to/final-checkout \
  --source-cache /path/to/frozen-inputs --docs-cache /path/to/frozen-inputs
# Put the exact harness checkout/archive at /tmp/cfdoctor-final-eval/harness.
python /tmp/cfdoctor-final-eval/harness/skill_benchmark.py validate \
  /tmp/cfdoctor-final-eval/manifest.json --strict-leakage --leakage-min-chars 1
python /tmp/cfdoctor-final-eval/harness/skill_benchmark.py prepare \
  /tmp/cfdoctor-final-eval/manifest.json --split tune --include-old-skill \
  --runs-per-variant 3 --models gpt-5.6-sol --out /tmp/cfdoctor-final-eval/tasks.jsonl
python /tmp/cfdoctor-final-eval/preflight.py
python /tmp/cfdoctor-final-eval/run_round.py /tmp/cfdoctor-final-eval
python /tmp/cfdoctor-final-eval/apply_oracle_addenda.py /tmp/cfdoctor-final-eval
python /tmp/cfdoctor-final-eval/judge_round.py /tmp/cfdoctor-final-eval codex
python /tmp/cfdoctor-final-eval/judge_round.py /tmp/cfdoctor-final-eval claude
python /tmp/cfdoctor-final-eval/summarize.py
python /tmp/cfdoctor-final-eval/overhead_uncertainty.py /tmp/cfdoctor-final-eval
python /tmp/cfdoctor-final-eval/harness/skill_benchmark.py benchmark \
  /tmp/cfdoctor-final-eval/manifest.json --runs /tmp/cfdoctor-final-eval/runs \
  --split tune --variant old_skill --variant with_skill \
  --judge-results /tmp/cfdoctor-final-eval/codex-judge-results.jsonl \
  --out /tmp/cfdoctor-final-eval/native-codex-benchmark.json
```

Use an environment with the pinned harness dependencies and authenticated Codex/Claude CLIs. `native-harness-receipts.json` records both native `benchmark` runs, gate counts and full-report hashes; complete native reports remain in the local run archive. Process receipts and summary JSON are included. All assertions here are soft, so the native hard-gate combined mean is null. The portable preflight omits the original private acquisition-builder hash; its raw-byte and prompt-isolation checks are unchanged. The old/new-only design has no `without_skill` arm; do not interpret the native `compare-judges` default null lift as judge agreement. Raw provider traces and third-party source/docs caches remain outside Git; final-answer hashes, usage, scores, rationales, pins and reconstruction hooks are committed.
