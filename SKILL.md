---
name: cloudflare-doctor
description: Audits Cloudflare projects for best-practice drift, wrong primitive/product choices, missed optimizations, product misconfiguration, security gaps, reliability risks, and cost footguns. Use when reviewing Workers, Pages, Wrangler, KV, D1, R2, Durable Objects, Queues, Workflows, Workers AI, AI Gateway, Vectorize, Images, Stream, Browser Run, Dynamic Workers, Agents SDK, Artifacts, Analytics Engine, Workers Logs, CDN/cache, DNS, WAF, Access/Zero Trust, Cloudflare account settings, pricing/overages, or IaC decisions.
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

## Standard workflow

1. Read [`references/audit-playbook.md`](references/audit-playbook.md), [`references/sharing-cloudflare-state.md`](references/sharing-cloudflare-state.md), [`references/recommendation-provenance.md`](references/recommendation-provenance.md), [`references/audit-engine-patterns.md`](references/audit-engine-patterns.md), [`references/war-story-scenario-checklist.md`](references/war-story-scenario-checklist.md), and [`references/cloudflare-best-practices-docs.md`](references/cloudflare-best-practices-docs.md).
2. If dashboard/account state matters, ask for the smallest evidence package from [`references/sharing-cloudflare-state.md`](references/sharing-cloudflare-state.md). Do not infer dashboard settings from repo files alone.
3. Fetch current Cloudflare docs for the detected products using `https://developers.cloudflare.com/llms.txt`, product `llms.txt` indexes, and the applicable Markdown pages from the verified best-practices list. Treat local reference files as navigation aids, not authoritative current guidance. Every recommendation needs `Source basis`: official current Cloudflare docs or an accepted war story.
4. If allowed, run the static scanner from the project root. Use the absolute path to this skill's script (the `scripts/` directory next to this `SKILL.md`):
   ```bash
   python3 <skill-dir>/scripts/cfdoctor_static_scan.py .
   ```
   Treat scanner output as leads, not proof.
5. Inventory Cloudflare surface area: repo files, Wrangler config, bindings, IaC, package scripts, routes/domains, runtime code, migrations, tests, and any supplied account/dashboard evidence.
6. Map products and primitives, then read the applicable reference sections:
   - [`references/product-fit-rubric.md`](references/product-fit-rubric.md)
   - [`references/config-and-security-checks.md`](references/config-and-security-checks.md)
   - [`references/performance-and-reliability.md`](references/performance-and-reliability.md)
   - [`references/cost-footguns.md`](references/cost-footguns.md)
   - [`references/audit-engine-patterns.md`](references/audit-engine-patterns.md) for report/check/evidence patterns borrowed from React Doctor, Duckbill, Lighthouse, and IaC scanners
   - [`references/war-story-scenario-checklist.md`](references/war-story-scenario-checklist.md) for cross-platform horror-story scenarios to check
   - [`references/official-source-map.md`](references/official-source-map.md) for source links and date-sensitive pricing/limits verification
7. Produce findings in the required format below. Prioritize high-impact correctness, security, reliability, and cost findings over exhaustive trivia.

## Required audit output

Start with:

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
### <severity>: <short finding title>
- Category: <best-practice drift | wrong primitive | missed optimization | misconfiguration | cost footgun | security | reliability>
- Evidence: <file:line/config/account source/command output>
- Why it matters: <Cloudflare-specific behavior, limit, consistency model, billing mechanism, or failure mode>
- Fix: <smallest safe remediation; include better primitive/product if applicable>
- Cost / trade-off: <billing meter or cost proxy affected; expected benefit; implementation effort; latency/complexity/security downside; reversibility; assumptions>
- Verify: <command, dashboard check, load test, or config check>
- Source basis: <official Cloudflare docs URL(s) fetched this audit and/or accepted war story URL(s)>
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
- Ask before authenticated Cloudflare commands, even read-only ones, because they may expose account/project names or consume API rate limits.
- Never deploy, mutate bindings, create/delete resources, purge cache, change DNS/WAF/rules, or rotate secrets unless the user explicitly asks.
