# Changelog

All notable changes to Cloudflare Doctor are tracked here.

## Unreleased

- Replaced the broad account-collector design with a Wrangler-first deployed-state snapshot workflow: explicitly approved read-only plans, private output outside Git, Worker dashboard/source download, Pages config download, deployment and active-version metadata, binding/runtime limits, secret-name inventory, command/file hashes, metadata-only mode, and offline fake-Wrangler tests. No package installation, credential storage, or Cloudflare mutation is introduced.
- Hardened scanner correctness and evidence quality:
  - Scanner 0.3.3 parses valid JSONC comments/trailing commas, distinguishes valid empty config from parse failure, always emits actionable parse diagnostics, and includes evidence/fix fields in JSON output.
  - Corrected current-doc semantics for Queue retries/DLQ deletion, Durable Object storage batching versus coalescing/backend billing, D1 `SELECT *`, and direct Workers meters versus downstream amplification.
  - Added valid/malformed JSONC and Queue-DLQ near-miss fixtures (19/19 detection fixtures) plus offline unit tests.
- Added a 27-record structured incident/claim ledger with stable source-cluster IDs, evidence classes, multidimensional confidence, freshness, scenario/check lineage, and reciprocal fixture provenance validation. A 2026-07-11 web refresh added direct D1 row-read, Durable Object alarm-loop, Durable Object product-fit, and first-party Cloudflare outage evidence.
- Repaired link checking after the narrow install-boundary move: runtime references are now scanned, generated reports are excluded, canonical Cloudflare URLs are refreshed, and critical official-doc semantic anchors have an explicit review policy.
- Upgraded Skill Eval Harness integration to v0.6.0 with strict leakage, materialized-ablation, and manifest-audit validation; strengthened prompt-leakage assertions and structural fixture oracles.
- Refreshed post-cutoff Cloudflare docs for Workflow step/storage billing and dynamic retries, new Durable Object KV-backend namespace restrictions, and Images binding unique-transformation billing/cache behavior. Ran a 72-output GPT-5.5 three-way eval comparing local, GitHub `origin/main`, and no skill, with GPT-5.5 qualitative judging; results are recorded under `evals/results/gpt-5.5-value/latest.md`.
- Removed mandatory broad reference reading and full-report output for narrow/no-finding prompts; added focused triage, a hard non-Cloudflare activation boundary, path-safe benchmark fixtures, zero-finding precision gates, a DLQ-safe control/oracle, calibrated judge thresholds, and token/elapsed budgets for all tune answer cases.
- Tightened mutation safety after the eval: broad audit/fix requests no longer authorize deploys, secret rotation, cache purges, or DNS/WAF/resource mutations; exact target evidence, blast radius, rollback/dry-run, and final confirmation are required.
- Added Workers Cache (per-Worker declarative cache, `cache.enabled`) coverage grounded in the 2026-07-06 launch (https://blog.cloudflare.com/workers-cache/) and official docs (`workers/cache/`, `workers/cache/limitations/`, `workers/runtime-apis/cache/`):
  - New cost-footgun guidance: cache hits still bill a request (only CPU is saved), enabling caching bills normally-free static-asset and worker-to-worker (service binding / `ctx.exports`) traffic, request collapsing vs the Cache API, and the auth-bypass / `ctx.props` tenant-separation footguns.
  - Updated `cost-footguns.md`, `performance-and-reliability.md` (layered cache map + caching-behavior checks), `product-fit-rubric.md`, `config-and-security-checks.md`, and the source maps (`official-source-map.md`, `cloudflare-best-practices-docs.md`, `recommendation-provenance.md`).
  - Added war-story scenario #23 and scanner lead `CFDOC-COST-WORKERS-CACHE-BILLING` (fires on Wrangler `cache.enabled` / `exports[*].cache.enabled`), with a matrix row and a `workers-cache-auth-bypass` detection fixture. The full suite is now `19/19` detection fixtures and scanner `0.3.3` after the additional hardening above.

## 0.2.2 — 2026-06-14

- Moved the runtime skill from the repository root to `skills/cloudflare-doctor/`.
- Kept only `SKILL.md`, runtime references, and the static scanner inside the installable skill boundary.
- Updated Pi/package metadata, install commands, eval manifest paths, and CI checks for the narrow installable directory.

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
