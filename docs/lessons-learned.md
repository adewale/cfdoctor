# Lessons Learned

## What we learned in the eval-harness, Wrangler config, and scanner-role pass

This pass started as a PR review, then turned into a small but useful hardening loop: the shared eval harness made the audit contract more testable, the Wrangler examples were updated to match current Cloudflare docs, and the scanner documentation was tightened so users know what the Python tool can and cannot prove.

### Eval assertions must track the audit contract exactly

The skill had already made `Cost / trade-off` mandatory for every confirmed finding, but the first shared benchmark assertions only checked for `Evidence`, `Fix`, `Verify`, and `Source basis`. That left a gap: an answer could pass the benchmark while omitting one of the most important fields in the current output contract.

The lesson is: **contract evals must assert every mandatory contract field, not just the older or easiest-to-match ones**. When the audit format changes, update the skill text, examples, and eval assertions together.

### Current platform defaults should shape examples, not historical muscle memory

The README and trigger eval used `wrangler.toml` because that was the familiar historical config filename. Current Cloudflare docs say Wrangler supports JSON, JSONC, and TOML, but recommends `wrangler.jsonc` for new projects and notes that some newer Wrangler features are only available to JSON config users.

The lesson is: **examples teach defaults**. If the docs recommend `wrangler.jsonc` for new projects, public examples should use `wrangler.jsonc` while still making clear that JSON and legacy TOML remain supported audit inputs.

Source basis: https://developers.cloudflare.com/workers/wrangler/configuration/index.md

### Legacy support belongs in scanners even when examples move forward

Changing examples to `wrangler.jsonc` does not mean the scanner should ignore `wrangler.toml`. Real Cloudflare repos still contain TOML configs, and audit tools need to inspect what exists, not only what new projects should create.

The right split is:

- README/new-project examples: prefer `wrangler.jsonc`
- scanner and audit playbook: inspect `wrangler.jsonc`, `wrangler.json`, and legacy `wrangler.toml`
- recommendations: cite current docs before calling a format preferred, legacy, or feature-limited

The lesson is: **use current defaults for guidance, but broad compatibility for evidence collection**.

### The Python scanner is a triage layer, not the Doctor

The scanner walks local text, parses Wrangler config, inventories products/bindings, and flags heuristic risk patterns. It deliberately does not fetch current docs, inspect account/dashboard state, know traffic volume, know billing data, or prove a finding. That distinction needed to be explicit in the README, recipes, and script docstring.

The lesson is: **a scanner can make suspicious patterns cheap to find, but only the audit workflow can turn a lead into a sourced finding**. Scanner output should be framed as leads to confirm, suppress, or escalate.

### Fixtures should not pollute self-scan signal

Adding a Wrangler fixture for dashboard-claim eval coverage made the repo self-scan start treating the fixture as a real Worker config. That was correct scanner behavior but noisy validation behavior until the fixture declared intentional observability.

The lesson is: **fixture repos are still repo files**. If a self-scan traverses fixtures, either make fixtures intentionally clean or isolate them from scanner scope. Otherwise test data becomes a source of false repository-health noise.

### Bundled skill contents need an explicit mental model

Pi packages progressively disclose skills: the startup prompt sees the skill name and description, then the model reads `SKILL.md`, and only then loads references/scripts/docs as needed. Because `cfdoctor` declares `"pi": { "skills": ["./"] }`, the repository root is the skill directory and adjacent files are available to the skill even though they are not all injected up front.

The lesson is: **document what is bundled and what is loaded**. Users need to know that references, docs, evals, examples, research, and helper scripts ship with the Git-installed package, but the model still has to read/run them on demand.

## What we learned in the check-ID, detection-fixture, and false-negative pass

This pass (2026-06-09) gave every scanner finding a stable check ID, built a
fixture-based detection eval, verified every citation link, routed SKILL.md
references by detected product, and then used the new fixtures to find and fix
five real scanner false negatives.

### Rank work by verifiability, not appeal

Ordering the improvements by "can a command prove this worked" pushed the
plumbing (check IDs, fixtures, consistency checkers) ahead of the more
exciting ideas (account-state collector), and that ordering was right: each
later item consumed the verified output of an earlier one, and the one item
nothing could verify (the collector) was the one worth deferring entirely.

### Fixtures must be written from the failure, not from the regex

The detection fixtures were written as idiomatic code modeling documented war
stories first, and only then checked against the scanner. That discipline is
what surfaced five false negatives — fixtures reverse-engineered from the
scanner's own patterns would have passed immediately and proven nothing. The
follow-up rule is now in the recipes: to fix a false negative, commit a
failing `gap-*` fixture first, then fix the heuristic.

### Heuristic fixes trade precision for recall — say so where users look

Widening the Stream-preload check to work across files also made it fire on
non-Stream video tags in repos that mention a Stream host anywhere. That
trade-off is acceptable for a leads-generator, but only because it is written
down next to the check in the coverage matrix. A widened heuristic with an
undocumented precision cost is a future trust bug.

### Plans are records — correct them in place

The plan assumed the holdout/holdback eval directories were empty
placeholders; they turned out to be intentionally gitignored with a working
split policy. The fix was to amend the plan item in place with the correction
dated, not to quietly skip it. The plan doc is only useful later if it says
what was actually true.

### Updated lesson list

1. Contract evals must assert every mandatory output field, including newly-added fields like `Cost / trade-off`.
2. Public examples should follow current platform defaults; for new Wrangler projects, use `wrangler.jsonc`.
3. Evidence collection should remain backward-compatible with real repos, including legacy `wrangler.toml`.
4. The Python scanner is a read-only lead generator, not a proof engine or replacement for sourced audit judgment.
5. Eval fixtures that live in the repo can affect self-scan results and should be intentionally clean or scoped out.
6. Pi skill packaging is progressive disclosure: `SKILL.md` is discovered, adjacent files are bundled, and references/scripts load on demand.
7. Rank improvement work by verifiability; defer what nothing in the environment can prove.
8. Detection fixtures must model the documented failure, not the detector — and false-negative fixes start with a failing fixture.
9. Document every precision/recall trade-off next to the check it affects, in the coverage matrix.
10. Plan documents are records: correct wrong premises in place, dated, instead of silently dropping items.

## What we learned in the launch-backlog and usage-documentation pass

The final launch cleanup looked administrative — license, CI, repository metadata, release tag, and usage docs — but it exposed one more product lesson: a skill repo is both a tool and a distribution artifact. Users need to know how to consume it; maintainers need to know how to verify it; neither group should have to reverse-engineer that from package metadata.

### A release tag is part of the API

`pi install https://github.com/adewale/cfdoctor` is convenient, but it tracks the moving default branch. Once the repo is public, users also need a stable install target like `@v0.1.0` so they can pin behavior and update intentionally.

The lesson is: **for installable skills, tags and releases are user-facing API, not ceremonial GitHub decoration**.

### Usage docs must separate user paths from maintainer paths

The README originally documented installation, scanner execution, and validation, but not the mental model connecting them. That left a reasonable question: is a normal user expected to run the shared benchmark, provide private holdout prompts, run the scanner, or just install the skill and ask for an audit?

The right split is explicit:

- normal users install the skill and ask for an audit from the target repo
- scanner-only users run the Python scanner for quick read-only triage
- maintainers run validation, shared benchmarks, trigger evals, and ablations
- private holdout/holdback prompts are maintainer eval assets, not usage prerequisites

The lesson is: **if a repo contains both product files and evaluation machinery, the README must say which parts are for users and which parts are for maintainers**.

### Repository settings are documentation surfaces

Topics, homepage, wiki state, license detection, and release state all shape how the project is understood before anyone reads `SKILL.md`. Leaving the wiki enabled, omitting topics, or lacking a license does not break the skill, but it creates ambiguity about where documentation lives and how the code can be used.

The lesson is: **repository metadata is part of launch readiness because it tells users where to look, what they may do, and whether the project is maintained intentionally**.

### CI should run the same checks maintainers ask humans to run

Adding CI was straightforward because the repo already had a small, deterministic validation loop: JSON manifests, Python compile, trigger eval, static self-scan, and `git diff --check`. That made the automated workflow less a new system and more a codified version of the existing release ritual.

The lesson is: **CI is most useful when it automates the exact validation commands documented for maintainers**.

### Updated lesson list addendum

11. Release tags are part of the install API for Git-installed skills.
12. READMEs for skill repos must distinguish normal usage, scanner-only triage, and maintainer eval workflows.
13. Private holdout/holdback eval prompts are not user prerequisites and should be documented as maintainer-only assets.
14. Repository metadata — topics, homepage, wiki state, license, release — is a documentation surface.
15. CI should codify the same deterministic checks maintainers are told to run locally.
