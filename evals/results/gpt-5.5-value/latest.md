# GPT-5.5 current-PR three-way value, precision, and efficiency eval

Run date: 2026-07-11

Answer model: `openai-codex/gpt-5.5` (`high` reasoning)

Judge model: `openai-codex/gpt-5.5` (`high` reasoning)

Harness: Skill Eval Harness v0.6.0, commit `abd8d7d57aae788658bc293abac1dab80dfb24ac`

## Compared variants

- **PR skill (`with_skill`)**: commit `1e654f4bb9b2f17f6b5ffb947782c04f703bdf3a`.
- **Current main (`old_skill`)**: `origin/main` at `4468533281e15a6c14c039a9cc4b186056b250ce`, materialized in a detached worktree.
- **No skill (`without_skill`)**: the 24 pinned no-skill answer outputs from the prior final5 round. Reuse is valid because `evals/shared-benchmark.json` remains byte-identical (`d387778882a14479ea79208230d90d2b2129bdd47b0366ddcab714faecd16749`) and no-skill has no skill tree. All 20 no-skill qualitative judgments were rerun.

The run contains 24 visible answer cases and 72 graded outputs. All 24 PR and 24 current-main answers were generated fresh. All 60 qualitative judgments were generated fresh. Four trigger-only cases remain in the deterministic trigger suite. Hidden holdout/holdback prompts were unavailable.

Deterministic grading used `--allow-scripts --strict`; qualitative assertions used the declared `0.85` threshold. Dollar cost was unavailable, so tokens, elapsed time, and commands remain the cost proxies.

## Headline results

| Metric | PR skill | Current main | No skill |
|---|---:|---:|---:|
| Objective pass rate | **88.61%** | **93.12%** | 73.19% |
| Combined pass rate | **89.75%** | **94.31%** | 68.13% |
| Process pass rate | 80.00% | **100.00%** | **100.00%** |
| Efficiency pass rate | 95.83% | **100.00%** | 97.92% |
| GPT-5.5 judge mean | 0.9455 | **0.9525** | 0.7100 |
| Judge passes at 0.85 | 19/20 | **20/20** | 9/20 |
| Mean tokens/run | 65,271 | 48,480 | **25,818** |
| Median tokens/run | 48,377 | 40,930 | **17,330.5** |
| Mean elapsed/run | 35.8 s | 31.1 s | **26.9 s** |
| Mean commands/run | 3.04 | 2.50 | **1.25** |
| Missing outputs / execution errors | 0 / 0 | 0 / 0 | 0 / 0 |

## PR versus current main

The PR did **not** improve the model-based point estimates in this one-run round:

- Objective: **-4.51 percentage points**.
- Combined: **-4.55 points**.
- Process: **-20.00 points**.
- Efficiency: **-4.17 points**.
- Judge score: **-0.0070**, with 19/20 rather than 20/20 passes.
- Mean tokens: **34.6% higher**.
- Mean elapsed time: **15.2% higher**.
- Mean commands: **21.7% higher**.

The paired objective difference was not significant in the seeded 4,096-sample sign-flip test (`mean delta = -0.045139`, `p = 0.184281`). With one answer per case, this is a regression signal, not proof that the small reference change caused a stable regression.

Case-level objective differences versus main occurred in six cases:

- Lower: JSONC trailing-commas fixture (`-0.333`), runaway self-fetch fixture (`-0.167`), stale-doc advice (`-0.333`), and docs-link-only near miss (`-0.500`).
- Higher: Terraform DNS/WAF/Access (`+0.250`).
- Equal objective but lower combined: dead cross-boundary RPC because the PR answer missed the output contract and scored `0.78` with the judge.

The docs-link-only answer inspected the staged skill scanner despite the hard no-evidence boundary and exceeded its 40,000-token budget (41,888 tokens). This caused the only process failure. The dead-RPC answer was the only PR judge failure.

## PR versus no skill

The PR retained material diagnostic lift over no skill:

- Objective: **+15.42 percentage points**.
- Combined: **+21.62 points**.
- Judge score: **+0.2355**, with 19/20 versus 9/20 passes.
- Paired objective lift remained significant in the seeded sampled sign-flip test (`mean delta = +0.154167`, `p = 0.004882`).

The cost of that lift was **2.53×** mean tokens, **1.33×** mean elapsed time, and **2.43×** mean commands versus no skill.

## Interpretation

This PR primarily adds a read-only Wrangler snapshot tool, tests, and documentation; those components sit outside the answer-model benchmark. Its installable-skill change is limited to Worker/Pages deployed-state sharing guidance. The eval therefore acts as a regression/equivalence check, not direct coverage of the new CLI.

The correct conclusion is mixed:

- The PR remains substantially better than no skill on objective and judged diagnostic quality.
- It does not beat current main in this single-sample round, and its point estimates are worse on quality and overhead.
- The local-versus-main objective difference is not statistically significant under the sampled paired test.
- A repeated run or targeted rerun of the divergent cases is needed before attributing the difference to the new reference material.

## Limitations

- One answer per case is insufficient for pass@k or flakiness claims.
- GPT-5.5 judged GPT-5.5; there is no human or second-model alignment sample in this round.
- No-skill answer outputs were reused from the prior pinned round; their 20 judgments were fresh.
- Hidden holdout and holdback prompts were unavailable.
- Efficiency thresholds are visible tune-set budgets, not universal guarantees.
- Dollar-cost telemetry was unavailable.

## Reproduction artifacts

The durable machine-readable aggregate at [`summary.json`](summary.json) contains all 72 per-case rows, objective/process/efficiency results, fresh judge evidence, normalized telemetry, failed assertions, command traces, skill material hashes, and output/trace hashes. Raw model artifacts remain outside Git:

- Runs: `/tmp/cfdoctor-pr12-gpt55/runs`
- PR judges: `/tmp/cfdoctor-pr12-gpt55/local-judge.jsonl`
- Current-main judges: `/tmp/cfdoctor-pr12-gpt55/main-judge.jsonl`
- No-skill judges: `/tmp/cfdoctor-pr12-gpt55/none-judge.jsonl`
- PR benchmark: `/tmp/cfdoctor-pr12-gpt55/local-final.json`
- Current-main benchmark: `/tmp/cfdoctor-pr12-gpt55/main-final.json`
- No-skill benchmark: `/tmp/cfdoctor-pr12-gpt55/none-final.json`
- Current-main worktree: `/tmp/cfdoctor-pr12-gpt55/main-baseline`
