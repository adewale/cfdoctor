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

### Updated lesson list

1. Contract evals must assert every mandatory output field, including newly-added fields like `Cost / trade-off`.
2. Public examples should follow current platform defaults; for new Wrangler projects, use `wrangler.jsonc`.
3. Evidence collection should remain backward-compatible with real repos, including legacy `wrangler.toml`.
4. The Python scanner is a read-only lead generator, not a proof engine or replacement for sourced audit judgment.
5. Eval fixtures that live in the repo can affect self-scan results and should be intentionally clean or scoped out.
6. Pi skill packaging is progressive disclosure: `SKILL.md` is discovered, adjacent files are bundled, and references/scripts load on demand.
