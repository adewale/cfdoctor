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

Fixture `evidence_ids` resolve through `research/incident-claim-ledger.json`.
`scripts/check_claim_ledger.py` validates source-cluster deduplication,
evidence class, confidence/freshness, scenario/check lineage, and reciprocal
fixture links. The fixture runner proves scanner behavior; the ledger validator
proves that experience-report provenance is not merely free-text decoration.
Reports land in `evals/results/detection/`. Repo self-scans must exclude these
intentionally bad fixtures: `./skills/cloudflare-doctor/scripts/cfdoctor_static_scan.py . --exclude evals/fixtures`.

## Paired model value eval

The latest GPT-5.5 three-way round (`with_skill` local, `old_skill` from GitHub `origin/main`, and `without_skill`) is summarized in [`results/gpt-5.5-value/latest.md`](results/gpt-5.5-value/latest.md). It grades diagnostic lift, precision, token/latency overhead, and the requested clean/DLQ/no-trigger fixes. Raw model transcripts stay outside the repository; the checked-in report records the protocol, metrics, limitations, and artifact paths.

Qualitative assertions now use an explicit `0.85` threshold instead of the fake-red implicit `1.0`. Every tune answer case also has token and elapsed-time assertions. Keep the multi-dimensional objective/qualitative/efficiency view rather than collapsing value to one pass number.

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
