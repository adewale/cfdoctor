# Changelog

All notable changes to Cloudflare Doctor are tracked here.

## Unreleased

- Derived the D1 isolate-cache check family from the kentcdodds.com evidence (scanner `0.3.7`): new scanner lead `CFDOC-COST-D1-ISOLATE-CACHE` fires when an expensive D1 aggregate (COUNT/SUM/AVG/GROUP BY over a table) is cached only through a per-isolate memory adapter (`cache: lruCache`-style cachified adapters, or a module-scope `Map`/`LRUCache` memo with no shared KV/cache layer near the query). Precision controls keep the good patterns quiet: shared/KV-backed adapters, L1-memory-over-L2-shared layering, and in-memory caching of cheap non-aggregate values do not fire. Added war-story scenario #24, detection fixtures `d1-isolate-cache-rescan` (must fire) and `d1-shared-cache-safe` (layered near-miss, `max_findings: 0`), five scanner unit tests, a coverage-matrix row, cost-footgun/performance guidance, and reciprocal ledger lineage; `scripts/check_claim_ledger.py` now validates scenarios 1..24. Live validation against five recent `adewale/*` D1 repos surfaced one false-positive class — function-local accumulator `Map`s (which cannot cache across requests) matched the memo shape — fixed by requiring module-scope (column-0) declarations, with a regression unit test and an accumulator control file added to `d1-shared-cache-safe`.
- Added `research/kentcdodds-pr-890-review.md` and accepted ledger record `CFDOC-EVD-KCD-D1-ISOLATE-CACHE` (30 records): kentcdodds.com's merged 2026-08-08 fix for a $195.05 / 195-billion-rows-read D1 invoice line caused by per-isolate LRU caching of two full-table `PostRead` aggregates — isolate churn re-ran the scans ~127× more often than the 5–30 min TTLs imply. Key lessons captured: cache-layer *placement* (not presence) is the audit question; per-isolate TTLs do not bound global recompute rate; the D1 meter is per-execution scan size × execution count (complementing `CFDOC-EVD-D1-134-BILL`'s missing-index half); `forceFresh` reachable from public actions is an amplifier; `d1QueriesAdaptiveGroups` invoice-to-query attribution is a reusable evidence recipe.
- Fixed a `CFDOC-SEC-SECRET-ASSIGNMENT` false positive (scanner `0.3.6`). In source files a secret-named variable assigned a *reference* — `const token = form.get("cf-turnstile-response")`, `const apiKey = env.API_KEY`, `api_token = var.cloudflare_api_token` — was reported as a high-severity committed credential ("Rotate if real"). Those are the correct way to read a credential, and the first is the shape the skill's own Turnstile server-side-validation guidance asks for, so acting on cfdoctor's advice produced a new finding. Call and reference values are now exempt in code files only (`.js/.ts/.tf/.sql` and friends); unquoted literals in `.env`, YAML, and other config text are unchanged, as are quoted literals in code. Added the `secret-reference-not-literal` precision control (`max_findings: 0`, 26 detection fixtures) and three scanner unit tests covering both directions.

## 0.3.0 — 2026-07-12

- Replaced the broad account-collector design with a Wrangler-first deployed-state snapshot workflow: explicitly approved read-only plans, private output outside Git, metadata-only-by-default deployment/active-version/secret-name capture, separately opted-in Worker source/config and Pages config download, binding/runtime limits, command/file hashes, offline fake-Wrangler tests, and approved private live validation across Wrangler 4.53.0, 4.71.0, and 4.94.0. Raw snapshots were deleted after shape-only review. No runtime package installation, credential storage, or Cloudflare mutation is introduced.
- Reviewed all 86 accessible `adewale/*` default branches and parsed all 334 `wrangler.jsonc` files. Separated 24 deployable configs from 60 maintained examples, 20 intentional fixtures, and 230 generated corpus copies; the resulting changes make metadata-only capture the default, exclude `corpus-cache`, recognize modern Wrangler product families, and document environment/multi-config/Service Binding scope boundaries.
- Hardened and repeated the four GPT-5.5 Wrangler cases against a clean current skill tree: semantic approval/no-install/Static Assets oracles, a direct forbidden-package-runner script oracle, identifier-minimization checks, and a no-browse planning rule. Three fresh samples per case scored 94.52% objective / 95.08% combined with 12/12 judge passes, a 0.9608 judge mean, and 100% process/efficiency passes. No sample recommended a package runner or repeated the prior documentation-search outlier.
- Hardened scanner correctness and evidence quality:
  - Scanner 0.3.5 excludes generated `corpus-cache` trees; inventories modern Wrangler product families; resolves bounded imported/computed DO keys and self-fetch aliases; matches literal Queue consumers per queue; requires real alarm conditions; links Stream preload to Stream symbols; and adds full-sampling/webhook-idempotency leads.
  - Scanner 0.3.5 parses valid JSONC comments/trailing commas, distinguishes valid empty config from parse failure, always emits actionable parse diagnostics, and includes evidence/fix fields in JSON output.
  - Corrected current-doc semantics for Queue retries/DLQ deletion, Durable Object storage batching versus coalescing/backend billing, D1 `SELECT *`, and direct Workers meters versus downstream amplification.
  - Added valid/malformed JSONC, Queue-DLQ, sharding, alarm, Stream, self-fetch, observability, and webhook near-miss fixtures (25/25 detection fixtures) plus offline unit tests.
- Added a 29-record structured incident/claim ledger with stable source-cluster IDs, evidence classes, multidimensional confidence, freshness, scenario/check lineage, and reciprocal fixture provenance validation. A 2026-07-11 refresh added direct D1 row-read, Durable Object alarm-loop, Durable Object product-fit, three first-party Cloudflare outage postmortems, and an explicit superseded-evidence disposition.
- Repaired link checking after the narrow install-boundary move: runtime references are now scanned, generated reports are excluded, canonical Cloudflare URLs are refreshed, and critical official-doc semantic anchors have an explicit review policy.
- Upgraded Skill Eval Harness integration to v0.6.0 with strict leakage, materialized-ablation, and manifest-audit validation; strengthened prompt-leakage assertions and structural fixture oracles.
- Refreshed post-cutoff Cloudflare docs and mined 544 recent docs commits plus 1,160 Workers SDK issues. Ran a matched 279-answer GPT-5.5 three-way eval comparing the exact current skill, immutable GitHub `origin/main`, and no skill with three interleaved runs per visible case, paired uncertainty, 243 blind GPT judgments, and a 27-case Claude sensitivity sample. Current scored 89.15% objective versus 81.79% main and 72.97% no skill; the Wrangler lift was strong while legacy compatibility and pricing limitations are reported separately under `evals/results/gpt-5.5-current-threeway/`. A one-shot private holdout/holdback release guard passed 2/2 with only sanitized aggregates committed.
- Removed mandatory broad reference reading and full-report output for narrow/no-finding prompts; added focused triage, a hard non-Cloudflare activation boundary, path-safe benchmark fixtures, zero-finding precision gates, a DLQ-safe control/oracle, calibrated judge thresholds, and token/elapsed budgets for all tune answer cases.
- Tightened mutation safety after the eval: broad audit/fix requests no longer authorize deploys, secret rotation, cache purges, or DNS/WAF/resource mutations; exact target evidence, blast radius, rollback/dry-run, and final confirmation are required.
- Added Workers Cache (per-Worker declarative cache, `cache.enabled`) coverage grounded in the 2026-07-06 launch (https://blog.cloudflare.com/workers-cache/) and official docs (`workers/cache/`, `workers/cache/limitations/`, `workers/runtime-apis/cache/`):
  - New cost-footgun guidance: cache hits still bill a request (only CPU is saved), enabling caching bills normally-free static-asset and worker-to-worker (service binding / `ctx.exports`) traffic, request collapsing vs the Cache API, and the auth-bypass / `ctx.props` tenant-separation footguns.
  - Updated `cost-footguns.md`, `performance-and-reliability.md` (layered cache map + caching-behavior checks), `product-fit-rubric.md`, `config-and-security-checks.md`, and the source maps (`official-source-map.md`, `cloudflare-best-practices-docs.md`, `recommendation-provenance.md`).
  - Added war-story scenario #23 and scanner lead `CFDOC-COST-WORKERS-CACHE-BILLING` (fires on Wrangler `cache.enabled` / `exports[*].cache.enabled`), with a matrix row and a `workers-cache-auth-bypass` detection fixture. The full suite is now `25/25` detection fixtures and scanner `0.3.5` after the additional hardening above.

Release: https://github.com/adewale/cfdoctor/releases/tag/v0.3.0

## 0.2.2 — 2026-06-15

- Moved the runtime skill from the repository root to `skills/cloudflare-doctor/`.
- Kept only `SKILL.md`, runtime references, and the static scanner inside the installable skill boundary.
- Added install-boundary validation and CI so repository-only eval, research, fixture, and documentation files cannot leak into the installable skill.
- Upgraded the shared eval integration to Skill Eval Harness v0.4.0 and added case taxonomy fields.
- Updated Pi/package metadata, install commands, eval manifest paths, and CI checks for the narrow installable directory.

Release: https://github.com/adewale/cfdoctor/releases/tag/v0.2.2

## 0.2.1 — 2026-06-11

- Added Agent Skills compatibility metadata for Codex, OpenCode, Pi, Gemini CLI, and Claude Code.
- Documented per-agent installation and usage paths.
- Added `package.json` `skill` and `pi.skills` metadata for Git-installed packages.

Release: https://github.com/adewale/cfdoctor/releases/tag/v0.2.1

## 0.2.0 — 2026-06-11

- Added optional dead cross-boundary RPC audit path for TypeScript `DurableObject`, `WorkerEntrypoint`, `WorkflowEntrypoint`, `RpcTarget`, and Agents SDK classes, including scanner lead `CFDOC-REL-CROSS-BOUNDARY-RPC-DEAD`, fixture coverage (`15/15` detection fixtures), trigger coverage (`39/39`), and gated `deadlint` guidance.
- Added stable scanner check IDs, JSON scanner output, fixture-backed detection evals, coverage-matrix consistency checks, and CI validation for clean self-scans.
- Added v0.3 shared eval quality oracles and updated shared benchmark guidance.
- Refreshed README usage modes, validation commands, recipes, lessons learned, official source maps, and Wrangler config guidance.

## 0.1.0 — 2026-06-09

- Created the public `cfdoctor` repository.
- Added MIT license metadata and root `LICENSE`.
- Added CI validation for JSON manifests, Python helpers, trigger evals, self-scan, and diff whitespace.
- Documented user, scanner-only, and maintainer usage modes plus what evidence users should provide.
- Clarified that `wrangler.jsonc` is Cloudflare's recommended config format for new Wrangler projects while JSON and legacy TOML remain supported audit inputs.
- Expanded README and recipes to explain the Python scanner as a read-only triage layer, not proof or a replacement for sourced audit judgment.
- Added Lessons Learned documentation for eval contract coverage, Wrangler config examples, scanner scope, fixture self-scan noise, and Pi skill bundling.
- Added the Cloudflare Doctor Agent Skill (`SKILL.md`) with source-backed audit workflow and safety rules.
- Added read-only static scanner for Cloudflare repos.
- Added deterministic trigger evals with current proxy result: `38/38 = 100%`.
- Added reference docs for Cloudflare product fit, cost footguns, performance/reliability, account evidence sharing, official docs sourcing, and war-story-derived scenarios.
- Added Coey Durable Objects, Dynamic Workers, Agents SDK, Artifacts, logging, and TCP/database scenario coverage.
