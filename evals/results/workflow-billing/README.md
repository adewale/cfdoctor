# cfdoctor Workflow billing evaluation

Run date: 2026-10-18. This receipt measures the local billing-guidance patch against immutable main; test-suite success is not treated as proof of behavioral lift.

## Protocol

- Harness: Skill Eval Harness v0.6.0, pinned to abd8d7d57aae788658bc293abac1dab80dfb24ac.
- Baseline: 5fb7d995b3409522bc7b4551ebff58543e1cb978.
- Three variants, ten cases, three repetitions per variant. The study made 108 answer calls: a 90-answer pilot plus 18 reruns after clarifying two questions. The final 90-answer comparison combines 72 unchanged pilot answers with those 18 fresh answers; it is not a fresh full-suite replication. Variant order is deterministically shuffled within each case/repetition over four answer shards.
- Model: isolated Codex CLI default, resolved by a successful startup diagnostic to GPT-5.6 Sol, high reasoning. CLI version 0.145.0. Per-run JSON traces omit the selected model ID.
- Six new cases receive identical official-doc snapshots captured on 2026-10-18; four existing controls retain their original live-doc process.
- Typed billing worksheets are checked deterministically. Blinded primary judgments use the same native Codex backend and 0.85 threshold. Sonnet independently judges run 1 for all three variants.
- Generation and judging overlap. Uncertainty clusters repetitions by case.

Execution errors: 0; missing outputs: 0. Unsupported-model infrastructure probes are excluded from these 90 answers.

## Measurement correction

The pilot appeared to favor the updated skill: 17/18 worksheets passed versus 15/18 for main and 15/18 without the skill. Manual review found all numerical values correct in all three variants (18/18 each). Seven apparent misses came solely from undefined `retry_work_free` / `rollback_work_free` flags. Every flagged answer explicitly scoped free to the step meter and separately warned about CPU or downstream costs. These were not seven demonstrated billing mistakes.

We preserved the pilot and its original oracle, replaced those fields with separate extra-step-fee and CPU/downstream-zero-guarantee fields, and reran both affected cases across all variants and repeats. The runtime skill and the other eight case prompts were not changed. Results below use this disclosed composite dataset. This correction improves measurement, not the measured skill.

## Six Workflow billing cases

| Variant | Correct worksheets | Qualitative passes | Mean objective gates | Median tokens | Median seconds |
|---|---:|---:|---:|---:|---:|
| Updated skill | 18/18 | 18/18 | 100.0% | 90,562 | 57.5 |
| Pinned main | 18/18 | 18/18 | 100.0% | 88,912 | 65.3 |
| No skill | 18/18 | 18/18 | 100.0% | 31,200 | 27.3 |

| Case | Updated worksheet passes | Main worksheet passes | No-skill worksheet passes |
|---|---:|---:|---:|
| workflow-application-retry-billing | 3/3 | 3/3 | 3/3 |
| workflow-builtin-retry-billing | 3/3 | 3/3 | 3/3 |
| workflow-retention-cohort | 3/3 | 3/3 | 3/3 |
| workflow-rollback-billing | 3/3 | 3/3 | 3/3 |
| workflow-storage-daily-peak | 3/3 | 3/3 | 3/3 |
| workflow-wait-invocation-billing | 3/3 | 3/3 | 3/3 |

The worksheet oracle verifies values and arithmetic. Qualitative judgments separately assess source interpretation, retention cohorts/overrides, unnecessary fixes, and contradictory prose.

## Existing controls

| Variant | Mean objective gates | Qualitative passes |
|---|---:|---:|
| Updated skill | 55.4% | 9/12 |
| Pinned main | 66.7% | 9/12 |
| No skill | 53.3% | 6/12 |

Controls cover Workflow fan-out, safe Queue/DLQ behavior, compound billing with missing inputs, and pricing-effective-date conflicts. Some inherited gates check skill output format; lower no-skill format scores alone do not demonstrate better billing decisions.

## Efficiency

| Variant | Mean tokens | Median tokens | Mean seconds | Median seconds | Budget checks passed |
|---|---:|---:|---:|---:|---:|
| Updated skill | 158,305 | 104,094 | 70.2 | 65.0 | 36/60 |
| Pinned main | 127,707 | 105,843 | 70.2 | 67.9 | 37/60 |
| No skill | 62,783 | 31,355 | 36.8 | 29.3 | 50/60 |

Tokens include cached input. Dollar-cost telemetry is unavailable; these are efficiency proxies.

## Paired uncertainty

- workflow, updated versus main: +0.00 percentage points; case-cluster bootstrap 95% interval [+0.00, +0.00]; exact sign-flip p=1.0000; 6 case clusters.
- controls, updated versus main: -11.25 percentage points; case-cluster bootstrap 95% interval [-31.25, +6.67]; exact sign-flip p=0.5000; 4 case clusters.

The zero-width empirical billing interval reflects six saturated cases; it does not prove equivalence on other workloads.

## Cross-model judge sensitivity

Primary/Sonnet pass agreement on run 1: 27/30 (90.0%). Mean absolute score difference: 0.071. This measures judge sensitivity, not human alignment.

## Interpretation

The updated skill does not improve the observed worksheet pass count versus pinned main on these cases. This round does not establish a billing-accuracy lift from the added guidance. Assess qualitative differences and efficiency overhead before keeping additional prose.

Both skill variants pass 9/12 qualitative control judgments; no skill passes 6/12. Updated control objective gates are lower (55.4% versus 66.7% for main), with a wide case-cluster interval spanning zero. Failure inspection found lexical false negatives: an answer that explicitly capped in-flight work missed a bounded-concurrency synonym regex; another correctly explained unknown D1 rows and refused an exact dollar total but missed the inherited phrasing patterns. Other omissions are real rubric concerns, including at-least-once/idempotency caveats and incomplete treatment of a synthetic historical-rate conflict. These controls should not be silently repaired or interpreted as established regression from the billing patch.

The whole-suite mean token count is about 24% higher than main, while medians are similar and mean latency is almost identical. The narrow billing slice does not show the same mean-token increase. With ten case clusters and noisy shared-run timings, neither efficiency improvement nor a stable overhead estimate is established.

Recommendation: retain the factual doc alignment, strengthened source-drift checks, and new regression cases, but do not market this as a demonstrated answer-quality improvement. Do not add further skill prose based on this saturated benchmark. A separately authorized next experiment would use independently authored, less signposted code-review cases and account-meter reconciliation; this run does not establish a full release gate.

## Limitations

- Same author wrote changes and eval cases.
- Two withheld prompts are not independently authored holdouts.
- Controlled docs may make the baseline already correct, reducing discrimination.
- Live browsing remained available; snapshots standardize supplied evidence, not every source acquired during execution.
- CLI default model resolved with startup diagnostic; per-run JSON traces omit model ID.
- Dollar costs are unavailable; reported token totals include cached input.
- Only ten cases; repeats are clustered by case for uncertainty.
- Reference-name commands indicate read/search attempts, not proof of full consumption.
- Final comparison is a disclosed composite of 72 unchanged pilot answers and 18 clarified reruns; not a fresh full-suite replication.
- Judge assertions use the harness soft-score channel; threshold pass counts here are computed from recorded judge verdicts, not its gated qualitative rate.

## Validation and evidence

- Repository checks: 110 unit tests, 43 trigger cases, 30 detection fixtures, coverage/ledger checks, and install-boundary validation pass.
- Offline source-drift minimal pairs: old anchor policy misses 3/3 simulated changes; updated policy flags 3/3 (removing retry/rollback exclusion, replacing daily-peak averaging, and changing the new-definition retention default). Both policies accept the captured documents. This demonstrates guard coverage, not model-answer lift or detection of every possible documentation change.
- Publication readiness: lint-only regex-alias/import edits made no runtime-skill change; all 90 preserved answers were regraded with the final oracle. Publication copies of one doc snapshot and selected answers have trailing whitespace removed for the repository diff gate; original captured/answer bytes and hashes remain in local raw artifacts. The drift regression test fails as expected when the baseline policy is substituted in a temporary fixture tree.
- Strict manifest/leakage validation, seven ablation application checks, and audit-manifest preflight pass with no blockers.
- Skill/input hashes, CLI identity evidence, per-run grades, reference-read/search evidence, and sanitized judge results are retained with local artifacts.
- The generic skill-creator validator rejects the existing, unchanged compatibility frontmatter field; this is separate from repository checks.

Process guidance used: the `skill-creator` skill supplied the failure-review/refinement discipline; `openai-docs` supplied the isolated Codex CLI configuration guidance. The repository's pinned shared-harness process remained authoritative for this run.

## Reproduce

Supply the two private holdout prompts, materialize baseline commit `5fb7d995b3409522bc7b4551ebff58543e1cb978` outside the working tree, and freeze the current skill in a separate directory. Use the pinned harness above. Set `/tmp/workflow-billing-eval/manifest.json` with:

```sh
python3 scripts/focus_workflow_billing_eval.py --baseline /tmp/cfdoctor-main --current /tmp/cfdoctor-current --out /tmp/workflow-billing-eval/manifest.json
skill-benchmark validate /tmp/workflow-billing-eval/manifest.json --strict-leakage --leakage-min-chars 1
skill-benchmark prepare /tmp/workflow-billing-eval/manifest.json --include-old-skill --runs-per-variant 3 --out /tmp/workflow-billing-eval/tasks.jsonl
skill-benchmark run-codex --tasks /tmp/workflow-billing-eval/tasks.jsonl --runs /tmp/workflow-billing-eval/runs --codex-cmd "codex exec --config model_reasoning_effort=high" --timeout 600
python3 scripts/judge_workflow_billing_eval.py --root /tmp/workflow-billing-eval --backend codex --model default
python3 scripts/judge_workflow_billing_eval.py --root /tmp/workflow-billing-eval --backend claude --model sonnet --sample-run 1
skill-benchmark benchmark /tmp/workflow-billing-eval/manifest.json --runs /tmp/workflow-billing-eval/runs --variant with_skill --variant old_skill --variant without_skill --judge-results /tmp/workflow-billing-eval/codex-default-judge-results.jsonl --allow-scripts --out /tmp/workflow-billing-eval/benchmark.json
```

This runs a fresh revised suite, not the historical composite. The original run used four interleaved answer shards; record order, environment, hashes, and model resolution again. A default-model rerun is not guaranteed to select the same model. Use a fresh root if prompts, candidates, rubrics, or models change: cached judge files must not be reused across revisions.

Checked-in evidence: `results.json`, `judgments.json`, `judge-alignment.json`, and four selected public-case answers under `artifacts/` beside this receipt. Full raw run trees, the preserved pilot, and scripts used for assembly remain locally under `/Users/adewale/Documents/Codex/2026-07-16/how/work/workflow-billing-eval/`; provider logs and private holdout prompts are not published.

No live Workflows were deployed, no paid Cloudflare workload was generated, and no account invoice was verified. These synthetic scenarios test billing interpretation, not provider-meter reconciliation.

Official sources: [Workflow pricing](https://developers.cloudflare.com/workflows/reference/pricing/), [billing effective date](https://developers.cloudflare.com/changelog/post/2026-07-07-workflows-billing-updates/), [retention cohort change](https://developers.cloudflare.com/changelog/post/2026-09-10-paid-retention-default/).
