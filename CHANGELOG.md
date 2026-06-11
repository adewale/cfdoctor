# Changelog

All notable changes to Cloudflare Doctor are tracked here.

## Unreleased

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
