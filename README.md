# Cloudflare Doctor

Cloudflare Doctor is an Agent Skill plus read-only scanner for auditing Cloudflare projects. It helps an AI coding agent find best-practice drift, wrong primitives, misconfiguration, security/reliability risk, missed optimizations, and cost footguns across Workers, Pages, Static Assets, KV, D1, R2, Durable Objects, Queues, Workflows, Workers AI, AI Gateway, Vectorize, Images, Stream, Browser Run, Dynamic Workers, Containers, Pipelines, Workers VPC, Email bindings, Secrets Store, Agents SDK, Artifacts, CDN/cache, DNS, WAF, Access/Zero Trust, and Cloudflare account/IaC surfaces.

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

- `skills/cloudflare-doctor/SKILL.md` — runtime instructions and audit output contract.
- `skills/cloudflare-doctor/references/` — product-fit rubrics, account evidence guidance, official docs source map, performance/reliability/cost checks, war-story scenarios, and the check coverage matrix.
- `skills/cloudflare-doctor/scripts/cfdoctor_static_scan.py` — read-only Python scanner that parses local Cloudflare configs and source files to generate audit leads with stable check IDs (`--list-checks`, `--json`, `--exclude`).
- `scripts/eval_skill_trigger.py` — deterministic trigger/description eval for the skill.
- `scripts/eval_detection.py` — deterministic detection eval: runs the scanner against known-bad war-story fixtures and a clean baseline.
- `scripts/check_coverage.py` — consistency check between `skills/cloudflare-doctor/references/check-coverage-matrix.md` and the scanner's check registry.
- `scripts/check_claim_ledger.py` — validates stable evidence/source-cluster IDs, source quality, confidence dimensions, scenario/check/fixture lineage, and freshness in `research/incident-claim-ledger.json`.
- `scripts/capture_wrangler_snapshot.py` — explicitly approved, private Wrangler snapshot wrapper for deployed Worker/Pages config and secret names, Worker active versions/bindings/limits, and Pages deployments; it never installs Wrangler or mutates Cloudflare state.
- `scripts/check_links.py` — checks the installable runtime references plus current research/docs, excluding historical generated reports; optional semantic anchors detect critical official-doc content drift.
- `docs/` — recipes, lessons learned, and the ranked improvement plan with per-change risk analysis.
- `evals/` — trigger cases, shared benchmark manifest, detection fixtures (war-story known-bad projects plus a clean baseline), gitignored private holdout/holdback assets, and saved sanitized eval reports.
- `examples/` — copy-paste usage examples.
- `research/` — source notes used to evolve the audit checklist.
- `TODO.md` — remaining and deferred work.

## What is bundled into the Pi skill?

`package.json` declares:

```json
"pi": {
  "skills": ["./skills/cloudflare-doctor"]
}
```

That makes `skills/cloudflare-doctor` the skill directory. Pi discovers `skills/cloudflare-doctor/SKILL.md`, puts only the skill name/description in the startup prompt, and loads the full `SKILL.md` plus adjacent runtime references/scripts on demand. Repo-only evals, research notes, docs, and saved results stay outside the installable skill boundary. There are no npm runtime dependencies; the scanner uses Python standard-library modules.


## Agent compatibility

The installable skill directory is `skills/cloudflare-doctor`. It uses the Agent Skills `SKILL.md` format and is configured for Codex, OpenCode, Pi, Gemini CLI, and Claude Code.

Cloudflare Doctor's canonical skill entry is `skills/cloudflare-doctor/SKILL.md`; the scanner and references are adjacent to that entrypoint, while docs, examples, eval fixtures, research notes, and saved results remain repo-only.

| Agent/client | Install or use |
|---|---|
| Codex | `cp -R skills/cloudflare-doctor ~/.codex/skills/cloudflare-doctor` |
| OpenCode | `cp -R skills/cloudflare-doctor ~/.config/opencode/skills/cloudflare-doctor` or use `.opencode/skills/cloudflare-doctor` in a project |
| Pi | `pi install https://github.com/adewale/cfdoctor` or `pi --skill skills/cloudflare-doctor` |
| Gemini CLI | `gemini skills install https://github.com/adewale/cfdoctor --path skills/cloudflare-doctor` or copy to `.gemini/skills/cloudflare-doctor` |
| Claude Code | `cp -R skills/cloudflare-doctor ~/.claude/skills/cloudflare-doctor` |

## Usage modes

### Use the installed skill for real audits

Install the latest released version:

```bash
pi install https://github.com/adewale/cfdoctor@v0.3.0
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
pi --skill ./skills/cloudflare-doctor/SKILL.md "Cloudflare Doctor this repo and tell me where we're wasting money."
```

### Run scanner-only triage

Use the Python scanner when you want a quick read-only inventory/risk lead pass without invoking an agent:

```bash
python3 /path/to/cfdoctor/skills/cloudflare-doctor/scripts/cfdoctor_static_scan.py /path/to/cloudflare-project
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
python3 -m py_compile skills/cloudflare-doctor/scripts/cfdoctor_static_scan.py scripts/eval_skill_trigger.py scripts/eval_detection.py scripts/check_coverage.py scripts/check_claim_ledger.py scripts/capture_wrangler_snapshot.py scripts/check_links.py
python3 -m unittest discover -s tests
python3 scripts/eval_skill_trigger.py --out-dir /tmp/cfdoctor-trigger-eval
python3 scripts/eval_detection.py --out-dir /tmp/cfdoctor-detection-eval
./skills/cloudflare-doctor/scripts/cfdoctor_static_scan.py . --exclude evals/fixtures
python3 scripts/check_coverage.py
python3 scripts/check_claim_ledger.py
python3 scripts/check_links.py --validate-policy
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

## Capture deployed Worker or Pages state

Use the project-pinned Wrangler executable. Review the static authenticated-read plan first; for Workers, Wrangler expands the displayed `versions view <ACTIVE_VERSION_ID>` shape after reading deployment status. Then write the snapshot to a private directory outside Git:

```bash
python3 scripts/capture_wrangler_snapshot.py \
  --kind worker --name my-worker --output-dir /tmp/cfdoctor-my-worker \
  --wrangler ./node_modules/.bin/wrangler --plan

python3 scripts/capture_wrangler_snapshot.py \
  --kind worker --name my-worker --output-dir /tmp/cfdoctor-my-worker \
  --wrangler ./node_modules/.bin/wrangler --approve-authenticated-read
```

Use `--kind pages` for Pages. Metadata-only collection is the default; add `--include-source-config` to the reviewed plan and capture command only when deployed Worker source/config or experimental Pages config is necessary and explicitly accepted. Worker snapshots compare repository intent with active-version metadata and, when opted in, downloaded dashboard configuration; Pages snapshots compare intent with deployment history and optional downloaded config. The snapshot can contain plain vars, routes, resource names, secret names, account metadata, and—when opted in—deployed source, so review `REVIEW_BEFORE_SHARING.txt` and redact before sharing. See [`research/wrangler-state-snapshot.md`](research/wrangler-state-snapshot.md).

## Run the scanner directly

From the root of a Cloudflare project:

```bash
python3 /path/to/cfdoctor/skills/cloudflare-doctor/scripts/cfdoctor_static_scan.py .
```

The Python scanner is a fast triage layer, not the audit itself. It:

- walks local text files while skipping heavy/generated directories such as `.git`, `node_modules`, `.wrangler`, and build outputs;
- parses `wrangler.jsonc`, `wrangler.json`, and legacy `wrangler.toml` configs;
- detects Cloudflare products/bindings and flags heuristic risk patterns in config, source, docs, migrations, and IaC;
- emits leads with stable check IDs for the Cloudflare Doctor skill to confirm, suppress, or escalate (`--json` for machine-readable output, `--list-checks` for the registry, `--exclude REL_PATH` to scope out subtrees such as this repo's intentionally bad eval fixtures).

Coverage status for every check — implemented heuristic vs skill-guidance-only — lives in [`skills/cloudflare-doctor/references/check-coverage-matrix.md`](skills/cloudflare-doctor/references/check-coverage-matrix.md), enforced by `scripts/check_coverage.py`.

It does **not** fetch current Cloudflare docs, inspect dashboard/account state, know traffic or billing volume, prove a finding, or mutate anything. Confirmed findings still need source context, current Cloudflare docs/pricing, and explicit account/dashboard evidence where applicable.

## Validate this repo

```bash
python3 -m py_compile skills/cloudflare-doctor/scripts/cfdoctor_static_scan.py scripts/eval_skill_trigger.py scripts/eval_detection.py scripts/check_coverage.py scripts/check_claim_ledger.py scripts/capture_wrangler_snapshot.py scripts/check_links.py
python3 -m unittest discover -s tests
python3 scripts/eval_skill_trigger.py --out-dir /tmp/cfdoctor-trigger-eval
python3 scripts/eval_detection.py --out-dir /tmp/cfdoctor-detection-eval
python3 scripts/check_coverage.py
python3 scripts/check_claim_ledger.py
python3 scripts/check_links.py --validate-policy
./skills/cloudflare-doctor/scripts/cfdoctor_static_scan.py . --exclude evals/fixtures
```

Run `npm run update-results` when the checked-in proof reports should change.

Current proof from the latest validation run (2026-08-10; model-based evals from 2026-07-11):

- Trigger eval: `39/39 = 100%` (`evals/results/latest.md`).
- Detection eval: `28/28` fixtures pass, including valid/malformed JSONC, Queue-DLQ controls, deeper DO sharding, per-consumer Queue matching, alarm guard precision, linked Stream preload, indirect self-fetch, full observability sampling, credential-reference precision, and the unindexed-D1/cached-layout pair (`evals/results/detection/latest.md`).
- Sonnet fixture spot-check (2026-08-10): 18 matched audits over the two new D1 fixtures (current skill vs `origin/main` skill vs no skill, 3 runs each). The scenario-24 planner-statistics lesson (`ANALYZE`/`sqlite_stat1`) appeared in 3/3 current-skill audits of the unindexed fixture versus 0/6 without the change; incident-sourced basis 3/3 versus 0/6; zero false positives on the remediated control across all 9 runs (`evals/results/sonnet-d1-fixture-2026-08-10.md`).
- Coverage matrix: consistent with the 62-check scanner registry.
- Evidence ledger: 29 structured records cover all 24 checklist scenarios and 28 detection fixtures with reciprocal lineage; newer records add direct D1 cost, Durable Object alarm, product-fit, three first-party Cloudflare outage postmortems, and an explicit superseded-evidence disposition.
- Wrangler snapshot wrapper: 14 offline tests cover explicit approval/planning, exact Worker/Pages command shapes, profile forwarding, metadata-only-by-default behavior, opt-in Worker config/source and Pages config capture, active-version metadata, environment isolation, version/active-state failure gates, symlink removal, recursive private permissions, and Git-worktree refusal. Approved private live runs completed against `readability-worker` (Wrangler 4.71.0), `atlas` (4.94.0), and `keyboardia-staging` (4.53.0); only sanitized shapes were retained.
- Skill Eval Harness: v0.6.0 strict leakage/ablation validation and manifest audit pass across 37 cases / 6 ablations.
- Current matched GPT-5.5 three-way eval: 31 visible answer cases × 3 variants × 3 runs = 279 fresh answers and 243 primary judgments. Current PR scored 89.15% objective / 89.69% combined, versus pinned `origin/main` 81.79% / 83.00% and no skill 72.97% / 69.24%. Paired objective lift was +7.36 points versus main (`p=0.000270`) and +16.17 versus no skill (`p=0.000010`). The Wrangler slice scored 93.01% versus 63.96% main and 60.53% no skill; legacy current/main remained compatible (`p=0.107439`). A 27-case Claude judge sample agreed with GPT on 26/27 pass decisions. The one-shot private release guard passed 2/2 with a 0.925 blind-judge mean. See `evals/results/gpt-5.5-current-threeway/latest.md` and `evals/results/private-release-2026-07-11.md`; earlier reports under `gpt-5.5-value/` are pinned historical evidence.
- Static self-scan: `0 findings` with `--exclude evals/fixtures` (the fixtures are intentionally bad; a full scan finds only fixture paths).
- Current-source links: 477 checked across 33 runtime/research/docs/evidence files, 0 dead/errors; all 11 critical official-doc semantic anchors passed on 2026-07-11. Generated/private eval paths and authenticated runtime API templates are excluded from current network health.

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
