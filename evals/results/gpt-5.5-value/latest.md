# GPT-5.5 expanded PR three-way value, precision, and efficiency eval

Run date: 2026-07-11

Answer model: `openai-codex/gpt-5.5` (`high` reasoning)

Judge model: `openai-codex/gpt-5.5` (`high` reasoning)

Harness: Skill Eval Harness v0.6.0, commit `abd8d7d57aae788658bc293abac1dab80dfb24ac`

## Compared variants

- **PR skill (`with_skill`)**: commit `8a5aab572e065c120cd01571408785466251f157`.
- **Current main (`old_skill`)**: `origin/main` at `4468533281e15a6c14c039a9cc4b186056b250ce`.
- **No skill (`without_skill`)**: GPT-5.5 without cfdoctor instructions/references.

The expanded round contains 28 visible answer cases and 84 graded outputs. All 28 PR answers were generated fresh from one skill revision. The 24 unchanged legacy current-main/no-skill outputs remained pinned to the same revisions and byte-identical case inputs; four new outputs per baseline were generated fresh. All 72 qualitative judgments were fresh. Four trigger-only cases remain in the deterministic suite. Hidden holdout/holdback prompts were unavailable.

Deterministic grading used `--allow-scripts --strict`; qualitative assertions used the declared `0.85` threshold. Dollar cost was unavailable, so tokens, elapsed time, and commands remain the cost proxies.

## Headline results

| Metric | PR skill | Current main | No skill |
|---|---:|---:|---:|
| Objective pass rate | **93.21%** | 88.39% | 72.70% |
| Combined pass rate | **94.08%** | 89.68% | 68.32% |
| Process pass rate | **100.00%** | **100.00%** | **100.00%** |
| Efficiency pass rate | **98.21%** | 96.43% | **98.21%** |
| GPT-5.5 judge mean | **0.9550** | 0.9392 | 0.7183 |
| Judge passes at 0.85 | **24/24** | 23/24 | 11/24 |
| Mean tokens/run | 50,375 | 49,243 | **24,605** |
| Median tokens/run | 42,663.5 | **42,469.5** | **17,244.5** |
| Mean elapsed/run | **32.4 s** | **32.4 s** | **25.4 s** |
| Mean harness-normalized commands/run | 2.71 | 2.57 | **1.21** |
| Missing outputs / execution errors | 0 / 0 | 0 / 0 | 0 / 0 |

## PR versus current main

- Objective: **+4.82 percentage points**.
- Combined: **+4.40 points**.
- Efficiency: **+1.79 points**.
- Judge score: **+0.0158**, with 24/24 rather than 23/24 passes.
- Mean tokens: **2.3% higher**.
- Mean elapsed time: effectively equal (**0.01% lower**).
- Mean harness-normalized commands: **5.6% higher**.

The paired objective difference was not significant in the seeded 4,096-sample sign-flip test (`mean delta = +0.048214`, `p = 0.234562`). This round supports equivalence on legacy behavior plus targeted new-functionality lift; it does not establish a universal quality improvement.

## PR versus no skill

- Objective: **+20.52 percentage points**.
- Combined: **+25.76 points**.
- Judge score: **+0.2367**, with 24/24 versus 11/24 passes.
- Paired objective lift remained significant (`mean delta = +0.205159`, `p = 0.000244`).

The cost of that lift was about **2.05×** mean tokens, **1.27×** mean elapsed time, and **2.24×** mean harness-normalized commands versus no skill.

## New Wrangler snapshot coverage

Four cases now directly test the PR functionality:

1. fixture-backed reconciliation of two traffic-bearing Worker versions when only one version view is supplied;
2. fixture-backed separation of Pages deployment evidence from Worker version/config evidence;
3. an approval-gated Worker snapshot command plan; and
4. Static Assets metadata-only collection without source/config download.

| New four-case slice | PR skill | Current main | No skill |
|---|---:|---:|---:|
| Objective | **95.00%** | 60.00% | 69.72% |
| Combined | **95.45%** | 61.95% | 64.45% |
| Efficiency | **100.00%** | 75.00% | **100.00%** |
| Judge mean | **0.9400** | 0.8625 | 0.7900 |
| Judge passes | **4/4** | 3/4 | 1/4 |

The four-case slice is intentionally small and should be treated as a targeted regression guard, not a significance claim.

## Legacy regression analysis

The earlier 24-case PR round had scored 88.61% objective versus main's 93.12%. Trace analysis found no causal link to the new reference:

- PR and main `SKILL.md` were byte-identical.
- None of the six divergent cases loaded the changed Wrangler/account-state reference.
- The largest difference came from autonomous trajectory variance: one PR run searched the entire skill tree and consumed 364,334 tokens where main stopped after `SKILL.md` at 25,019 tokens.
- Another PR run violated the no-evidence boundary by inspecting the scanner; its paired main run stopped early.

After adding direct coverage and rerunning all PR answers from one tuned skill revision, the legacy 24-case slice was effectively unchanged:

| Legacy 24-case slice | PR skill | Current main | No skill |
|---|---:|---:|---:|
| Objective | 92.92% | **93.12%** | 73.19% |
| Combined | 93.85% | **94.31%** | 68.97% |
| Efficiency | 97.92% | **100.00%** | 97.92% |
| Judge mean | **0.9580** | 0.9545 | 0.7040 |
| Judge passes | **20/20** | **20/20** | 10/20 |

The legacy paired objective delta was `-0.21` points with sampled `p=1.0`. The prior apparent regression did not reproduce.

The implementation change that improved the new slice was architectural rather than keyword tuning: Wrangler guidance moved out of the broad account-sharing document into a short dedicated reference, with direct routing for supplied snapshots/deployed-state collection. The reference makes approval, project-pinned tooling, active-version fanout, snapshot sensitivity, Pages/Worker separation, and Static Assets metadata-only behavior explicit.

Detailed evidence is in [`../../../research/gpt55-pr12-regression-analysis.md`](../../../research/gpt55-pr12-regression-analysis.md).

## Limitations

- One answer per case is insufficient for pass@k or flakiness claims.
- GPT-5.5 judged GPT-5.5; there is no human or second-model alignment sample.
- The 24 unchanged current-main/no-skill outputs were reused from the immediately preceding same-day round; their judgments and all four new-case outputs were fresh.
- Hidden holdout and holdback prompts were unavailable.
- Efficiency thresholds are visible tune-set budgets, not universal guarantees.
- Dollar-cost telemetry was unavailable.

## Reproduction artifacts

The durable machine-readable aggregate at [`summary.json`](summary.json) contains all 84 per-case rows, objective/process/efficiency results, fresh judge evidence, normalized telemetry, failed assertions, command traces, skill material hashes, and output/trace hashes. Raw model artifacts remain outside Git:

- Runs: `/tmp/cfdoctor-pr12-expanded-gpt55/runs`
- PR judges: `/tmp/cfdoctor-pr12-expanded-gpt55/local-judge.jsonl`
- Current-main judges: `/tmp/cfdoctor-pr12-expanded-gpt55/main-judge.jsonl`
- No-skill judges: `/tmp/cfdoctor-pr12-expanded-gpt55/none-judge.jsonl`
- PR benchmark: `/tmp/cfdoctor-pr12-expanded-gpt55/local-final.json`
- Current-main benchmark: `/tmp/cfdoctor-pr12-expanded-gpt55/main-final.json`
- No-skill benchmark: `/tmp/cfdoctor-pr12-expanded-gpt55/none-final.json`
- Current-main worktree: `/tmp/cfdoctor-pr12-gpt55/main-baseline`
