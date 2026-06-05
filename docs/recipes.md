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
Inspect our Durable Objects for WebSocket hibernation/close hygiene, storage.list hot paths, alarm recursion, hot shards, one-object-per-idempotency-key patterns, storage batching, fanout to many objects, and KV-vs-DO storage fit.
```

Pair with DO class code, Wrangler migrations, object naming strategy, and metrics for requests/duration/storage ops.

## Dashboard/account evidence request

```text
Cloudflare Doctor this repo, but do not infer dashboard settings from code. Tell me the smallest redacted evidence package you need for DNS, WAF, Access, cache rules, Logpush, billing, and product usage.
```

Use before authenticated commands or screenshots. The skill should ask for exact evidence and mark missing account state as not inspected.

## Static scan only

```bash
python3 /path/to/cfdoctor/scripts/cfdoctor_static_scan.py .
```

Use in CI or as a pre-audit smoke check. Scanner findings are leads, not proof.

## Trigger eval maintenance

```bash
python3 scripts/eval_skill_trigger.py
```

Run after editing `SKILL.md` or `evals/trigger-cases.json`. Current expected result is 100% proxy accuracy with no missing description terms.
