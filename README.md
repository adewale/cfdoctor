# Cloudflare Doctor

Cloudflare Doctor is an Agent Skill plus read-only scanner for auditing Cloudflare projects. It helps an AI coding agent find best-practice drift, wrong primitives, misconfiguration, security/reliability risk, missed optimizations, and cost footguns across Workers, Pages, KV, D1, R2, Durable Objects, Queues, Workflows, Workers AI, AI Gateway, Vectorize, Images, Stream, Browser Run, Dynamic Workers, Agents SDK, Artifacts, CDN/cache, DNS, WAF, Access/Zero Trust, and Cloudflare account/IaC surfaces.

The skill is intentionally source-driven: Cloudflare product behavior, pricing, limits, and best practices must be refreshed from current official Cloudflare docs before final recommendations. War stories are used as scenario prompts, not pricing authority.

## How to use Cloudflare Doctor

Use it as a **read-only audit partner** when you want Cloudflare-specific judgment, not generic linting:

- **Repo/config audit** — inspect Wrangler config (`wrangler.jsonc` for new projects; JSON/TOML also supported), bindings, Workers/Pages code, IaC, tests, and docs before launch or review.
- **Product-fit review** — ask whether KV, D1, R2, Durable Objects, Queues, Workflows, Vectorize, Workers AI, etc. match the access pattern.
- **Cost and surprise-billing review** — identify billing meters, fanout, retries, AI/browser/media/vector usage, cache misses, and missing cost proxies.
- **Security/reliability posture** — check auth boundaries, preview exposure, WAF/rate-limit evidence, queue/DLQ behavior, cron/loop bounds, and observability.
- **Dashboard/account evidence review** — provide screenshots, API exports, Terraform, `cf-terraforming`, or approved read-only command output for state that is not in the repo.
- **Scanner triage** — run the static scanner for leads, then use the skill to confirm or suppress findings with source context and current docs.

Good prompts are explicit about scope and evidence:

```text
Use Cloudflare Doctor to audit this repo for production launch. Refresh current Cloudflare docs, treat scanner output as leads, include Source basis and Cost / trade-off for every finding, and list dashboard evidence you could not inspect.
```

```text
Audit our Workers AI + Vectorize search path for cost, abuse, cache, rate-limit, and product-fit risks. Assume 50k searches/day unless repo evidence says otherwise.
```

Interpret the output as an evidence-backed risk review: findings should include file/account evidence, Cloudflare-specific failure or billing mechanism, smallest safe fix, cost/trade-off, verification, source basis, and confidence. It is not a substitute for live load testing, billing exports, formal security review, or dashboard/account inspection that you did not provide.

## What you get

- `SKILL.md` — runtime instructions and audit output contract.
- `references/` — product-fit rubrics, account evidence guidance, official docs source map, performance/reliability/cost checks, war-story scenarios, and the check coverage matrix.
- `scripts/cfdoctor_static_scan.py` — read-only Python scanner that parses local Cloudflare configs and source files to generate audit leads with stable check IDs (`--list-checks`, `--json`, `--exclude`).
- `scripts/eval_skill_trigger.py` — deterministic trigger/description eval for the skill.
- `scripts/eval_detection.py` — deterministic detection eval: runs the scanner against known-bad war-story fixtures and a clean baseline.
- `scripts/check_coverage.py` — consistency check between `references/check-coverage-matrix.md` and the scanner's check registry.
- `scripts/check_links.py` — citation link checker (network-dependent; never gates CI unless `--strict`).
- `docs/` — recipes, lessons learned, and the ranked improvement plan with per-change risk analysis.
- `evals/` — trigger cases, shared benchmark manifest, detection fixtures (war-story known-bad projects plus a clean baseline), holdout/holdback placeholders, and saved eval reports.
- `examples/` — copy-paste usage examples.
- `research/` — source notes used to evolve the audit checklist.
- `TODO.md` — remaining and deferred work.

## What is bundled into the Pi skill?

`package.json` declares:

```json
"pi": {
  "skills": ["./"]
}
```

That makes the repository root the skill directory. Pi discovers the root `SKILL.md`, puts only the skill name/description in the startup prompt, and loads the full `SKILL.md` plus adjacent files on demand. When installed from Git, the bundled skill directory includes the repo files above: references, docs, examples, evals, research notes, and helper scripts. There are no npm runtime dependencies; the scanner/eval helpers use Python standard-library modules.


## Agent compatibility

The installable skill directory is `.`. It uses the Agent Skills `SKILL.md` format and is configured for Codex, OpenCode, Pi, Gemini CLI, and Claude Code.

Cloudflare Doctor's canonical skill entry is the repository root `SKILL.md`; the scanner, references, docs, examples, and eval fixtures are intentionally repo-adjacent.

| Agent/client | Install or use |
|---|---|
| Codex | `cp -R . ~/.codex/skills/cloudflare-doctor` |
| OpenCode | `cp -R . ~/.config/opencode/skills/cloudflare-doctor` or use `.opencode/skills/cloudflare-doctor` in a project |
| Pi | `pi install https://github.com/adewale/cfdoctor` or `pi --skill .` |
| Gemini CLI | `gemini skills install https://github.com/adewale/cfdoctor --path .` or copy to `.gemini/skills/cloudflare-doctor` |
| Claude Code | Clone/copy the repo to `.claude/skills/cloudflare-doctor` |

## Usage modes

### Use the installed skill for real audits

Install the latest released version:

```bash
pi install https://github.com/adewale/cfdoctor@v0.2.1
```

Or install the current `main` branch:

```bash
pi install https://github.com/adewale/cfdoctor
```

Then open Pi from the Cloudflare project you want audited and ask for the audit:

```bash
pi "Use Cloudflare Doctor to audit this repo for production launch. Refresh current Cloudflare docs, run the static scan if useful, include Source basis and Cost / trade-off for every finding, and list dashboard/account evidence you could not inspect."
```

In interactive Pi, you can also force-load the skill:

```text
/skill:cloudflare-doctor audit this repo for Workers/D1/Queues cost and reliability risks
```

For one-off local use without installing this repo as a package:

```bash
pi --skill ./SKILL.md "Cloudflare Doctor this repo and tell me where we're wasting money."
```

### Run scanner-only triage

Use the Python scanner when you want a quick read-only inventory/risk lead pass without invoking an agent:

```bash
python3 /path/to/cfdoctor/scripts/cfdoctor_static_scan.py /path/to/cloudflare-project
```

Then feed the scanner output into a Cloudflare Doctor audit if you want sourced recommendations. Scanner output alone is not a final audit.

### Maintain the skill and evals

Repository maintainers can run the local validation suite:

```bash
npm test
```

or the explicit checks:

```bash
python3 -m json.tool package.json
python3 -m json.tool evals/evals.json
python3 -m json.tool evals/trigger-cases.json
python3 -m json.tool evals/shared-benchmark.json
python3 -m py_compile scripts/cfdoctor_static_scan.py scripts/eval_skill_trigger.py scripts/eval_detection.py scripts/check_coverage.py scripts/check_links.py
python3 scripts/eval_skill_trigger.py --out-dir /tmp/cfdoctor-trigger-eval
python3 scripts/eval_detection.py --out-dir /tmp/cfdoctor-detection-eval
./scripts/cfdoctor_static_scan.py . --exclude evals/fixtures
python3 scripts/check_coverage.py
git diff --check -- . ':(exclude)evals/results'
```

Use `npm run update-results` only when you intentionally want to refresh the checked-in eval report artifacts under `evals/results/`.

The shared benchmark manifest is for maintainers who want paired with-skill/without-skill and ablation evaluation. Hidden holdout/holdback prompts are intentionally private and are not required for normal users.

## What to provide for best results

Cloudflare Doctor can audit repo evidence by itself, but stronger audits need the evidence that proves runtime/account state:

- repo/config evidence: `wrangler.jsonc`, `wrangler.json`, legacy `wrangler.toml`, Worker/Pages code, migrations, tests, docs, and IaC;
- usage assumptions: requests/day, routes/jobs/crons that are hot, D1 query volume, AI/vector/media/browser usage, retry/backlog patterns;
- account/dashboard evidence when relevant: redacted screenshots, Terraform/API exports, `cf-terraforming`, billing/product usage exports, WAF/cache/DNS/Access/Logpush settings;
- constraints: acceptable latency, cost ceiling, rollback requirements, migration effort, and whether authenticated read-only Cloudflare commands are approved.

If account evidence is missing, Cloudflare Doctor should mark that scope as **not inspected** rather than infer dashboard state from repo files.

## Run the scanner directly

From the root of a Cloudflare project:

```bash
python3 /path/to/cfdoctor/scripts/cfdoctor_static_scan.py .
```

The Python scanner is a fast triage layer, not the audit itself. It:

- walks local text files while skipping heavy/generated directories such as `.git`, `node_modules`, `.wrangler`, and build outputs;
- parses `wrangler.jsonc`, `wrangler.json`, and legacy `wrangler.toml` configs;
- detects Cloudflare products/bindings and flags heuristic risk patterns in config, source, docs, migrations, and IaC;
- emits leads with stable check IDs for the Cloudflare Doctor skill to confirm, suppress, or escalate (`--json` for machine-readable output, `--list-checks` for the registry, `--exclude REL_PATH` to scope out subtrees such as this repo's intentionally bad eval fixtures).

Coverage status for every check — implemented heuristic vs skill-guidance-only — lives in [`references/check-coverage-matrix.md`](references/check-coverage-matrix.md), enforced by `scripts/check_coverage.py`.

It does **not** fetch current Cloudflare docs, inspect dashboard/account state, know traffic or billing volume, prove a finding, or mutate anything. Confirmed findings still need source context, current Cloudflare docs/pricing, and explicit account/dashboard evidence where applicable.

## Validate this repo

```bash
python3 -m py_compile scripts/cfdoctor_static_scan.py scripts/eval_skill_trigger.py scripts/eval_detection.py scripts/check_coverage.py scripts/check_links.py
python3 scripts/eval_skill_trigger.py --out-dir /tmp/cfdoctor-trigger-eval
python3 scripts/eval_detection.py --out-dir /tmp/cfdoctor-detection-eval
python3 scripts/check_coverage.py
./scripts/cfdoctor_static_scan.py . --exclude evals/fixtures
```

Run `npm run update-results` when the checked-in proof reports should change.

Current proof from the latest validation run (2026-06-10):

- Trigger eval: `39/39 = 100%` (`evals/results/latest.md`).
- Detection eval: `15/15` war-story fixtures pass, including five `gap-*` fixtures that reproduce previously missed code shapes and one dead-RPC review-surface fixture (`evals/results/detection/latest.md`).
- Coverage matrix: consistent with the 57-check scanner registry.
- Static self-scan: `0 findings` with `--exclude evals/fixtures` (the fixtures are intentionally bad; a full scan finds only fixture paths).
- Citation links: 397 checked, dead official-docs links re-pointed, war stories annotated with verified archive snapshots (`evals/results/link-check-2026-06-09.md`).

## Example audit prompts

```text
Audit my wrangler.jsonc for Cloudflare best-practice drift and unsafe bindings.
```

```text
Review our Durable Objects and Agents/RPC code for hibernation mistakes, storage.list hot paths, alarm recursion, hot shards, and dead public cross-boundary RPC methods.
```

```text
Use known Cloudflare/serverless surprise-billing horror stories to audit our Cloudflare setup for similar risks.
```

More examples are in [`docs/recipes.md`](docs/recipes.md) and [`examples/README.md`](examples/README.md).

## Safety model

Cloudflare Doctor defaults to read-only work:

- local repo inspection and static scans are safe;
- unauthenticated Cloudflare docs fetches are expected;
- authenticated Cloudflare account reads require explicit approval;
- deploys, binding changes, DNS/WAF/cache mutations, purges, secret rotation, and other account mutations require explicit user approval.

The skill also refuses to infer dashboard/account state from repository files alone. If DNS, WAF, Access, cache rules, Logpush, or billing evidence is missing, it reports that scope as not inspected and asks for the smallest useful evidence package.

## Repository status

This repo is public, usable as a Git-installed Pi package, and licensed under the MIT License. See [`LICENSE`](LICENSE).
