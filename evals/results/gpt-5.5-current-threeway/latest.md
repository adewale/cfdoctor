# Current PR matched three-way GPT-5.5 evaluation

Run date: 2026-07-11

Answer model: `openai-codex/gpt-5.5` (`high` reasoning)

Primary judge: `openai-codex/gpt-5.5`; secondary alignment judge: `anthropic/claude-sonnet-4-6`

Harness: Skill Eval Harness v0.6.0, commit `abd8d7d57aae788658bc293abac1dab80dfb24ac`

## Protocol

- Current PR skill material: `9c4ea771a6ef3697035d49cf39067195df72c34cea354cf093cff47a1499b34c`.
- GitHub `origin/main`: immutable commit recorded in `summary.json` with skill material hash `79417093939bbc1995eac1de79e8795576eb40251cf323e891b84964e3182829`.
- No-skill arm: no cfdoctor files/instructions.
- 31 visible tune answer cases, three fresh isolated runs per case and variant: **279 answers**.
- 27 judged cases, three judgments per variant: **243 primary judgments**.
- Variant order was deterministically shuffled inside each case/run pair, then distributed round-robin across four answer shards.
- Objective grading used the same current manifest/oracles for all variants with `--allow-scripts --strict`.
- Hidden holdout/holdback cases were not included.
- A cleanup-only local harness patch made temporary-directory removal ignore a Codex plugin-clone race; answer/judge logic was unchanged and the patch is disclosed in `summary.json`.

## Full 31-case result

| Metric | Current PR | GitHub main | No skill |
|---|---:|---:|---:|
| Objective | **89.15%** | 81.79% | 72.97% |
| Combined | **89.69%** | 83.00% | 69.24% |
| Process | **100.00%** | **100.00%** | **100.00%** |
| Efficiency | 91.94% | 82.26% | **96.24%** |
| GPT judge mean | **0.9507** | 0.9333 | 0.7684 |
| GPT judge passes | **77/81** | 72/81 | 41/81 |
| Mean tokens | 59,835 | 69,182 | **30,866** |
| Mean elapsed | 43.7 s | 48.3 s | **27.5 s** |
| Mean normalized commands | 2.56 | 2.52 | **1.24** |
| Missing outputs / execution errors | 0 / 0 | 0 / 0 | 0 / 0 |

Current PR versus main objective delta: **+7.36 points**, paired sign-flip `p=0.000270`, paired bootstrap 95% CI **[+3.59, +11.26]**.

Current PR versus no skill objective delta: **+16.17 points**, paired sign-flip `p=0.000010`, paired bootstrap 95% CI **[+11.59, +20.64]**.

## Slices

### Legacy 24-case slice

| Metric | Current PR | GitHub main | No skill |
|---|---:|---:|---:|
| Objective | **89.77%** | 86.67% | 73.73% |
| Combined | **90.59%** | 88.32% | 69.15% |
| Efficiency | **95.83%** | 89.58% | 96.53% |
| Judge mean | 0.9503 | **0.9565** | 0.7348 |

Current versus main: +3.10 objective points, `p=0.107439`, bootstrap 95% CI [-0.44, +6.85]. This supports no clear legacy regression, but not a significant legacy improvement.

### Wrangler four-case slice

| Metric | Current PR | GitHub main | No skill |
|---|---:|---:|---:|
| Objective | **93.01%** | 63.96% | 60.53% |
| Combined | **93.70%** | 63.33% | 60.85% |
| Efficiency | **95.83%** | 70.83% | **95.83%** |
| Judge mean | **0.9725** | 0.8317 | 0.8267 |
| Judge passes | **12/12** | 6/12 | 7/12 |

Current versus main: **+29.04 points**, `p=0.001870`, bootstrap 95% CI [+17.22, +42.07].

Current versus no skill: **+32.47 points**, `p=0.000430`, bootstrap 95% CI [+26.89, +38.36].

### Pricing-conflict three-case slice

| Metric | Current PR | GitHub main | No skill |
|---|---:|---:|---:|
| Objective | 79.05% | 66.56% | **83.54%** |
| Combined | 77.18% | 66.67% | **81.15%** |
| Efficiency | 55.56% | 38.89% | **94.44%** |
| Judge mean | **0.9244** | 0.9144 | 0.9144 |

Current beats main by +12.49 objective points, but the nine-pair result is not significant (`p=0.062429`). No skill is 4.50 points higher objectively; that difference is also not significant (`p=0.625554`). The skill produced the best judge mean but paid substantial reference/docs overhead. Pricing remains a targeted efficiency/structure improvement area rather than a proven lift over no skill.

## Second-model judge alignment

A blind Claude Sonnet 4.6 sample judged current-PR run 1 for all 27 judged cases:

- GPT mean: 0.9544; Claude mean: 0.9581.
- Pass agreement: **26/27 (96.30%)**.
- Mean absolute score difference: 0.0185.
- Pearson score correlation: 0.6973.
- The only pass disagreement was `pricing-future-effective-conflict`: GPT 0.82/fail versus Claude 0.92/pass.

This is cross-model sensitivity evidence, not human alignment.

## Interpretation

Under a matched current protocol, the exact current PR skill is better than pinned GitHub main and no skill on the full visible benchmark, with statistically significant paired objective lift. The lift is concentrated in Wrangler behavior; legacy performance is statistically compatible with main. No skill remains much cheaper, and the new pricing slice does not yet prove objective lift over no skill.

## Limitations

- Visible tune cases and post-generation semantic oracle refinement can overfit.
- No hidden split was scored in this report.
- GPT-5.5 judged GPT-5.5 for the primary panel; Claude alignment sampled only current run 1.
- Three runs improve variance visibility but do not establish broad production generalization.
- Dollar-cost telemetry was unavailable.

Machine-readable evidence: [`summary.json`](summary.json). Raw runs, traces, judges, prepared tasks, pinned baseline tree, and transcripts remain outside Git under `/tmp/cfdoctor-current-threeway-gpt55`.
