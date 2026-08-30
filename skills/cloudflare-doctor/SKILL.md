---
name: cloudflare-doctor
description: Audits concrete Cloudflare projects/configurations for best-practice drift, wrong primitive/product choices, missed optimizations, product misconfiguration, security gaps, reliability risks, and cost footguns. Use when reviewing repo/account evidence for Workers, Pages, Wrangler, Static Assets, KV, D1, R2, Durable Objects, WorkerEntrypoint/RpcTarget RPC, Queues, Workflows, Workers AI, AI Gateway, Vectorize, Images, Stream, Browser Run, Dynamic Workers, Containers, Pipelines, Workers VPC, Email bindings, Secrets Store, Agents SDK, Artifacts, Analytics Engine, Workers Logs, CDN/cache, DNS, WAF, Access/Zero Trust, Cloudflare account settings, pricing/overages, budget alerts/spend monitoring, runaway-loop bill diagnosis, or IaC decisions. Do not use for generic Cloudflare status-page/uptime questions, product news, or conceptual Cloudflare explainers without project/config/account evidence to audit.
compatibility: Agent Skills clients including Codex, OpenCode, Pi, Gemini CLI, and Claude Code.
---

# Cloudflare Doctor

Use this skill to audit a user's Cloudflare project like a doctor: diagnose from evidence, name the risk precisely, explain the Cloudflare primitive/product mismatch, and prescribe the smallest safe fix.

## First principles

- Evidence first: every finding needs a file/config/account source, line/reference where possible, and a concrete Cloudflare behavior or billing mechanism.
- Current docs over memory: before asserting a Cloudflare best practice, product behavior, limit, pricing detail, or configuration recommendation, fetch the current official Cloudflare docs. Never rely on the agent's training data or memory when live docs can be fetched. If docs cannot be fetched, say the claim was not current-doc verified.
- Do not infer dashboard/account settings from repo files. If DNS, SSL/TLS, WAF, cache rules, Access, billing, or Logpush evidence is absent, ask for Terraform/export/screenshots/API output or mark it **not inspected**.
- Separate **confirmed findings** from **suspicions to verify**. Cloudflare products and limits change; cite current docs/pricing when making date-sensitive claims.
- Prefer primitive-fit fixes over local patches: KV vs D1 vs Durable Objects vs R2 vs Queues vs Workflows vs Cache is often the root problem.
- Cost issues are findings even when the app works. Estimate the cost mechanism, not exact dollars unless the user supplied volumes and plan details.

## Activation boundary

Use this skill only when the request includes concrete Cloudflare project, configuration, architecture, IaC, account, or usage evidence to audit. Decide from the user request and explicitly supplied inputs before inspecting the workspace. **Hard stop:** when the task names only AWS or another non-Cloudflare platform, reply in one brief sentence that Cloudflare Doctor is not applicable; do not inspect the repo, emit scope markers, or perform that audit. If a prompt merely says a README/repo/config exists but attaches no such files, reply only that no auditable project evidence was supplied; do not search the workspace or emit `Scope inspected:`. For example, a claim that a README links to Cloudflare docs without an attached README is not an audit input. For generic DNS explanations, public status checks, product news, brand copy, or conceptual Cloudflare questions with no project evidence, do not search the workspace, read this skill's references, or emit its audit format; answer normally or route to the appropriate skill.

## Standard workflow

1. Inventory the supplied evidence first: relevant repo files, Wrangler config, bindings, IaC, routes, runtime paths, migrations, tests, and account exports. If there is no concrete Cloudflare evidence, stop at the activation boundary.
2. If allowed, run the static scanner from the project root before reading broad guidance. Use the absolute path to this skill's script (the `scripts/` directory next to this `SKILL.md`):
   ```bash
   python3 <skill-dir>/scripts/cfdoctor_static_scan.py .
   ```
   Treat scanner output as leads, not proof. Add `--json` for machine-readable leads with stable check IDs. When a scanner lead supports a reported finding, preserve its stable check ID in `Evidence:` so the reader can track it precisely across reruns and fixes. When scanning this skill's own repository, add `--exclude evals/fixtures` (the fixtures are intentionally bad). A zero-finding scan is affirmative precision evidence: do not manufacture hygiene findings merely because the prompt asks what is wrong. Explicit intent, tests, or compensating controls in supplied README/config evidence suppress generic route/default/hygiene suggestions unless contrary runtime evidence exists.
3. Map detected products, primitives, hot paths, and concrete hypotheses.

   For cost audits, perform bounded public-surface discovery before ranking individual queries only when crawler-amplified public access is the stated problem or a supported hypothesis from the supplied routing, discovery, or traffic evidence. Treat a sitemap as one seed, not the inventory boundary: derive public host entrypoints and static/dynamic route families from supplied Wrangler/Pages configuration, router or framework artifacts, shared middleware/layouts/loaders, internal links, redirects, and separately requested media/API URLs; overlay observed paths only when traffic evidence is supplied. Do not enumerate or crawl an unbounded live corpus. For every dynamic family, distinguish (a) the known or discoverable valid corpus, (b) the syntactically accepted path/query keyspace, which may be much larger or unbounded, and (c) the first rejection or validation point. Trace arbitrary, missing, malformed, and unknown keys far enough to prove whether rejection occurs before any metered or quota-bearing work; do not use the content count as the exposure bound when code accepts more keys.

   For each route family, trace `host + route family -> discovery evidence -> accepted keyspace/early rejection -> runtime entrypoint -> inherited and route-specific live dependencies -> invocation count -> billable or quota unit + aggregation key/window -> cache/control placement`, including zero-live-cost families. A dependency call is not automatically a separately billable event: verify the current unit, exclusions, included allowance, aggregation dimension, and billing window from the relevant official product and pricing/limits documentation. Show this compact graph in the answer so off-sitemap discovery, inherited work, rejection order, and compound meters are auditable. Do not combine route families whose live-dependency sets differ: name inherited work once, then name each family's added call and applicable unit. Do not probe a live host unless the user authorized it.

   For each materially crawlable route family, decide whether the recommended change prevents corpus-scale, fan-out, or otherwise high-cost live work **before that work executes**. Calculate repeated-hit exposure and a cache exposure envelope. For a corpus-covering crawl, model `distinct requested cache keys × one fill` as a **minimum first-fill scenario**, not a worst case; when request coverage is unknown, label it as a scenario rather than an observed lower bound. Where evidence permits, add independent cache locations and refills caused by expiry, eviction, purge/version changes, revalidation, and concurrent uncoalesced misses. State unknown factors instead of inventing a hit ratio. Move shared aggregates and other broad work to the content-update/publish path through static generation or materialization; if a live route-specific lookup remains, require evidence that its plan and billed units are bounded, state the first-fill and refill assumptions, and use an explicit cache for recrawls. Moving, indexing, or removing one wasteful query is sufficient only when it demonstrably removes the dangerous cost shape from every public path; do not call an unmeasured residual lookup safe. Give the primary prevention a TTL or refresh/invalidation owner and error-response behavior as applicable. If the evidence cannot establish a safe boundary, say what freshness, personalization, validation order, query-plan, cache-eligibility, aggregation, or billing fact is missing. Keep deployed cache, traffic, and control state marked not inspected unless supplied.

   Treat scanner output as supporting evidence inside the analysis, not as the primary unit of analysis. Read only the minimum references needed to test those hypotheses; do not read a reference solely because its product is mentioned. Before another reference or web fetch, name the unresolved question it would answer; stop once the finding is confirmed/rejected. For a narrow single-product task, use one routed reference and at most two direct official pages unless a documented conflict requires more. For a compound cost path, use the minimum directly relevant official page set that covers every materially different unit; do not force unlike dependencies under one product's pricing semantics.

   | Reference routing | Read when |
   |---|---|
   | [`audit-playbook.md`](references/audit-playbook.md) | Broad repo/account audit, multiple product families, or the user requests the full audit. |
   | [`recommendation-provenance.md`](references/recommendation-provenance.md) | Before publishing confirmed findings that need sourced recommendations. |
   | [`wrangler-snapshots.md`](references/wrangler-snapshots.md) | The user supplies a Wrangler snapshot or asks to collect deployed Worker/Pages state. |
   | [`sharing-cloudflare-state.md`](references/sharing-cloudflare-state.md) | A different specific hypothesis depends on dashboard/account state. |
   | [`targeted-account-reads.md`](references/targeted-account-reads.md) | Wrangler/repo evidence leaves one named DNS/ruleset/Access/R2/Queue/usage hypothesis unresolved. |
   | [`cloudflare-best-practices-docs.md`](references/cloudflare-best-practices-docs.md) | Locating official pages for an already identified hypothesis. |
   | [`product-fit-rubric.md`](references/product-fit-rubric.md) | A primitive/product choice is materially in question. |
   | [`config-and-security-checks.md`](references/config-and-security-checks.md) | Concrete Wrangler, binding, auth, secret, route, or IaC evidence is in scope. |
   | [`performance-and-reliability.md`](references/performance-and-reliability.md) | A detected hot path, retry, queue, lifecycle, or reliability mechanism is in scope. |
   | [`cost-footguns.md`](references/cost-footguns.md) | A detected path uses a mutable billing meter or cost amplification is in scope. |
   | [`war-story-scenario-checklist.md`](references/war-story-scenario-checklist.md) | A concrete incident-shaped mechanism is detected; use it for hypotheses, never current semantics. |
   | [`audit-engine-patterns.md`](references/audit-engine-patterns.md) | Designing/changing report or check tooling, not routine audits. |
   | [`check-coverage-matrix.md`](references/check-coverage-matrix.md) | Deciding whether the scanner already covers a pattern. |
   | [`official-source-map.md`](references/official-source-map.md) | Locating official product docs for an identified finding. |
   | [`pricing-source-bundles.md`](references/pricing-source-bundles.md) | Resolving a concrete pricing/rate/meter conflict or estimating a compound bill. |
4. Fetch only the current official Cloudflare pages needed to confirm or reject the hypotheses, using product `llms.txt` indexes and applicable Markdown pages. Treat local references as navigation aids, not current authority. For each dependency in a reported cost path, use the current official product/runtime documentation for call semantics and the applicable official pricing or limits documentation for its billable/quota unit, exclusions, aggregation key, and window; do not label an operation "paid" merely because it is a Cloudflare binding. Every current product/configuration recommendation needs official `Source basis` that directly supports it. War stories can support historical mechanisms, not current semantics, applicability, or probability. Exception: a static Wrangler snapshot plan or reconciliation from supplied artifacts should use [`wrangler-snapshots.md`](references/wrangler-snapshots.md) without browsing unless the user asks or a command's current availability/semantics is materially disputed.
5. If account/dashboard state could change a hypothesis, ask for the smallest discriminating evidence package. Do not request broad account dumps or infer state from its absence in the repo.
6. If TypeScript code exposes `DurableObject`, `WorkerEntrypoint`, `WorkflowEntrypoint`, `RpcTarget`, or Agent classes, use the optional dead cross-boundary RPC path only when reachability is actually in scope. Gate third-party tools on approval/pinning and treat output as leads, not proof.
7. Produce only evidence-backed findings. Prioritize correctness, security, reliability, and cost over exhaustive trivia.

## Output modes

Use **focused triage** by default for one narrow mechanism, prompt-only architecture evidence, small fixture reviews, and zero-finding results. Keep it concise. For three or fewer supplied files, read them directly: do not inventory/search the entire workspace, read the broad playbook/provenance/war-story references, or fetch a product index. Use at most one scanner run and the minimum direct official page needed for a mutable claim. Include `Scope inspected:`, `Scope not inspected:`, and `Docs refreshed:` (or why no mutable semantic required a fetch). If no finding is supported, say `No confirmed findings.` and stop after any question that would materially change that conclusion. Do not add low-severity filler, generic cost maps, or a full run summary.

When public crawlability is the cost mechanism, include the compact route-family dependency/cost map required by step 3; it is evidence for the finding, not generic filler.

When focused triage has a confirmed finding, use every finding-card field below with the literal labels (`Severity`, `Category`, `Evidence`, `Why it matters`, `Fix`, `Cost / trade-off`, `Verify`, `Source basis`, and `Confidence`); do not fold `Source basis` into inline citations. The full audit scaffold is not required. Explicit bounded retries plus a configured DLQ and process-before-ack flow are a valid Queue near-miss: do not invent findings for optional custom backoff, a separate DLQ consumer, or permanent-error classification unless workload/account evidence makes them necessary.

Use the **full audit** format only for broad repo/account audits, multiple material findings/product families, or when the user explicitly requests the complete report. Before finalizing a full audit, verify the summary and finding fields are present.

Start a full audit with:

```markdown
## Cloudflare Doctor audit
Scope inspected: <repo paths, config, account/dashboard evidence, commands run>
Scope not inspected: <missing account/dashboard/deploy evidence>
Docs refreshed: <Cloudflare docs URLs fetched, or explicit note that current docs could not be fetched>
Detected products: <Workers/Pages/KV/D1/...>
Cost proxy summary: <request count assumptions; CPU/subrequests; D1 rows; R2/KV ops; DO duration/requests; Queue retries; AI/browser/media/vector usage; cache hit/miss assumptions>
Overall risk: <low|medium|high> — <one sentence>
```

Then group findings:

```markdown
### Severity: <critical|high|medium|low> — <short finding title>
- Category: <best-practice drift | wrong primitive | missed optimization | misconfiguration | cost footgun | security | reliability>
- Evidence: <file:line/config/account source/command output, or "User-supplied prompt/architecture statement" when no files were provided>
- Why it matters: <Cloudflare-specific behavior, limit, consistency model, billing mechanism, or failure mode>
- Fix: <smallest safe remediation; include better primitive/product if applicable>
- Cost / trade-off: <billing meter or cost proxy affected; expected benefit; implementation effort; latency/complexity/security downside; reversibility; assumptions>
- Verify: <command, dashboard check, load test, or config check>
- Source basis: <current official Cloudflare docs URL(s) fetched this audit; optionally add accepted war story URL(s) for historical mechanism provenance>
- Confidence: <high|medium|low>
```

End with:

```markdown
## Run summary with cost proxies
- Hot paths: <routes/jobs/crons/workflows reviewed>
- Expensive primitives per user action: <rough operation counts or unknown>
- Retry/fanout/circuit-breaker posture: <bounded|unbounded|unknown>
- Cache map: <browser/CDN/Worker Cache/KV/R2/D1/AI Gateway/etc.; key, TTL, invalidation owner>

## Recommended next actions
1. <highest leverage fix>
2. <next>

## Questions / evidence needed
- <only questions that would change the diagnosis>
```

## Severity guide

- **Critical**: likely secret exposure, public data exposure, production outage risk, runaway billing, or a deployed security bypass.
- **High**: wrong primitive causing correctness/reliability/cost risk at normal scale; severe misconfig; missing auth/rate limit on sensitive endpoints.
- **Medium**: meaningful performance/cost/reliability improvement or configuration drift that can become serious with growth.
- **Low**: hygiene, maintainability, minor optimization, or low-confidence smell.

## Safe command policy

- Local read-only commands are fine: `find`, `rg`, `python3 <skill-dir>/scripts/cfdoctor_static_scan.py .`, package manager metadata commands, and unauthenticated Cloudflare docs fetches such as `curl -fsSL https://developers.cloudflare.com/workers/llms.txt`.
- Ask before running third-party code or network-installing tools with `npx`/package managers unless the user already approved that class of tooling. For example, `npx @acoyfellow/deadlint . --check dead-rpc --json` is read-only analysis, but still executes third-party code and should be approved or pinned in repo tooling first.
- Ask before authenticated Cloudflare commands, even read-only ones, because they may expose account/project names or consume API rate limits.
- Never deploy, mutate bindings, create/delete resources, purge cache, change DNS/WAF/rules, or rotate secrets from an audit or broad “fix it” request. Before mutation, show the exact target/current evidence, proposed change, blast radius, dry-run/plan where available, and rollback path, then obtain explicit final confirmation. A second confirmation may be omitted only when the user already supplied the precise resource/change or command and explicitly requested immediate execution.
