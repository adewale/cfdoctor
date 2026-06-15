# TODO

Remaining work, ordered by the same criteria as
[`docs/improvement-plan.md`](docs/improvement-plan.md) (verifiability first,
then likelihood of delivering value). Items completed on 2026-06-09 — stable
scanner check IDs (v0.3.0), the fixture-based detection eval (now 15 fixtures after the dead-RPC review-surface case), the coverage
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

- [ ] Run the shared benchmark (`evals/shared-benchmark.json`) through
      skill-eval-harness with a real model, including the two new
      fixture-backed tune cases (`detection-fixture-runaway-self-fetch`,
      `detection-fixture-clean-baseline-precision`), and review whether the
      skills/cloudflare-doctor/SKILL.md reference-routing change regressed audit quality — that change
      carries the plan's main regression risk and has only been validated
      deterministically (trigger eval + contract markers).
- [ ] Populate holdout/holdback cases from a non-ephemeral environment (the
      directories are gitignored by design; see plan item 6 correction).

## Citations and sources

- [ ] Find durable replacements for the 11 war-story links annotated
      `no archive snapshot found as of 2026-06-09` (see
      `evals/results/link-check-2026-06-09.md`); manually verify the 3
      bot-blocked URLs (Reddit/Medium/HN 403s) in a browser.
- [ ] Re-run `python3 scripts/check_links.py` periodically (suggested: each
      release or quarterly) and refresh the `Link status last verified`
      lines; the checker is intentionally not in CI.

## Research backlog (new patterns and horror stories)

- [ ] Mine the public `cloudflare/cloudflare-docs` git history for added
      warnings/pitfall admonitions — each one is a fossilized user incident;
      turn matches into war-story checklist entries and fixtures.
- [ ] Sweep `cloudflare/workers-sdk` issues/changelogs for guardrails added
      after failures (recursion detection, limit warnings, default changes).
- [ ] Ingest the full serverlesshorrors.com catalog (only ~4 entries cited
      today) and map each story to a scenario/check.
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
