# TODO

Remaining work, ordered by the same criteria as
[`docs/improvement-plan.md`](docs/improvement-plan.md) (verifiability first,
then likelihood of delivering value). Items completed on 2026-06-09 — stable
scanner check IDs (v0.3.0), the fixture-based detection eval (now 25 fixtures, including JSONC, Queue, sharding, alarm, Stream, self-fetch, observability, and webhook controls), the coverage
matrix + CI consistency checker, citation link verification, SKILL.md
reference routing, and five false-negative heuristic fixes — are recorded in
the plan doc and the git history, not repeated here.

## Scanner

- [x] Harden the five known false-negative limits fixture-first: bounded imported/computed DO keys, literal per-queue consumer matching, real alarm-condition guards, linked Stream preload, and bounded self-fetch URL aliases.
- [x] Reassess the five prompt-only checks. Full observability sampling and webhook idempotency gained calibrated scanner leads; origin bypass, alerts-only, and public preview state remain account-evidence questions with existing partial static coverage.
- [ ] Consider SARIF output (`--sarif`) once a real CI consumer exists; do
      not add it speculatively.

## Deployed-state snapshots (Wrangler-first)

- [x] Add an explicitly approved private Wrangler snapshot wrapper for Workers
      and Pages. It captures deployments, active-version metadata,
      bindings/runtime limits, and secret names by default, with downloaded
      dashboard config/source behind a separate opt-in, using
      an existing pinned Wrangler executable; it never installs packages or
      calls mutation commands.
- [x] Run the wrapper, after explicit approval, against `readability-worker`,
      `atlas`, and `keyboardia-staging` with their lockfile-resolved Wrangler
      versions. All plans completed; only sanitized response-shape fixtures were
      retained and the private raw snapshots were deleted.
- [x] Add a targeted-read registry for concrete Wrangler gaps (DNS, rulesets, Access, R2, Queues, usage/billing) with hypothesis, approval, minimization, redaction, and stop boundaries. Do not build a universal account collector.

## Evals

- [x] Improve Wrangler approval/no-install semantics, add package-runner and identifier-minimization oracles, suppress unnecessary docs refresh, and require explicit metadata-only/source boundaries.
- [x] Run a matched current/main/no-skill three-way evaluation with three runs per case, paired uncertainty, blind GPT judgments, and a 27-case Claude judge sample.
- [ ] Add human-labeled judge alignment. Cross-model pass agreement is 26/27, but neither model is a human gold label.
- [ ] Reduce current-vs-no-skill overhead (1.94× mean tokens, 1.59× elapsed in the matched full run), especially the pricing slice, without regressing objective lift.
- [x] Populate gitignored local holdout/holdback prompt and answer files.
- [x] Score one private holdout and one private holdback exactly once for the release decision: 2/2 blind-judge passes, 0.925 mean; only sanitized hashes/aggregates are committed.

## Citations and sources

- [x] Codify pricing source bundles by claim type without storing mutable rates.
- [x] Add pricing-conflict evals for future-effective changes, Enterprise contracts, and compound Worker-plus-binding bills.
- [x] Supersede `CFDOC-EVD-AWS-S3-HOTLINK`; no recoverable primary or independent corroboration was found, so it cannot support current claims.
- [x] Run `python3 scripts/check_links.py --strict --check-content` for this release (477 URLs; zero dead/error targets after excluding authenticated runtime API templates).
- [ ] Re-run the strict content-aware link check quarterly or for the next release.

## StandardAgents DO runaway-loop follow-ups (2026-08-09)

- [ ] Re-review `CFDOC-EVD-STDAGENTS-DO-LOOP` by 2026-09-08: check the X threads/replies for the confirmed in-code trigger (stub calls vs alarms), any Cloudflare refund outcome, and independent pickup (HN or postmortem) that could raise the independence score.
- [ ] Verify budget-alert delivery latency against current docs/changelog at the same review: the cycle-end delivery observed in the incident is operator evidence, and Cloudflare has said billable-usage data is moving toward real-time; update `CFDOC-EVD-CF-BUDGET-ALERTS` and scenario 9/24 wording if semantics change.
- [ ] Consider extending `DO-STUB-CALL-CYCLE` to cross-script `script_name` Durable Object bindings once a real multi-config fixture exists; same-config scope only today, and the matrix row documents the boundary.
- [ ] Confirm the Billable Usage API response shape against the API schema docs (the endpoint template in `targeted-account-reads.md` came from the launch blog) before relying on it in an approved read.

## Research backlog (new patterns and experience reports)

The 29-record structured `research/incident-claim-ledger.json` now separates incidents, official guidance, operator notes, product announcements, and superseded evidence; deduplicates source clusters; records five confidence dimensions and freshness; covers all 23 runtime scenarios and 25 detection fixtures; and has reciprocal fixture lineage enforced by `scripts/check_claim_ledger.py`.

- [x] Mine 544 recent `cloudflare/cloudflare-docs` commits for warnings, pricing/billing transitions, deprecations, and limits; retain selected first-party fossils in `research/frontier-refresh-2026-07-11.md`.
- [x] Sweep 1,160 recent `cloudflare/workers-sdk` issues for guardrail/failure leads; keep issue evidence discovery-only until reproduced/corroborated.
- [x] Sample the eight-entry serverlesshorrors.com catalog as a discovery index; reject all unrepresented wrappers that cannot yet meet the ledger's primary-evidence bar.
- [x] Broaden the hypothesis frontier beyond billing with environment drift, secret effective-state mismatch, Access claim limits, media cache correctness, and false-success deploy verification.
- [x] Add accepted first-party Cloudflare reliability postmortems for the 2025 KV dependency outage and feature-file propagation outage; SDK issue titles remain discovery-only.
- [x] Cover Containers, Pipelines, Workers VPC, Email Service, Dynamic Workers, and Agents/Browser/Sandbox risk surfaces.
- [x] Add Deno Deploy, AWS Amplify, and Dynamic Workers/Workers for Platforms to the evidence matrix.
- [x] Define four explicit synthetic workload profiles (hobby, launch, production SaaS, viral/abuse), clearly labeled as replaceable assumptions rather than observed averages.
