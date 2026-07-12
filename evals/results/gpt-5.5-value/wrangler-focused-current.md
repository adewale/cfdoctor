# GPT-5.5 repeated Wrangler eval against current skill material

Run date: 2026-07-11

Answer/judge model: `openai-codex/gpt-5.5` (`high` reasoning)

Harness: Skill Eval Harness v0.6.0, commit `abd8d7d57aae788658bc293abac1dab80dfb24ac`

Scope: four visible Wrangler snapshot cases, three fresh isolated `with_skill` runs per case. Current-main and no-skill baselines were not regenerated because they do not load the changed skill material. Canonical skill material SHA-256: `ee6f00047b736ad0286e33c5f52590391bea7f6c647ecd077e37a346edc54b7e`.

## Result

| Metric | Current repeated eval | Prior pinned PR slice |
|---|---:|---:|
| Samples per case | **3** | 1 |
| Objective | **94.52%** | 95.00% |
| Combined | **95.08%** | 95.45% |
| Process | **100.00%** | 100.00% |
| Efficiency | **100.00%** | 100.00% |
| Judge mean | **0.9608** | 0.9400 |
| Judge passes | **12/12** | 4/4 |
| Mean tokens | 43,945.83 | 45,516.25 |
| Median tokens | 42,190 | — |
| Mean elapsed | 34.4 s | 27.6 s |
| Mean harness-normalized commands | 2.75 | 3.00 |
| Missing outputs / execution errors | 0 / 0 | 0 / 0 |

The current three-sample objective and combined means are within 0.48 and 0.37 percentage points of the prior one-sample slice, while qualitative judgment is higher. Per-round objective rates were 97.50%, 95.23%, and 90.83%, directly demonstrating why one trajectory should not be treated as stable. The manifests and sample counts differ, so this is descriptive evidence, not a paired significance result.

## Per-case means

| Case | Objective | Combined | Judge | Judge passes |
|---|---:|---:|---:|---:|
| Worker multi-version reconciliation | 94.44% | 95.24% | 0.9433 | 3/3 |
| Pages/Worker evidence separation | 100.00% | 100.00% | 0.9467 | 3/3 |
| Approval-gated collection plan | 96.97% | 97.22% | 0.9667 | 3/3 |
| Static Assets metadata-only plan | 86.67% | 87.88% | 0.9867 | 3/3 |

## What changed

1. Approval and no-install assertions now accept safe semantic equivalents such as “pending approval,” “approve running these reads,” and “not npx or an installer-backed runner.”
2. Both collection-plan cases have a script oracle that rejects positively recommended `npx`, `npm exec`, `pnpm dlx`, or `bunx` while allowing explicit prohibitions.
3. `SKILL.md` and the routed Wrangler reference tell static snapshot planning/reconciliation not to browse unless the user asks or command availability/semantics is materially disputed.
4. The Wrangler reference requires truncated deployment/version IDs unless a full ID is necessary for an exact approved command or disambiguation. The Worker fixture oracle rejects unnecessary full fixture IDs.
5. Three fresh samples per case replace the unstable one-answer interpretation.

## Remaining misses

Across 12 runs:

- No output recommended a package runner.
- No run exceeded token or elapsed budgets; the previous documentation-search outlier did not recur.
- One Worker answer unnecessarily emitted a full missing-version ID in a proposed command.
- Four collection plans used the direct existing binary but omitted an explicit no-install/package-runner sentence.
- One Static Assets answer described the correct no-download behavior without using the literal `metadata-only` label.

These remaining misses explain the gap from 100%; all 12 qualitative judgments still passed.

## Tuning disclosure

These are visible tune cases. The instruction, package-runner oracle, full-ID rule, and initial semantic regexes were changed before generation. After inspecting the generated outputs, safe approval/Static Assets word orders and a scoped Worker-evidence phrase were added to the oracles, then the same outputs were regraded. No answer text or telemetry was changed. This is regression evidence, not hidden generalization evidence.

Machine-readable evidence: [`wrangler-focused-current.json`](wrangler-focused-current.json). Raw outputs, traces, judge transcripts, and benchmark data remain outside Git under `/tmp/cfdoctor-pr12-focused-gpt55-repeated`.
