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

## Isolate memory and startup baseline probe

```text
Cloudflare Doctor this repo for isolate memory load. Our Durable Objects are reset for exceeding memory (or: Wrangler rejects deploys with "Script startup exceeded CPU time limit"). Separate module-scope baseline from request data, check request-path buffering, tell me what to measure before refactoring, and give me the smallest safe fix.
```

Pair with the Wrangler config, the tool/schema registry modules, workspace `package.json` files, barrel files, and (if available) the Workers or Durable Objects memory chart with deployment markers. The scanner leads `CFDOC-PERF-MODULE-SCOPE-SCHEMA-WEIGHT` and `CFDOC-PERF-BODY-BUFFERING` are counts and patterns, not heap figures; the audit should ask for a measurement before recommending a rewrite.

Cheap first pass (no account access, no third-party code):

```bash
# Emit the exact bundle a deploy would upload, with its module graph, and report compressed size
npx wrangler deploy --dry-run --outdir /tmp/cfdoctor-bundle --metafile /tmp/cfdoctor-bundle/meta.json
# Profile the global scope against the 1 s startup limit (writes a .cpuprofile for DevTools/VS Code)
npx wrangler check startup
```

`wrangler deploy` and `versions upload` also print `startup_time_ms` and `Total Upload` on every run; keep them in the deploy log so regressions show up next to the commit that caused them.

Module-scope heap probe on the emitted bundle (adapted from the Polylane write-up; Node-only, no dependencies beyond Node and Wrangler; compare deltas between runs, not absolutes against production):

1. Build with the dry-run command above. If the import graph is fully static, esbuild emits no lazy `__esm` wrappers and per-module attribution is impossible; build from a probe entry that reaches the real entry through a dynamic import and exports a placeholder Durable Object class so Wrangler's export check passes:
   ```js
   // probe-entry.ts
   export default { fetch: () => new Response("probe") };
   export class YourDurableObjectClassName {}
   export const probeLoad = () => import("./src/index");
   ```
2. Rewrite the bundle's `__esm` helper so each module initialiser records `v8.getHeapStatistics().used_heap_size` before and after itself and subtracts its children's cost (exclusive heap per module). Guard the rewrite with a check that the helper regex matched; esbuild's output shape can change.
3. Run the instrumented bundle under `node --expose-gc` with a loader shim (`module.registerHooks`) that resolves `cloudflare:*` imports to stubs and mirrors any Wrangler text rules (for example `.sql` as text). `process.memoryUsage()` is an unenv polyfill that reports zeros in Workers-targeted bundles, so read `v8.getHeapStatistics()` directly.
4. Print heap after module evaluation, the top modules by exclusive heap, and per-package totals. Rank, fix the top row, re-profile, repeat.
5. Classify every surviving schema module by why it is in the bundle (used at runtime; reached through `export *` in a barrel; reached through a dynamic import of a package root; kept because the package lacks `"sideEffects": false`), using the metafile's `imports` graph to print one import chain from the entry.
6. Apply fixes in order and re-profile after each: `"sideEffects": false` (or a side-effect file list) after grepping for top-level `globalThis` writes and `addEventListener`; named re-export lists generated with the TypeScript compiler API rather than regex; static named imports in place of dynamic package-root imports, after checking the import was not lazy for another reason (circular imports, Node-only test loading). Convert schema-library tool definitions to plain JSON Schema only once the ranking shows what it saves.
7. Add a CI assertion that reads the metafile of the memory-sensitive Worker and fails when a schema module survives tree shaking into it, printing the import chain. After deploy, compare memory P50/P99 and reset counts across the deployment marker.

## Dashboard/account evidence request

```text
Cloudflare Doctor this repo, but do not infer dashboard settings from code. Tell me the smallest redacted evidence package you need for DNS, WAF, Access, cache rules, Logpush, billing, and product usage.
```

Use before authenticated commands or screenshots. The skill should ask for exact evidence and mark missing account state as not inspected.

## Static scan only

```bash
python3 /path/to/cfdoctor/skills/cloudflare-doctor/scripts/cfdoctor_static_scan.py .
```

Use in CI or as a pre-audit smoke check. The Python scanner parses local `wrangler.jsonc`, `wrangler.json`, and legacy `wrangler.toml` configs plus source/docs/IaC text to build a product inventory and heuristic risk leads. Every finding carries a stable check ID from the registry (`--list-checks`); add `--json` for machine-readable output and `--exclude REL_PATH` to scope out subtrees (when scanning this repo itself, use `--exclude evals/fixtures` — the detection fixtures are intentionally bad). Scanner findings are leads, not proof: they do not replace current Cloudflare docs, account/dashboard evidence, traffic/billing data, or the full Cloudflare Doctor audit contract.

## Trigger eval maintenance

```bash
python3 scripts/eval_skill_trigger.py --out-dir /tmp/cfdoctor-trigger-eval
```

Run after editing `skills/cloudflare-doctor/SKILL.md` or `evals/trigger-cases.json`. Current expected result is 100% proxy accuracy with no missing description terms. Use `npm run update-results` only when the checked-in report under `evals/results/` should be refreshed.

## Detection eval and coverage maintenance

```bash
python3 scripts/eval_detection.py --out-dir /tmp/cfdoctor-detection-eval
python3 scripts/check_coverage.py
```

Run after changing scanner heuristics, fixtures, or the coverage matrix. The detection eval must pass every fixture under `evals/fixtures/detection/` (including the `clean-baseline` false-positive guard), and the coverage checker must report the matrix consistent with the scanner registry. When fixing a scanner false negative, add a failing `gap-*` fixture first, then fix the heuristic. Use `npm run update-results` only when the checked-in report under `evals/results/detection/` should be refreshed.
