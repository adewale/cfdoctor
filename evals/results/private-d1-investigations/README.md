# Private/background D1 investigation smoke reviews

Date: 2026-10-18. This is visible tune/regression evidence, not an independent holdout or a measured comparison with no skill.

Repository validation passed: 116 unit tests, 43/43 trigger cases, 30/30 scanner fixtures, a clean self-scan, and strict validation of 49 shared cases / eight materialized ablations with no manifest blockers.

## Scope and method

Five fresh assistant contexts received the case's user prompt, its four raw fixture files, and the current runtime skill. They were instructed to inspect only those inputs, needed runtime references, and current official documentation; not the manifest, expected behavior, tests, or oracle. They wrote the retained [audit outputs](artifacts/) without changing the implementation or querying a Cloudflare account. The filesystem was shared and the scope was instruction-enforced, not process isolation. No token, timing, cost, or pinned model telemetry is claimed.

A separate assistant reviewed all five answers against the raw fixture files and runtime skill without reading grading inputs or initial scores. It found no material diagnosis, arithmetic, uncertainty, remediation, safe-control, or format defect. This is assistant qualitative review, not human judge alignment.

| Case | Main evidence used correctly | Qualitative review |
| --- | --- | --- |
| [Private polling](artifacts/private-d1-polling-growth.md) | 360 nominal polls/active-hour × 50,000 sampled reads; manual diagnostics remain separate | PASS |
| [Deep OFFSET](artifacts/private-d1-deep-offset.md) | Existing covering index; 10,020 versus 20 sampled reads; seek pagination proposed | PASS |
| [Repeated sync](artifacts/private-d1-repeated-sync.md) | DELETE plus INSERT; 2,000 sampled writes/run × 288 nominal triggers/day | PASS |
| [Indexed updates](artifacts/private-d1-indexed-writes.md) | Separate read/write terms and comparison clone; no unsupported index removal | PASS |
| [Safe controls](artifacts/private-d1-safe-controls.md) | Bounded query shapes and conditional atomic admission contract; no finding | PASS |

All scenarios and measurements are synthetic. None establishes the cause of the Cyberlane report or demonstrates a production saving.

## Structural grader repair

The first structural pass rejected all five answers. The [initial grades](initial-structural-grades.json) are retained. Review identified false negatives: Markdown emphasis/heading depth, deep versus shallow cohort selection, equivalent index descriptions, split query rows with shared frequency, zero-query rejection rows, and valid sample/bound caveats. The parser was repaired with regression tests while retaining negative checks for wrong units, canned missing-index diagnoses, unsupported invoice attribution, false deployment verification, and invented bounds.

Regrading the same unchanged answers passes five of five cases. [Revised grades and input/output hashes](results.json) preserve the final result. This reuse makes these artifacts grader-development regression evidence; it does not create new independent samples or establish incremental skill lift. Structural matching still needs qualitative review and cannot decide arbitrary prose correctness.

## Reproduce and limitations

From the repository root, materialize the focused manifest with `python3 scripts/focus_private_d1_eval.py --out .private-d1-focused.json`. Use the exact harness revision in `package.json` to validate with strict leakage and ablation checks, prepare fresh paired tasks and the accounting ablation, and grade with `--allow-scripts`. Output must remain at the repository root because the pinned harness requires safe relative ablation paths.

The native Codex preflight failed with HTTP 401 authentication before a fixture benchmark could run. No native paired/ablation results, speed comparison, or model-effectiveness claim is made. Fresh native evaluation remains separate from these scoped smoke reviews. Repository-only research and grading code remain outside answer inputs; expected behavior must never be included in generation prompts.
