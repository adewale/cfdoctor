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

   **Public-route cost release gate.** Run this gate whenever supplied evidence shows an anonymous public `GET` or `HEAD` entrypoint whose response path can reach a metered or quota-bearing dependency. The user does not need to mention crawlers, bots, or billing. Do not probe a live host unless the user authorized it, and do not enumerate or crawl an unbounded live corpus.

   Derive the bounded public surface from supplied Wrangler/Pages configuration, router or framework artifacts, shared middleware/layouts/loaders, sitemaps, internal links, redirects, and separately requested media/API URLs; overlay observed paths only when traffic evidence is supplied. Treat a sitemap as one discovery seed, never the inventory boundary. Use this exact matrix header: `host + route family | discovery evidence | known valid corpus | accepted keyspace | first rejection/validation | inherited work | route-specific work | per-hit product unit | first prevention boundary`. Give every materially different route family its own row; never combine routes such as `/` and `/about` when either has additional work. Include zero-live-cost families, and mark uninspected hostnames or generated routes unknown rather than absent. For every dynamic family, trace arbitrary, missing, malformed, and unknown keys far enough to establish whether rejection occurs before metered work; do not use the content count as the exposure bound when code accepts more keys.

   For a pre-launch or pre-merge audit, emit exactly one `Release verdict: BLOCK`, `Release verdict: CONDITIONAL`, or `Release verdict: PASS` before the findings:

   - `BLOCK` when supplied code, a query plan, measurements, or equivalent evidence establishes that anonymous request volume repeatedly invokes corpus-scale, fan-out, or otherwise high-unit live work before validation, static delivery, materialization, or a cache that runs before that work. A visible `COUNT`, `GROUP BY`, or equivalent aggregate over an unbounded or growing corpus on every request is code evidence of corpus-proportional work even when its exact billed units still need a plan or measurement. Route or cache-key cardinality can amplify the exposure, but is not required: a fixed `/` route that demonstrably runs a broad query on every request is still a block.
   - `CONDITIONAL` when the route may have that shape but a query plan, measured product unit, cache placement/eligibility, accepted-keyspace bound, or deployed configuration needed to decide is missing. Missing proof of bounded work is not proof of high-unit work: do not infer an absent index or a full scan solely because the plan or measurements were not supplied. Never translate missing safety evidence into `PASS`.
   - `PASS` only when the supplied evidence shows the expensive shape is prevented before execution and any residual live lookup has bounded, measured units. A pass applies only to the evidenced surface; preserve unknown scope explicitly.

   Crawler controls, rate limits, `robots.txt`, alerts, and caching reached only after the Worker or dependency starts are defense in depth, not closure of an unsafe request path. Closing a `BLOCK` requires removing shared aggregates and other broad work from **every** public request path through static generation or publish/update-time materialization, rejecting syntactically malformed or noncanonical keys before metered work, proving any residual lookup bounded from its query plan and measured billed units, and placing recrawl caching before the expensive dependency when freshness permits. A pre-dependency cache alone does not make broad fill or revalidation work safe: misses, bypasses, expiry, eviction, purge or version changes, independent cache locations, and uncoalesced concurrent fills must remain bounded; `PASS` requires acceptable bounded fill work or removal of the broad work. A valid-shaped key that does not exist may need one indexed lookup; do not require a complete allowlist when the supplied plan and measurement show that miss is bounded. Treat a larger accepted keyspace as an additional multiplier only when those requests reach materially expensive work. Prefer the least disruptive complete closure: do not prescribe generating the whole corpus when materializing shared data, early syntax rejection, a bounded residual lookup, and pre-dependency recrawl caching close the evidenced path. Do not call moving the broad query off only the high-cardinality dynamic family a safe or complete fix. State the cache/static-delivery key, TTL or refresh/invalidation owner, error-response behavior, and residual request meter. Cite the current official page that directly establishes the recommended boundary: Workers Caching configuration is `https://developers.cloudflare.com/workers/cache/configuration/`; Static Assets asset-first behavior is `https://developers.cloudflare.com/workers/static-assets/binding/` or `https://developers.cloudflare.com/workers/static-assets/routing/worker-script/`; the in-Worker Cache API is `https://developers.cloudflare.com/workers/runtime-apis/cache/`. Treat wording such as “render,” “publish,” or “serve as a static asset” as a Static Assets recommendation: cite one of those official Static Assets pages or omit the alternative. If recommending Workers Caching (`cache.enabled`), also cite `https://developers.cloudflare.com/workers/platform/pricing/` for its residual billed-request rate and no-CPU-on-hit behavior. Never use a generic overview/configuration page or the Cache API page to support a pre-Worker claim. The Cache API executes inside the Worker, is data-center-local, and has different location/refill semantics.

   Calculate repeated-hit exposure from the matrix, choosing the branch supported by the evidence. For an uncached, bypassed, or cache-ineligible dependency path, use `anonymous request count × product units per request`; repeated requests to the same URL must remain in the model. For a cached dependency path, use `distinct cache keys × fills per key × product units per fill`, where fills per key expands with independent cache locations, expiry, eviction, purge or version changes, revalidation, bypasses, and uncoalesced concurrent misses. For a corpus-covering crawl, `distinct requested keys × one fill` is only a named first-fill scenario, not a worst case or a substitute for request volume. Substitute only evidenced values and label every other multiplier unknown rather than omitting it or inventing a hit ratio. Separately report any request charge that remains on cache hits. A dependency call is not automatically a separately billable event: verify the current unit, exclusions, included allowance, aggregation dimension, and billing window from the relevant official product and pricing/limits documentation.

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

When the public-route cost release gate activates, put this compact evidence block before the findings, in order: the literal `Release verdict:` line; the route-family matrix; `Discovery gaps:` naming evidenced public families absent from the sitemap or other initial seed and where they were found; `Exposure scenario:` stating per-hit units and the evidence-selected uncached or cached equation (including the first-fill and location/refill/concurrency envelope only for cached paths); and `Closure conditions:` naming what must be true before the verdict can become `PASS`. Before returning, check that all four literal labels, the matrix, and official source basis for the product meter and every recommended cache or static-delivery boundary are present. If the answer recommends Workers Caching or `cache.enabled`, it must cite both Workers Caching configuration and Workers pricing, and state that a cache hit bypasses Worker execution/CPU but retains the documented request charge.

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
