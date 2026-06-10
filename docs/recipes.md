# Cloudflare Doctor recipes

Copy these prompts into Pi after installing this repo as a skill.

## Full repo audit

```text
Cloudflare Doctor this repo. Inspect Wrangler config, bindings, runtime code, migrations, tests, and docs. Separate confirmed findings from questions, refresh current Cloudflare docs, and include Source basis for every recommendation.
```

Good when you want the full audit scaffold: inspected scope, missing dashboard evidence, detected products, cost proxy summary, findings, cache map, and next actions.

## Cost-footgun review

```text
Review this Cloudflare project for surprise-billing risks. Focus on Workers CPU/subrequests, D1 rows read, R2/KV operations, Durable Object duration/storage, Queue retries, Workers AI, Browser Run, Images/Stream, Vectorize, logs, and preview/demo environments.
```

Use when spend is high or traffic patterns changed. The answer should identify meters and amplification mechanisms rather than invent dollar estimates.

## Durable Objects deep dive

```text
Inspect our Durable Objects for WebSocket hibernation/close hygiene, storage.list hot paths, alarm recursion, hot shards, one-object-per-idempotency-key patterns, storage batching, fanout to many objects, KV-vs-DO storage fit, and dead public cross-boundary RPC methods.
```

Pair with DO class code, Wrangler migrations, object naming strategy, and metrics for requests/duration/storage ops. For TypeScript repos with `DurableObject`, `WorkerEntrypoint`, `WorkflowEntrypoint`, `RpcTarget`, or Agents SDK classes, optionally approve a read-only third-party analyzer:

```bash
npx @acoyfellow/deadlint . --check dead-rpc --json
```

Treat its output as reachability leads. Before deleting a method, check for dynamic dispatch, frontend companion files, API docs, old deployed versions, and callers in other repositories.

## Dashboard/account evidence request

```text
Cloudflare Doctor this repo, but do not infer dashboard settings from code. Tell me the smallest redacted evidence package you need for DNS, WAF, Access, cache rules, Logpush, billing, and product usage.
```

Use before authenticated commands or screenshots. The skill should ask for exact evidence and mark missing account state as not inspected.

## Static scan only

```bash
python3 /path/to/cfdoctor/scripts/cfdoctor_static_scan.py .
```

Use in CI or as a pre-audit smoke check. The Python scanner parses local `wrangler.jsonc`, `wrangler.json`, and legacy `wrangler.toml` configs plus source/docs/IaC text to build a product inventory and heuristic risk leads. Every finding carries a stable check ID from the registry (`--list-checks`); add `--json` for machine-readable output and `--exclude REL_PATH` to scope out subtrees (when scanning this repo itself, use `--exclude evals/fixtures` — the detection fixtures are intentionally bad). Scanner findings are leads, not proof: they do not replace current Cloudflare docs, account/dashboard evidence, traffic/billing data, or the full Cloudflare Doctor audit contract.

## Trigger eval maintenance

```bash
python3 scripts/eval_skill_trigger.py --out-dir /tmp/cfdoctor-trigger-eval
```

Run after editing `SKILL.md` or `evals/trigger-cases.json`. Current expected result is 100% proxy accuracy with no missing description terms. Use `npm run update-results` only when the checked-in report under `evals/results/` should be refreshed.

## Detection eval and coverage maintenance

```bash
python3 scripts/eval_detection.py --out-dir /tmp/cfdoctor-detection-eval
python3 scripts/check_coverage.py
```

Run after changing scanner heuristics, fixtures, or the coverage matrix. The detection eval must pass every fixture under `evals/fixtures/detection/` (including the `clean-baseline` false-positive guard), and the coverage checker must report the matrix consistent with the scanner registry. When fixing a scanner false negative, add a failing `gap-*` fixture first, then fix the heuristic. Use `npm run update-results` only when the checked-in report under `evals/results/detection/` should be refreshed.
