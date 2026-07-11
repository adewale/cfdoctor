# GPT-5.5 three-way value, precision, and efficiency eval

Run date: 2026-07-11

Answer model: `openai-codex/gpt-5.5` (`high` reasoning)

Judge model: `openai-codex/gpt-5.5` (`high` reasoning)
Harness: Skill Eval Harness v0.6.0, commit `abd8d7d57aae788658bc293abac1dab80dfb24ac`

## Compared variants

- **Local skill:** commit `ee8c704fcd7763cb114bf8b416e0c13339aa74d3`, generated after targeted routing, focused-triage, precision, oracle, and efficiency changes.
- **GitHub skill:** `origin/main` at `4a14f4d`, materialized in a detached worktree and graded as `old_skill`.
- **No skill:** GPT-5.5 without cfdoctor instructions/references.

The round contains 24 visible answer cases and 72 outputs (one run per case/variant), plus 20 GPT-5.5 qualitative judgments per variant. All 24 local outputs were regenerated from the single pinned local commit above; all GitHub outputs were freshly generated. Twenty-one unchanged no-skill outputs were reused from the immediately preceding same-day GPT-5.5 round; the three fixtures whose inputs changed were rerun. Four trigger-only cases remain in the separate deterministic trigger suite. Hidden holdout/holdback prompts were unavailable.

Qualitative assertions use an explicit `0.85` threshold rather than the previous implicit `1.0`. Deterministic grading used `--allow-scripts --strict`, including per-case token and elapsed-time assertions.

## Headline results

| Metric | Local skill | GitHub skill | No skill |
|---|---:|---:|---:|
| Objective pass rate | **97.22%** | 60.28% | 73.19% |
| Combined pass rate | **97.57%** | 65.23% | 70.50% |
| Efficiency pass rate | **97.92%** | 45.83% | 97.92% |
| GPT-5.5 judge mean score | **0.9585** | 0.9345 | 0.7570 |
| Judge passes at 0.85 | **20/20** | 19/20 | 12/20 |
| Mean tokens/run | **56,843** | 134,984 | 25,818 |
| Median tokens/run | **54,482.5** | 140,637 | 17,330.5 |
| Mean elapsed/run | **45.0 s** | 90.6 s | 26.9 s |
| Mean commands/run | **2.75** | 8.50 | 1.25 |

### Local versus GitHub

- Objective: **+36.94 percentage points**.
- Combined: **+32.34 points**.
- Efficiency: **+52.09 points**.
- Mean tokens: **57.9% lower**.
- Mean elapsed time: **50.3% lower**.
- Mean commands: **67.6% lower**.
- Judge score: **+0.0240**, with 20/20 rather than 19/20 passes.

### Local versus no skill

- Objective: **+24.03 percentage points**.
- Combined: **+27.07 points**.
- Judge score: **+0.2015**.
- Paired objective lift is significant in the harness's seeded sampled sign-flip test: `p = 0.000244` across 24 pairs (4,096 samples, seed 0).
- The local skill still costs about **2.20×** mean tokens and **1.67×** elapsed time versus no skill. This is materially better than GitHub, but remains the main optimization ceiling.

Dollar cost was unavailable; token and elapsed telemetry are the auditable cost proxies.

## Requested fixes: observed behavior

### Clean baseline and path preservation

The benchmark now uses a path-safe, self-contained clean fixture: `main: index.js`, intentional exact route behavior documented in a supplied README, `no-store`, sampled observability, and no bindings.

| Variant | Objective | Combined | Efficiency | Tokens | Result |
|---|---:|---:|---:|---:|---|
| Local | **1.00** | **1.00** | **1.00** | 58,424 | `No confirmed findings.`; compensating intent respected. |
| GitHub | 0.25 | 0.20 | 0.00 | 162,985 | Fabricated a medium route/query-string finding despite explicit intent. |
| No skill | 0.50 | 0.60 | 1.00 | 23,952 | Avoided a serious finding but lacked the structural scope/no-finding contract. |

This fixes the prior flattened `src/index.js` false missing-entrypoint finding and upgrades the oracle to require zero finding blocks.

### DLQ-safe near miss

The fixture now performs work before `ack()`, retries failures with a delay, sets `max_retries: 3`, and configures `dead_letter_queue`. The oracle no longer globally rejects benign phrases such as “not an unbounded retry policy”; it requires explicit process-before-ack recognition, the configured controls, and zero finding blocks. A contradictory ack-before-work regression now fails.

| Variant | Objective | Combined | Efficiency | Tokens | Result |
|---|---:|---:|---:|---:|---|
| Local | **1.00** | **1.00** | **1.00** | 110,073 | No confirmed finding; optional DLQ operations correctly left as account evidence. |
| GitHub | 0.00 | 0.25 | 0.00 | 162,925 | Invented retry-classification and DLQ-handling findings. |
| No skill | 0.67 | 0.75 | 1.00 | 50,954 | Recognized DLQ/bounds but still called the valid policy weak. |

### Standalone non-Cloudflare activation

The local skill now has a hard activation boundary: AWS-only tasks do not trigger project-evidence inspection, the Cloudflare scanner, or a Cloudflare audit. On the AWS case, local used 36,881 tokens versus GitHub's 106,591 and passed all efficiency checks. The harness read the staged `SKILL.md`, but the answer did not run the Cloudflare scanner, inspect project evidence, or emit an audit scaffold. No skill remained cheapest at 11,348 tokens.

### Valid JSONC path and structural oracle

JSONC fixture inputs now preserve `main: index.js`. Local produced a complete evidence-backed broad-route finding and passed objective, qualitative, and efficiency gates (`1.00/1.00/1.00`); GitHub scored `0.333/0.50/0.00` and used 213,789 tokens.

## Implemented process changes

1. **Reference routing:** inventory and scanner first; read only references tied to concrete hypotheses. Broad playbook/provenance/war-story reading is no longer mandatory.
2. **Output modes:** concise focused triage for narrow/no-finding cases; full scaffold only for broad audits or multiple material findings.
3. **Activation:** standalone AWS/non-Cloudflare, generic DNS, status, news, brand, and conceptual prompts do not use cfdoctor's audit workflow.
4. **Precision:** zero scanner findings, explicit intent, tests, and compensating controls suppress generic hygiene/default findings.
5. **Fixture fidelity:** benchmark fixtures use path-safe staged entrypoints and explicit intent rather than flattened-path artifacts.
6. **DLQ oracle:** safe control requires zero findings; benign negation text is allowed.
7. **Judge calibration:** all judge assertions now set `threshold: 0.85`.
8. **Efficiency gates:** every one of the 24 tune answer cases has token and elapsed-time limits; no-trigger cases have stricter budgets.

## Remaining risks

- One sample per variant is insufficient for pass@k/flakiness claims.
- GPT-5.5 judged GPT-5.5; release gating should add a human-labeled alignment set or second judge model.
- Local remains slower and more token-heavy than no skill, even though the diagnostic lift is significant.
- Some no-skill/GitHub answers receive high qualitative scores while failing structural precision or efficiency gates; combined metrics should remain multi-dimensional rather than judge-only.
- Efficiency budgets are tune-set calibration, not universal latency/token guarantees; several runs are close to their visible thresholds, and hidden holdout/holdback cases were unavailable.
- Raw dollar spend was unavailable from the Codex runner.

## Reproduction artifacts

A durable machine-readable aggregate with per-case scores, judge evidence, telemetry, failed assertions, and transcript/output hashes is committed at `evals/results/gpt-5.5-value/summary.json`. Raw transcripts remain outside the repository:

- Runs: `/tmp/cfdoctor-gpt55-3way-runs`
- Judge rows: `/tmp/cfdoctor-gpt55-3way-judge.jsonl`
- Local/no-skill benchmark: `/tmp/cfdoctor-gpt55-3way-local-none-final5.json`
- GitHub benchmark: `/tmp/cfdoctor-gpt55-3way-github-final5.json`
- GitHub baseline worktree: `/tmp/cfdoctor-github-baseline` at `4a14f4d`
