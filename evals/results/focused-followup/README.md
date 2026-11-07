# Focused follow-up — 7 November 2026

This is a small follow-up to the [92-audit comparison](../repair-final/README.md). It fixes the judge's missing execution evidence and makes control-flow remedy guidance more concrete. It also removes the requirement to devise a test for every finding: use existing checks when permitted and useful.

The installed skill now explains that callback `return` and loop `continue` have different scopes. A proposed loop refactor must be explicit. A short clarification distinguishes conditional operation bounds from counts guaranteed for every request. No output fields, dependencies or approval steps were added.

## What was checked

Four new unit tests cover observed scanner results, quoted tool mentions/failed commands, missing traces and stale judge caches. Removing receipt forwarding makes the forwarding test fail. The full suite passes: 151 unit tests, 43 trigger cases and 54 detector fixtures, plus self-scan, coverage/ledger/link/install checks, Ruff and pinned-harness ablation validation.

The known queue report was graded again with actual command receipts. A counterfactual changes its reported scanner lead to one absent from the recorded result. Both judges distinguish them:

| Report | Codex precision/evidence | Claude precision/evidence |
|---|---|---|
| Real scanner result | 5 / 5 | 5 / 4 |
| False scanner-lead attribution | 3 / 3 | 3 / 3 |

Previously Codex assigned 2 / 1 to the real report and called its scanner claim fabricated. The fix supplies evidence; it does not tell the judge to accept execution claims. [Four native verdicts](judge-check.json).

Eight fresh matched audits cover status-page and AnyNote, two repetitions per arm. Baseline is `69426f6`; candidate is `643911f`. Source, original prompts, documents, generation model/reasoning and 480-second limit match within each pair. Both arms use the corrected judge. These are known tuning cases, not a fresh-project sample.

- Both revised status-page reports explicitly propose `for...of` before `continue`. Both baseline reports also give valid callback-level remedies. Primary monitoring/cleanup failures remain detected in all four reports. This shows the new guidance is usable, not an established improvement in success rate.
- All four AnyNote reports detect the form-parser string/object mismatch. Both baseline reports bound or qualify writes. One revised report still gives an unqualified per-request count; the other uses “up to one” in its table/exposure but has a loose summary. The wording clarification has not reliably eliminated overstatement.

These source checks concern the targeted claims, not a certification of every finding. Policy framing and other ordinary audit mistakes remain possible. The original 92 ratings are preserved; this follow-up makes no broad quality or cost claim. [Eight outputs' hashes, source notes and both judges' ratings](results.jsonl), [configuration and source hashes](protocol.json).

## Review cost and merge judgment

Six superseded generated payloads, about 18,000 lines, were removed from the current PR file set. Their exact bytes remain linked from the [historical report](../final-expanded/README.md) at immutable commit `69426f6`. Current results and reproduction helpers remain available.

The earlier blanket hold treated the AnyNote wording error as a material merge blocker even where the table already supplied the right upper bound. That was too rigid. Judge concrete consequences and regressions alongside the demonstrated scanner/diagnosis gains. The syntax and judge-evidence corrections are substantive; these results do not promise error-free generated audits.

## Repeat the focused run

Use the pinned harness `abd8d7d57aae788658bc293abac1dab80dfb24ac`, authenticated native Codex/Claude CLIs and the existing raw-project wrappers in `../repair-final/`. Reuse the hash-verified input cache from the broader run. The supplied [manifest](manifest-template.json) contains the exact two cases; set its skill paths to immutable baseline/candidate checkouts and its input paths to that cache.

```sh
python "$work/harness/skill_benchmark.py" prepare "$work/manifest.json" \
  --split tune --include-old-skill --runs-per-variant 2 \
  --models gpt-5.6-sol --out "$work/tasks.jsonl"
python "$work/run_round.py" "$work"
python "$work/judge_round.py" "$work" codex
python "$work/judge_round.py" "$work" claude
```

The wrappers expect the pinned harness at `$work/harness ` and the adjacent grading contract. Local source inputs, full answers and traces remain in `focused-improvements-work/`. A new grading input fingerprint prevents stale verdict reuse after source, receipt, rubric or output changes.

The bundled skill-creator validator still rejects the pre-existing `compatibility` frontmatter field on both baseline and candidate. Repository frontmatter/trigger/install checks pass; this change preserves that metadata.
