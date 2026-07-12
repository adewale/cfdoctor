# Private release evaluation — sanitized aggregate

- Date: 2026-07-11
- Answer model: `openai-codex/gpt-5.5`
- Blind judge: Claude Sonnet via Claude Code 2.1.116
- Current skill material: `9c4ea771a6ef3697035d49cf39067195df72c34cea354cf093cff47a1499b34c`
- Protocol: one successful answer and one blind judgment for each of one private holdout and one private holdback; threshold `0.85`
- Result: **2/2 passed**; judge mean **0.925** (scores `0.88`, `0.97`)
- Forbidden-behavior observations: **0**

The prompts, answer key, outputs, transcripts, and judge rationales remain outside Git. Raw scored artifacts are stored at `/tmp/cfdoctor-private-release-holdout-20260711` with mode `0700`; files use mode `0600`.

## Integrity hashes

| Artifact class | SHA-256 |
|---|---|
| Answer A | `dcdb61d001d5d3e440a059402e2620ef0861233469d074ff6f236b41c3bbe592` |
| Answer B | `44566d89f019b749f8c17c86f62a11bccc02b29fe97a517b42c8d2fbe29510fd` |
| Judgment A | `518f43e2c69c1def8a532acb4ef58726842c2effa8cd14b9b62ee1eb5edab133` |
| Judgment B | `ccce78e19cb8c8b2a3b4f73da5fa2bee43e3d7bfb877991b8211050b492ff1f7` |

This tiny private sample is a release guard, not a generalization claim. It was scored exactly once and must not be retuned or rerun as a replacement test set.
