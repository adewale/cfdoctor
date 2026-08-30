# PR 24 public-surface evaluation receipt

This receipt evaluates implementation `0bc463a4a394d3b885ec68bcabf194058711de4f`
against the skill at pinned base `72a57e9372ec65a28cfcb9edd201d57a3aed8148`.
The harness was pinned to `abd8d7d57aae788658bc293abac1dab80dfb24ac`;
Codex CLI was `0.145.0`. Answer models were `gpt-5.6-luna` and
`gpt-5.6-terra` with model-default reasoning (not overridden). Luna answers
were judged by Terra and Terra answers by Luna at threshold `0.85`.

Generation tasks contained the selected skill, prompt, and fixture files, but
not expected behavior or judge rubrics. Six visible tune cases used two runs
for `with_skill` and pinned `old_skill`, plus one run of the focused
`no-public-surface-graph` ablation. The generation-blind holdout was run once
per variant after the implementation was frozen and was not used for
post-score tuning.

## Results

| Answer model | Tune arm | Hard gates | Cross-judge passes | Mean judge | Efficiency gates | Tokens | Elapsed |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Luna | pinned base | 47/90 | 0/12 | 0.574 | 18/24 | 2,074,682 | 973.3 s |
| Luna | revised skill | 66/90 | 7/12 | 0.815 | 18/24 | 2,212,182 | 1,047.9 s |
| Luna | focused ablation | 22/45 | 0/6 | 0.538 | 9/12 | 947,833 | 483.4 s |
| Terra | pinned base | 48/90 | 1/12 | 0.633 | 15/24 | 2,258,652 | 953.8 s |
| Terra | revised skill | 65/90 | 8/12 | 0.845 | 15/24 | 2,642,240 | 920.7 s |
| Terra | focused ablation | 24/45 | 0/6 | 0.622 | 5/12 | 1,900,648 | 558.7 s |

The repeated tune panel shows targeted lift. The focused ablation's lack of
qualitative passes is consistent with the new workflow contributing to that
lift; this one-run ablation does not isolate model variance. The panel does not
show saturation: the Mulvany-shaped core case remained below the qualitative
threshold in all four revised tune runs, mainly because answers omitted parts
of the route inventory or cache first-fill/refill scenario.

| Answer model | Blind arm | Hard gates | Judge score | Efficiency gates |
| --- | --- | ---: | ---: | ---: |
| Luna | pinned base | 3/5 | 0.22 | 1/2 |
| Luna | revised skill | 3/5 | 0.42 | 2/2 |
| Luna | focused ablation | 1/5 | 0.18 | 2/2 |
| Terra | pinned base | 2/5 | 0.20 | 2/2 |
| Terra | revised skill | 3/5 | 0.72 | 2/2 |
| Terra | focused ablation | 1/5 | 0.18 | 1/2 |

Neither revised answer cleared the blind holdout's `0.85` judge threshold.
Both missed the complete split between exact assets served before the Worker
and missing reserved asset paths returned through `ASSETS` before D1; both also
omitted some directly relevant Static Assets/routing documentation. This is a
useful improvement over the base and ablation, but not generalization proof.

All 66 included answer executions completed with return code zero, no timeout,
and normalized token telemetry. An earlier sandboxed attempt produced 66
nonzero task exits because DNS access to the model endpoint was blocked. Those
error stubs had missing usage telemetry and are explicitly excluded.

## Reproduction protocol and command templates

The command templates below use the executable from harness commit
`abd8d7d57aae788658bc293abac1dab80dfb24ac`. `<evaluation-manifest>` is a local
materialized copy derived from checked-in `evals/shared-benchmark.json`, reduced
to the seven cases in this receipt, with `old_skill_paths` set to a copy of
`skills/cloudflare-doctor/SKILL.md` from the pinned base SHA. The source and
materialized hashes are recorded separately below. `<private-holdout-prompt>`
must be provisioned at the holdout case's `prompt_ref` with the recorded
SHA-256 before `prepare`; it is not committed.

```sh
skill-benchmark prepare <evaluation-manifest> --split tune --models gpt-5.6-luna --runs-per-variant 2 --include-old-skill --out /private/tmp/cfdoctor-pr24-tune-luna-all.jsonl
skill-benchmark prepare <evaluation-manifest> --split tune --models gpt-5.6-terra --runs-per-variant 2 --include-old-skill --out /private/tmp/cfdoctor-pr24-tune-terra-all.jsonl
skill-benchmark prepare <evaluation-manifest> --split tune --models gpt-5.6-luna --runs-per-variant 1 --include-ablations --ablation-dir /private/tmp/cfdoctor-pr24-ablation-luna-material --out /private/tmp/cfdoctor-pr24-ablation-luna-all.jsonl
skill-benchmark prepare <evaluation-manifest> --split tune --models gpt-5.6-terra --runs-per-variant 1 --include-ablations --ablation-dir /private/tmp/cfdoctor-pr24-ablation-terra-material --out /private/tmp/cfdoctor-pr24-ablation-terra-all.jsonl
skill-benchmark prepare <evaluation-manifest> --split holdout --models gpt-5.6-luna --runs-per-variant 1 --include-old-skill --include-ablations --ablation-dir /private/tmp/cfdoctor-pr24-holdout-luna-material --out /private/tmp/cfdoctor-pr24-holdout-luna-all.jsonl
skill-benchmark prepare <evaluation-manifest> --split holdout --models gpt-5.6-terra --runs-per-variant 1 --include-old-skill --include-ablations --ablation-dir /private/tmp/cfdoctor-pr24-holdout-terra-material --out /private/tmp/cfdoctor-pr24-holdout-terra-all.jsonl
```

The prepared files were filtered to `with_skill` and `old_skill` for the tune
arms, to `ablation:no-public-surface-graph` for the focused tune ablation, and
to those three variants for the one holdout case. The resulting six task-file
hashes are recorded in `results.json`. Each selected task file was then run as:

```sh
skill-benchmark run-codex --tasks <selected-tasks.jsonl> --runs <runs-directory> --timeout 240
skill-benchmark grade <evaluation-manifest> --runs <runs-directory> --split <tune-or-holdout> --variant <variant> --allow-scripts --strict --out <objective-report.json>
skill-benchmark judge <evaluation-manifest> --runs <runs-directory> --split <tune-or-holdout> --variant <variant> --judge-backend codex --judge-model <opposite-answer-model> --strict-judge-schema --transcripts <judge-transcript-directory> --out <judge-results.jsonl>
skill-benchmark grade <evaluation-manifest> --runs <runs-directory> --split <tune-or-holdout> --variant <variant> --allow-scripts --strict --judge-results <judge-results.jsonl> --out <final-report.json>
```

Luna answers used Terra as `<opposite-answer-model>` and Terra answers used
Luna. There were two tune runs for each `with_skill`/`old_skill` case and one
run for each ablation/holdout variant. Generation tasks contained the resolved
prompt but excluded expected behavior and review rubrics. The judge threshold
comes from the manifest (`0.85`).

Task-material SHA-256 values:

- checked-in manifest: `cfc3d73a9844d10ac0b274e627eeebae1325641a62fb71f79ba605c6333f4028`
- local seven-case evaluation manifest: `54d25773176231451dd0424bc0f4cea940fd3e16a2ecfce07bdf99be950d4a57`
- revised skill: `f56a933f925a734fd55a5766989580f2c843aa498cb9d779b363be03bce986c1`
- pinned base skill: `eb8596ea1b34c7fdf88806e0f941ca4252a47269235b006009ad2300917f3546`
- private holdout prompt: `fc1f7998110b7140feef7cf0550b6d47f6eea922f2e4441bda797877f73d4502`

Repository validation at the evaluated implementation:

- `npm test`: 88 unit tests, 43/43 trigger cases, 30/30 detection fixtures;
  self-scan clean.
- strict harness validation: 46 cases and 7/7 materialized ablations.
- manifest audit: no blockers (two unrelated pre-existing judge-only
  advisories remain).
- SvelteKit fixture: direct dependencies are pinned to exact versions;
  installation and `npm run build` succeeded, generated
  `.svelte-kit/cloudflare/_worker.js`, and Wrangler dry-run completed with D1
  and Assets bindings.
- fixture syntax, source-map integrity, JSON validity, and `git diff --check`
  passed.

[`results.json`](./results.json) contains per-run hard, judge, efficiency,
token, elapsed-time, and artifact-hash records. Raw answer and judge transcripts
remain in the local `/private/tmp` run tree and are not reviewer-accessible.
The JSON hashes prepared tasks, answer outputs/metadata, retained judge-result
files, and final reports, but not the raw transcript files. Visible tune results
measure targeted regression behavior. The one-shot holdout is generation-blind
but was designed in this iteration, so it is limited forward evidence rather
than broad framework or routing generalization proof.
