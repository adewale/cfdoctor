# TODO

Remaining work, ordered by the same criteria as
[`docs/improvement-plan.md`](docs/improvement-plan.md) (verifiability first,
then likelihood of delivering value). Items completed on 2026-06-09 — stable
scanner check IDs (v0.3.0), the fixture-based detection eval (now 19 fixtures, including JSONC parser and Queue-DLQ controls), the coverage
matrix + CI consistency checker, citation link verification, SKILL.md
reference routing, and five false-negative heuristic fixes — are recorded in
the plan doc and the git history, not repeated here.

## Scanner

- [ ] Fix the remaining known false-negative limits listed at the bottom of
      [`skills/cloudflare-doctor/references/check-coverage-matrix.md`](skills/cloudflare-doctor/references/check-coverage-matrix.md),
      fixture-first (add a failing `gap-*` fixture before changing a
      heuristic): deeper sharding indirection, per-queue (not project-global)
      consumer-config matching, alarm guard words in ordinary variable names,
      Stream-preload precision, self-fetch through a URL variable.
- [ ] Revisit the five `skill-prompt-only` checks in the coverage matrix
      (webhook idempotency, origin bypass, spend-alerts-only, log volume,
      preview/paid bindings) and decide which can gain at least a partial
      static lead.
- [ ] Consider SARIF output (`--sarif`) once a real CI consumer exists; do
      not add it speculatively.

## Account-state collector (deferred — needs a live Cloudflare account)

- [ ] Implement the `collect` / `eval` split from
      `research/doctor-patterns-research.md`: a read-only collector that
      snapshots zone settings, DNS, rulesets, and cache rules into
      `facts.json` for offline audit. Requires a session with a real test
      account and API token; ship nothing token-handling that cannot be
      tested. Start with zone settings + DNS + rulesets only.

## Evals

- [ ] Add a human-labeled or second-model judge-alignment sample and repeated runs for precision-critical fixtures. The current three-way GPT-5.5 round has one run per variant and uses GPT-5.5 as both answerer and judge.
- [ ] Continue reducing the remaining local-vs-no-skill overhead (2.77× mean tokens, 1.96× elapsed) without regressing the local skill's objective/combined lift.
- [ ] Populate holdout/holdback cases from a non-ephemeral environment (the
      directories are gitignored by design; see plan item 6 correction).

## Citations and sources

- [ ] Resolve or supersede unverified ledger record `CFDOC-EVD-AWS-S3-HOTLINK` at its review boundary; keep it discovery-only until stronger provenance is recorded.
- [ ] Re-run `python3 scripts/check_links.py --strict --check-content` each release or quarterly. CI validates target presence and content-policy freshness without making network-dependent requests.

## Research backlog (new patterns and experience reports)

The 27-record structured `research/incident-claim-ledger.json` now separates incidents, official guidance, operator notes, and product announcements; deduplicates source clusters; records five confidence dimensions and freshness; covers all 23 runtime scenarios; and has reciprocal fixture lineage enforced by `scripts/check_claim_ledger.py`.

- [ ] Mine the public `cloudflare/cloudflare-docs` git history for added
      warnings/pitfall admonitions — each one is a fossilized user incident;
      turn matches into war-story checklist entries and fixtures.
- [ ] Sweep `cloudflare/workers-sdk` issues/changelogs for guardrails added
      after failures (recursion detection, limit warnings, default changes).
- [ ] Sample the remaining serverlesshorrors.com catalog as a discovery index, resolve every candidate to a primary source, deduplicate by causal source cluster, and reject entries that cannot meet the ledger's provenance bar.
- [ ] Broaden beyond billing: cache deception/poisoning against
      Cloudflare-fronted apps, Flexible-SSL redirect loops, dangling DNS /
      `pages.dev` takeover, origins trusting `CF-Connecting-IP` without
      Authenticated Origin Pulls, WAF exceptions scoped too broadly,
      HackerOne disclosed reports for Workers/Pages/Access.
- [ ] Add reliability postmortems (Cloudflare's own outage write-ups and
      customer-side misconfig outages) — the corpus is ~90% cost today.
- [ ] Cover the new-product frontier before stories go viral: Workers
      AI / AI Gateway / Vectorize / Agents SDK runaway-loop costs, plus
      paired third-party meters (Upstash, Neon/Turso/PlanetScale, LLM APIs).
- [ ] Add missing platforms to the evidence matrix: Deno Deploy, AWS
      Amplify, Workers for Platforms (tenant code as denial-of-wallet).
- [ ] Calibrate cost proxies: define 3–4 canonical workload profiles
      (hobby / launch / production SaaS / viral spike) from public case
      studies so findings can state assumed volumes.
