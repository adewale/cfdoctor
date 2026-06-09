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
- `references/` — product-fit rubrics, account evidence guidance, official docs source map, performance/reliability/cost checks, and war-story scenarios.
- `scripts/cfdoctor_static_scan.py` — read-only Python scanner that parses local Cloudflare configs and source files to generate audit leads.
- `scripts/eval_skill_trigger.py` — deterministic trigger/description eval for the skill.
- `docs/` — recipes and lessons learned.
- `evals/` — trigger cases, shared benchmark manifest, holdout/holdback placeholders, fixtures, and saved trigger-eval reports.
- `examples/` — copy-paste usage examples.
- `research/` — source notes used to evolve the audit checklist.

## What is bundled into the Pi skill?

`package.json` declares:

```json
"pi": {
  "skills": ["./"]
}
```

That makes the repository root the skill directory. Pi discovers the root `SKILL.md`, puts only the skill name/description in the startup prompt, and loads the full `SKILL.md` plus adjacent files on demand. When installed from Git, the bundled skill directory includes the repo files above: references, docs, examples, evals, research notes, and helper scripts. There are no npm runtime dependencies; the scanner/eval helpers use Python standard-library modules.

## Install as a Pi skill

From GitHub:

```bash
pi install https://github.com/adewale/cfdoctor
```

For one-off local use without installing:

```bash
pi --skill ./SKILL.md
```

Then ask for an audit, for example:

```text
Cloudflare Doctor this repo and tell me where we're wasting money.
```

## Run the scanner directly

From the root of a Cloudflare project:

```bash
python3 /path/to/cfdoctor/scripts/cfdoctor_static_scan.py .
```

The Python scanner is a fast triage layer, not the audit itself. It:

- walks local text files while skipping heavy/generated directories such as `.git`, `node_modules`, `.wrangler`, and build outputs;
- parses `wrangler.jsonc`, `wrangler.json`, and legacy `wrangler.toml` configs;
- detects Cloudflare products/bindings and flags heuristic risk patterns in config, source, docs, migrations, and IaC;
- emits leads for the Cloudflare Doctor skill to confirm, suppress, or escalate.

It does **not** fetch current Cloudflare docs, inspect dashboard/account state, know traffic or billing volume, prove a finding, or mutate anything. Confirmed findings still need source context, current Cloudflare docs/pricing, and explicit account/dashboard evidence where applicable.

## Validate this repo

```bash
python3 -m py_compile scripts/cfdoctor_static_scan.py scripts/eval_skill_trigger.py
python3 scripts/eval_skill_trigger.py
./scripts/cfdoctor_static_scan.py .
```

Current proof from the latest validation run:

- Trigger eval: `38/38 = 100%` (`evals/results/latest.md`).
- Static self-scan: `0 findings` on this repository.

## Example audit prompts

```text
Audit my wrangler.jsonc for Cloudflare best-practice drift and unsafe bindings.
```

```text
Review our Durable Objects WebSocket code for hibernation mistakes, storage.list hot paths, alarm recursion, and hot shards.
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

This repo is public and usable as a Git-installed Pi package. A formal open-source license has not been selected yet; until a root `LICENSE` file is added, default copyright rules apply.
