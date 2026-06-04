# Cloudflare Doctor evals

These evals follow the skill-creator loop: define trigger prompts, run a quantitative pass, inspect failures, improve `SKILL.md`, and repeat.

## Trigger eval

Run:

```bash
python3 scripts/eval_skill_trigger.py
```

Inputs:
- `evals/trigger-cases.json` — positive and negative trigger prompts.
- `SKILL.md` — frontmatter description under test.

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

Use `expected: "no_trigger"` for unrelated Cloudflare mentions, false friends like `R2-D2`, generic browser/vector/stream tasks, or tasks better handled by another skill.
