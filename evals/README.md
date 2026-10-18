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

## Private/background D1 investigations

The five `private-d1-*` tune cases provide synthetic code, schema, plans, and row measurements for private polling, deep OFFSET pagination, repeated full syncs, indexed updates, and safe controls. Prompts start from ambiguous usage symptoms; fixture inputs do not supply the diagnosis or derived exposure arithmetic. These are agent-reasoning cases, not static-scanner detections or an incident replay.

Materialize the focused manifest at the repository root, where the pinned harness can resolve its relative ablation paths:

```bash
python3 scripts/focus_private_d1_eval.py --out .private-d1-focused.json
```

Use the repository-pinned harness from `package.json` to validate it, prepare paired `with_skill` / `without_skill` tasks and the `no-private-d1-cost-accounting` ablation, execute fresh isolated answers, and grade with `--allow-scripts`. The ablation removes the new mandatory accounting instructions and diagnosis routing; existing reference guidance remains, so it tests their incremental contribution. Expected behavior and oracle code are grading inputs, never answer-generation inputs.

The structural oracle checks path-specific evidence, separate read/write exposure, sampled-versus-enforced bounds, remediation, and precision controls. Negative unit tests guard plausible wrong diagnoses and arithmetic. These checks do not prove unrestricted prose correct or establish model lift. Report execution success, structural results, qualitative review, and efficiency separately; a smoke run or a reused tune case is not an independent holdout.

The [2026-10-18 smoke receipt](results/private-d1-investigations/README.md) retains all five outputs, initial structural failures, parser repairs, revised grading, and the native-runner authentication limitation. It makes no paired-effectiveness claim.

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
