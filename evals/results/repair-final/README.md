# Final repair evaluation — 7 November 2026

**cfdoctor improves on this sample. Keep PR #36 on hold.** Both judges score the final skill higher, and independent source review finds more complete diagnoses. The expanded sample also exposes a repeated new operation-count error. The repair has not met its predeclared condition of avoiding a new material error pattern.

The installed skill is frozen at `a1e9c3ae07d6cf61b50fadb44b2c12e0ff681372`. Later commits only align ablation offsets and publish evidence. The scanner and guidance changes are real improvements; they do not make generated audit reports safe to publish without checking their claims.

## What changed

The scanner recognizes terminal dead-letter consumers from the source consumer's configuration within the same Worker/environment. Unrelated consumers still need their own DLQ. Generic test variables named `secret` become low-confidence leads; service-shaped credentials and stronger assignments later in the file retain priority.

Finding criteria now precede exploration: verify the executed branch, violated requirement, API/counter identity and valid remedy. The guidance distinguishes admission-time expiry from stronger deadlines, scopes the public GET/HEAD cost verdict, permits source-grounded application findings, and requires attribution to documents actually inspected. Hidden configuration and initializing WebSocket sessions are included in relevant inventory/recovery checks.

Two visible 32-answer repair pilots failed before this version. They exposed a wrong quota minimum, unqualified expiry-policy claims and a false R2-null rejection. Their results remain in [pilots.json](pilots.json), separate from the final run. No pilot answer contributes to the scores below.

## Matched design

| Cohort | Baseline | Final | Cases × repetitions × arms |
|---|---|---|---|
| Real projects | Original main `7eefbc7` | `a1e9c3a` | 10 × 3 × 2 = 60 audits |
| Focused regressions | Previous PR head `4bdd6c5` | `a1e9c3a` | 8 × 2 × 2 = 32 audits |

These baselines answer different questions and are never pooled. Eight real projects were used during earlier evaluation/repairs. Two independently selected additions are [AnyNote](https://github.com/bestK/anynote/tree/6a9af2ab179efc0eea7a026a9b9d848c950d4581) and [Bashupload](https://github.com/DullJZ/bashupload-r2/tree/104901548e0b436fed269e445c4d23a0cfb043a6). Their source keys were visible to the operator before final freeze, so they are an expanded sample, not secret holdouts. No project-specific form-serialization or stream-length answer was added to the skill. [Source index and scope](source-index.json), [disclosures](disclosures.json).

All 92 answers were newly generated through the existing native Skill Eval Harness hooks, pinned to `abd8d7d57aae788658bc293abac1dab80dfb24ac`. Codex generation uses `gpt-5.6-sol`, high reasoning and a 480-second limit. Six workers interleave pairs; arms run serially within each pair. Each arm goes first in exactly half the pairs in each cohort. Seed `20261107` controls scheduling/statistics, not model determinism.

Each pair receives identical rendered prompts, raw source bytes, frozen official documentation and tool rules; only the selected skill differs. The serialized source bundle and answer keys are absent from model-visible workspaces. The public reconstruction matches every rendered prompt and the seeded order. [Isolation](isolation-receipt.json), [reconstruction](reproduction-receipt.json), [harness integrity](harness-integrity.json), [independent accounting verification](independent-accounting-review.json).

Both native judges score every report: Codex `gpt-5.6-sol` and Claude `claude-sonnet-4-6`, with opaque candidate identities and strict structured output. Both first passed 24/24 independently authored near-miss examples, including policy ambiguity, false source inspection, nullable R2 payloads and scoped cost verdicts. Calibration does not guarantee accurate judgment of a long audit. [Cases](calibration-cases.json), [verdicts](calibration-results.json).

## Audit scores

Each score is the mean of recall, precision, actionability and evidence after `(rating−1)/4` maps the anchored 1–5 ratings to 0–1. Scores below are on a 0–100 scale; they are not percentages of all project bugs found. Additional valid findings receive credit. Source keys are non-exhaustive.

| Cohort / judge | Old | Final | Change | 95% cluster bootstrap interval | Exact sign-flip p |
|---|---:|---:|---:|---|---:|
| 10 projects / Codex | 73.23 | 79.48 | +6.25 | [+3.33, +9.17] | 0.0078 |
| 10 projects / Claude | 71.04 | 77.08 | +6.04 | [+0.21, +12.08] | 0.1016 |
| Focused / Codex | 85.55 | 92.58 | +7.03 | [−1.56, +18.75] | 0.5000 |
| Focused / Claude | 89.45 | 95.70 | +6.25 | [0.00, +15.62] | 0.3750 |

Both judges improve all four mean dimensions in both cohorts. On real projects, Codex records 17 wins/7 losses/6 ties and Claude 18/7/5. Quality-threshold passes rise 8→11 of 30 for Codex and 5→11 for Claude. On the two additions, score gains are +8.33 Codex and +4.17 Claude; two projects cannot support a broad generalization claim.

Inference averages repetitions within ten project clusters or four regression families, then uses 50,000 bootstrap resamples and exact sign flips. The two tests have different assumptions; do not describe both judges as conventionally significant. The two-project bootstrap is especially uninformative: Codex's two project effects happen to be identical.

Precision remains weaker than diagnosis. Codex flags material precision errors in 20→18 of 30 real-project reports; Claude flags 13→6. They agree on that flag in only 35/60 reports, and on the quality threshold in 41/60. Independent source review therefore remains necessary. Numeric ratings were not replaced by manual judgments. A concrete grader error remains: Codex calls the final `repair-c1` repetition 1 scanner claim fabricated, although the original task permits read-only scanner use and the trace records an exit 0 scan containing that DLQ lead. It confuses its own grading permissions with the auditor’s permissions and treats missing grader-side execution evidence as proof of fabrication. The original rating is retained; this is another reason not to equate judge precision flags with verified false findings. Native scores round to four decimals; analysis retains exact normalized means, and export verifies the native rounded values.

## Source review and remaining problems

Independent agents reviewed all 92 opaque reports against frozen source/docs before receiving arm identities. Each report hash and every material quotation was verified. These are agent adjudications, not human maintainer review or runtime proof. Categories can overlap.

| Real-project reports | Old /30 | Final /30 |
|---|---:|---:|
| All required primary mechanisms explicitly detected | 24 | 28 |
| False or unsupported source/API statement flagged | 9 | 8 |
| Requirement/confidence overclaim flagged | 12 | 11 |
| Invalid remedy or verification step flagged | 6 | 6 |
| Incorrect source attribution flagged | 3 | 1 |
| Any flagged issue | 21 | 19 |

Both versions detect all primaries or respect the named invariant in 16/16 focused reports. The old focused arm has one false API claim and two requirement overclaims across two reports; the final arm has none. Both final expiry-control repetitions keep the unspecified sampling deadline as a question, while the broken expiry/ownership control remains detected.

The final real-project reports still need corrections:

- **New repeated branch-count error:** AnyNote final repetitions 2 and 3 say GET/HEAD requests to `/set` reach one attempted KV write each. Its awaited body parser can reject first, for example on an empty `application/json` body (`index.js:483`, `1155–1156`), before `NOTE.put` at 484. The upper bound is zero to one, not a guaranteed one per request. One report's table already uses “up to 1”; its prose contradicts that qualification. None of the old repetitions contains this guaranteed-operation assertion. Both versions nevertheless find the primary form-parser string/object mismatch.
- **Invalid fixes persist:** status-page reports prescribe literal `continue` inside a `.map()` callback in `src/cli/gcMonitors.js`. Use a callback return or actually refactor to a loop. Six final reports across projects have a remedy/verification issue; a correct diagnosis alone does not make its fix usable.
- **Scope and attribution errors persist:** supplied ByteGo inventory cannot establish upstream `.gitignore` policy; redirect analytics failure returns local 404 rather than global 500; README's query-style revocation example cannot be described as existing only in source.
- **Policy questions still become requirements:** intentional public/manual features and separately credentialed routes sometimes get mandatory removal/authentication recommendations without an established stronger contract. Real deployment/cost risks remain valid when qualified.
- **Recall is incomplete:** the final skill finds the initializing chat backlog loss in two of three repetitions; one still misses it. Additional valid findings do not substitute for that mechanism.

The new AnyNote pattern fails the preregistered readiness condition despite the aggregate gains. The next repair needs reliable branch-count and remedy verification; these results do not justify saying the gaps are all fixed. [Source summary](source-review-summary.json), [60 project reviews](projects-source-reviews.jsonl), [32 focused reviews](regressions-source-reviews.jsonl).

## Token overhead

Answer-generation usage only; judge/calibration calls are excluded. Cumulative input includes repeated context across tool/model turns. Cached input is a subset of input, and reasoning is a subset of output.

| Mean per real-project audit | Old | Final | Change |
|---|---:|---:|---:|
| Input tokens | 672,473 | 693,319 | +3.10% |
| Cached input | 599,134 | 620,100 | +3.50% |
| Uncached input | 73,339 | 73,219 | −0.16% |
| Output tokens | 13,344 | 13,877 | +3.99% |
| Total tokens | 685,817 | 707,197 | +3.12% |
| Elapsed seconds | 255.86 | 265.05 | +3.59% |

About 98.1% of the added total tokens are cached input. Reasoning output rises 5.7%; final answers are 2.5% shorter by word count. Commands rise 11.5% while command-output characters fall 2.2%; the new workload reference is read 1.83 times per audit on average. These observations do not identify exact per-file token cost or a causal reason for every change.

The 95% project intervals are [−7.83%, +16.82%] for total tokens, [−4.80%, +5.38%] for uncached input and [−0.13%, +8.04%] for elapsed time. The earlier 25.6% overhead does not reproduce as this run's estimate. Provider caching, model variation, changed sample and earlier mount changes prevent a stable cost or causal savings claim. Both arms now have zero serialized-bundle reads.

Against the previous PR head, the focused cohort uses 15.1% fewer total tokens and 11.0% less elapsed time on average. Keep that separate from original-main comparisons.

All 92 executions meet 480 seconds. Only 1/60 real-project audits meets the soft 350,000-token budget; all 32 focused audits meet it. All assertions here are soft: native hard-gate combined means are null, not overall passes. Default harness paired-lift expects a `without_skill` arm and is ineligible here; the explicit old/new cluster analysis supplies the comparison. [Native receipts](native-harness-receipts.json), [all per-run metrics](run-metrics.jsonl), [aggregates/intervals](results.json).

## Deterministic checks

The same 54 detection fixtures score 40/54 on original main and 54/54 on final. The original 53 remain unchanged as a set (40→53); the added terminal-DLQ control is 0→1. All 147 unit tests, 43 trigger cases, self-scan, coverage/claim-ledger/link/install checks, strict pinned-harness validation, all seven ablations, Ruff and whitespace checks pass. Scanner leads on the ten snapshots fall 47→27, high leads 15→5; counts are heuristic noise evidence, not confirmed defect totals. Independent code review found no actionable defect and checked positive controls. [Checks](required-checks.json), [scanner comparisons](scanner-comparison.json), [code review](independent-code-review.json).

The 92 command traces contain no observed browsing, target execution or account mutation. One heuristic installation match is quoted text in an `rg` search; the command does not install anything. Trace review is not an OS sandbox proof. No target code was dynamically tested. [Process evidence](process-receipt.json).

## Reproduce

Use an environment with the pinned harness dependencies and authenticated native Codex/Claude CLIs. Create immutable checkouts of original main `7eefbc7`, previous PR head `4bdd6c5` and final `a1e9c3a`. Clone the harness into `$work/harness` and check out `abd8d7d57aae788658bc293abac1dab80dfb24ac`.

```sh
python evals/results/repair-final/prepare_inputs.py \
  --work "$work" --baseline /path/to/main --previous /path/to/previous \
  --candidate /path/to/final \
  --source-cache /path/to/frozen/inputs --docs-cache /path/to/frozen/inputs
python "$work/preflight.py" "$work"
python evals/results/repair-final/calibrate.py --work "$work/calibration" --harness "$work/harness"
python "$work/run_round.py" "$work"
```

The cache arguments are optional; uncached acquisition verifies immutable source hashes and fails closed if current docs differ from the frozen snapshots. Complete source/docs caches, answers, provider traces and native reports remain in the local `repair-eval-work/suite-r3` archive; hashes and compact evidence are committed.

Run `judge_round.py` for each cohort (`$work/projects`, `$work/regressions`) with each backend (`codex`, `claude`), then `summarize_round.py`, `overhead_uncertainty.py` and the harness's `benchmark` command with both `--variant old_skill --variant with_skill` and the matching `--judge-results`. Calibration must pass before grading. The original execution pipelined judgments while answers arrived, with four judge workers per backend across cohorts. Provider traces and complete native reports remain outside Git; raw ratings, rationales, source adjudications, answer hashes and usage remain reviewable here.
