# Cloudflare Doctor

Cloudflare Doctor is an Agent Skill plus read-only scanner for auditing Cloudflare projects. It helps an AI coding agent find best-practice drift, wrong primitives, misconfiguration, security/reliability risk, missed optimizations, and cost footguns across Workers, Pages, KV, D1, R2, Durable Objects, Queues, Workflows, Workers AI, AI Gateway, Vectorize, Images, Stream, Browser Run, Dynamic Workers, Agents SDK, Artifacts, CDN/cache, DNS, WAF, Access/Zero Trust, and Cloudflare account/IaC surfaces.

The skill is intentionally source-driven: Cloudflare product behavior, pricing, limits, and best practices must be refreshed from current official Cloudflare docs before final recommendations. War stories are used as scenario prompts, not pricing authority.

## What you get

- `SKILL.md` — runtime instructions and audit output contract.
- `references/` — product-fit rubrics, account evidence guidance, official docs source map, performance/reliability/cost checks, and war-story scenarios.
- `scripts/cfdoctor_static_scan.py` — read-only heuristic scanner for local Cloudflare repos.
- `scripts/eval_skill_trigger.py` — deterministic trigger/description eval for the skill.
- `evals/trigger-cases.json` — positive and negative trigger cases.
- `research/` — source notes used to evolve the audit checklist.

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

The scanner is read-only and heuristic. Treat its output as leads; confirmed findings still need repo/account evidence and current Cloudflare docs.

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
Audit my wrangler.toml for Cloudflare best-practice drift and unsafe bindings.
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
