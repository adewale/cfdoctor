# Cloudflare Doctor evals

These evals follow the skill-creator loop: define trigger prompts, run a quantitative pass, inspect failures, improve `SKILL.md`, and repeat.

## Trigger eval

Run:

```bash
python3 scripts/eval_skill_trigger.py
```

Inputs:
- `evals/evals.json` — repo-level eval manifest and runner pointer.
- `evals/trigger-cases.json` — positive and negative trigger prompts.
- `skills/cloudflare-doctor/SKILL.md` — frontmatter description under test.

Outputs:
- `evals/results/latest.md`
- timestamped report under `evals/results/`

What it measures:
- Trigger recall on Cloudflare audit/review/cost/security prompts.
- No-trigger specificity on false friends and unrelated tasks.
- Description coverage: expected product/intent phrases from positive cases must appear in the skill description.
- Description length remains under the skills frontmatter limit.

Limitations:
- This is a deterministic proxy, not proof that a specific model/runtime will load the skill.
- For model-based evals, run the same prompts in a harness that exposes this skill and judge whether the assistant loads Cloudflare Doctor and emits the required audit scaffold (`Docs refreshed`, `Cost proxy summary`, `Source basis`, and final run summary/cache map sections).

## Detection eval

Run:

```bash
python3 scripts/eval_detection.py
```

Deterministic regression suite for the static scanner: each fixture under
`evals/fixtures/detection/` models an accepted evidence mechanism, parser
contract, or near-miss control and declares required/forbidden check IDs plus
optional diagnostic evidence terms in `expected.json`. Clean/near-miss fixtures
use `max_findings: 0` where appropriate.

A `max_findings: 0` fixture only guards the detectors its content nearly
triggers. `tests/test_detector_near_misses.py` holds minimal pairs for detectors
without a forbidden-ID fixture: a positive project that must fire and a
near-miss, differing only in the detector's guard, that must not. When you
widen or add a detector guard, add a pair there or a near-miss fixture here.
`tests/test_eval_detection.py` shows each rule of this runner (required,
forbidden, `max_findings`, evidence terms, exit code) can fail.

Fixture `evidence_ids` resolve through `research/incident-claim-ledger.json`.
`scripts/check_claim_ledger.py` validates source-cluster deduplication,
evidence class, confidence/freshness, scenario/check lineage, and reciprocal
fixture links. The fixture runner proves scanner behavior; the ledger validator
proves that experience-report provenance is not merely free-text decoration.
Reports land in `evals/results/detection/`. Repo self-scans must exclude these
intentionally bad fixtures: `./skills/cloudflare-doctor/scripts/cfdoctor_static_scan.py . --exclude evals/fixtures`.

## Paired model value eval

The current matched GPT-5.5 three-way round (`with_skill` current PR, `old_skill` from immutable GitHub `origin/main`, and `without_skill`) is summarized in [`results/gpt-5.5-current-threeway/latest.md`](results/gpt-5.5-current-threeway/latest.md). It uses three fresh isolated runs per visible answer case and variant, paired uncertainty analysis, and a cross-model Claude judge sample. Earlier pinned results remain under [`results/gpt-5.5-value/`](results/gpt-5.5-value/) as historical evidence. The one-shot private release guard is recorded only as a [sanitized aggregate](results/private-release-2026-07-11.md): 2/2 passes, 0.925 blind-judge mean. The evaluation grades diagnostic lift, precision, token/latency overhead, clean/DLQ/no-trigger controls, pricing conflicts, and four Wrangler snapshot behaviors: multi-version Worker reconciliation, Pages/Worker evidence separation, approval-gated collection plans, and Static Assets metadata-only mode. Raw model transcripts stay outside the repository; the checked-in report records the protocol, legacy/new-feature slices, metrics, limitations, and artifact paths.

Qualitative assertions now use an explicit `0.85` threshold instead of the fake-red implicit `1.0`. Every tune answer case also has token and elapsed-time assertions. Keep the multi-dimensional objective/qualitative/efficiency view rather than collapsing value to one pass number.

## Focused Workflow billing comparison

Six `workflow-*` cases in `shared-benchmark.json` exercise built-in retries versus explicit retry loops, rollback handlers, waits/invocations, retention cohorts/overrides, and daily-peak storage. They use synthetic usage records and official Markdown responses captured on 2026-10-18 under `fixtures/benchmark/workflow-billing/`. The billing worksheet oracle checks typed values and arithmetic; the qualitative judge separately checks source interpretation, contradictory prose, unnecessary fixes, and missing account evidence. Oracle unit tests reject wrong values, numeric strings, answer echoes, and duplicate contradictory worksheets.

Use `scripts/focus_workflow_billing_eval.py --baseline <immutable-repo-root> --current <frozen-current-repo-root> --out <temporary-manifest>` to select these cases plus four existing controls. Follow the pinned harness workflow in [`shared-harness.md`](shared-harness.md): validate/leakage-check the manifest, prepare with `--include-old-skill --runs-per-variant 3`, run isolated answers, then grade with script assertions and blind qualitative judgments. Record the baseline commit, skill/input hashes, model and reasoning settings, invocation failures, and reference-read traces. Report the six new cases and four controls separately; use cases as the uncertainty unit rather than treating repeated runs as independent cases.

The two holdout prompts live in gitignored `evals/holdout/workflow-*.md` and must be supplied privately before scoring. Their synthetic usage records and expected behavior are public, so they are split-isolation checks, not independently authored unseen tests. Do not claim behavioral lift from source-anchor checks or a passing test suite alone.

The [2026-10-18 receipt](results/workflow-billing/README.md) preserves the pilot measurement correction, final three-way results, uncertainty, source-drift tests, and reproduction commands. `scripts/judge_workflow_billing_eval.py` uses the shared harness backend with opaque variant labels; keep its raw artifacts outside the repository and use a fresh root after any candidate/rubric/model change.

## Adding cases

Add cases when the trigger policy changes or a false trigger is observed:

```json
{
  "id": "short-name",
  "prompt": "User prompt to test",
  "expected": "trigger",
  "category": "why this matters",
  "description_terms": ["Term that should appear in SKILL.md description"]
}
```

Use `expected: "no_trigger"` for unrelated Cloudflare mentions, false friends like `R2-D2`, generic dynamic-worker/analytics-engine phrases, generic browser/vector/stream tasks, or tasks better handled by another skill.
