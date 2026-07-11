# PR #12 GPT-5.5 regression analysis

Date: 2026-07-11

## Question

Why did the first current-PR GPT-5.5 round score below current `origin/main`, and did the new Wrangler guidance cause it?

## Finding: the first difference was run variance, not use of the new reference

At the evaluated revisions, the PR and current-main `SKILL.md` files were byte-identical:

```text
67e200cc471fd6ac75725ea781ec84ba6fad93fb249ad83d5980e6cb5c4bb58f
```

The only installable-skill difference was nine lines added to `references/sharing-cloudflare-state.md`. None of the six legacy cases whose PR/main objective or combined scores differed read that reference.

The divergent traces instead showed different autonomous trajectories:

- `docs-freshness-stale-local-advice`: PR searched the entire skill tree and read three references (364,334 tokens); main read only `SKILL.md` (25,019 tokens).
- `neg-docs-link-only`: PR violated the hard no-evidence boundary by listing the workspace and reading the scanner (41,888 tokens); main stopped after skill discovery/workspace listing (25,581 tokens).
- `detection-fixture-runaway-self-fetch`: PR read two broad references after the scanner; main did not.
- Dead-RPC and structural-fixture differences were answer-contract variation from identical core instructions.

The initial paired PR-versus-main objective difference was `-4.51` points with `p=0.184281`; one answer per case did not establish a stable regression. No-skill remained cheaper because it does not load or follow the skill, but it remained materially worse on diagnostic quality.

## Coverage gap

The 24 visible answer cases did not exercise the new functionality. The Wrangler snapshot script had 14 offline subprocess tests and three approved live integrations, but the shared model benchmark had no cases for:

- reconciling multiple traffic-bearing Worker versions;
- distinguishing Pages deployment rows from Worker version metadata;
- planning approval-gated Worker snapshot commands; or
- using metadata-only collection for Workers with Static Assets.

That made the first three-way score almost entirely unrelated to the PR's product value.

## Fix

Four visible tune cases were added, including two recorded-fixture cases using sanitized live-derived Wrangler shapes. They enforce:

- one version view for every active Worker version;
- no repeated authenticated read when artifacts are already supplied;
- Pages/Worker capability separation;
- explicit authenticated-read approval;
- project-pinned Wrangler rather than `npx`/`@latest`;
- snapshot privacy;
- Static Assets metadata-only behavior; and
- token/elapsed budgets.

The snapshot guidance was moved from the broad account-sharing reference into a dedicated `wrangler-snapshots.md` reference and routed directly from `SKILL.md`. This avoided loading the longer general dashboard checklist and made approval, sensitivity, active-version fanout, and Assets limitations explicit.

## Targeted before/after result

On the four new GPT-5.5 cases, before the dedicated reference tuning:

| Variant | Objective | Combined | Efficiency | Mean tokens | Mean elapsed |
|---|---:|---:|---:|---:|---:|
| PR skill | 68.21% | 72.62% | 62.50% | 52,484 | 35.5s |
| Current main | 61.90% | 63.84% | 50.00% | 59,973 | 42.2s |
| No skill | 65.95% | 60.12% | 100.00% | 17,326 | 16.3s |

After the dedicated reference and tighter routing, the final fresh local slice scored:

| Variant | Objective | Combined | Efficiency | Judge passes |
|---|---:|---:|---:|---:|
| PR skill | **100.00%** | **100.00%** | **100.00%** | **4/4** |
| Current main | 65.48% | 66.96% | 50.00% | 3/4 |
| No skill | 65.95% | 60.12% | 100.00% | 1/4 |

The four-case slice is too small for a significance claim; it is a targeted regression guard, not a broad quality estimate.

## Expanded 28-case result

A fresh PR run across all 28 visible answer cases, combined with current-main/no-skill outputs for identical case inputs and fresh judgments, showed:

- Legacy 24-case objective: PR `92.92%`, main `93.12%` (`-0.21` points; sampled paired `p=1.0`). The prior apparent legacy regression did not reproduce.
- New four-case objective: PR `100%`, main `65.48%`, no skill `65.95%`.
- Full 28-case objective: PR `93.93%`, main `89.18%`, no skill `72.16%`.
- Full PR-versus-main difference: `+4.75` points, not significant (`p=0.300464`).
- Full PR-versus-no-skill difference: `+21.77` points, significant (`p=0.000244`).

The correct conclusion is not that the new reference universally improves GPT-5.5. It is that the earlier negative point estimate was stochastic, legacy behavior is effectively unchanged in this single rerun, and the added functionality now has direct fixture-backed model coverage where the PR materially outperforms both baselines.
