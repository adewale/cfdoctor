# Audit engine patterns borrowed from React Doctor, Duckbill, and adjacent scanners

Use these patterns to make Cloudflare Doctor behave like a reproducible audit engine rather than a loose checklist.

## Borrowed patterns

### Doctor-style preflight

Sources: React Native CLI Doctor, Expo Doctor, React Doctor.

Pattern:
- Start with environment/readiness checks before deep findings.
- Validate required tools and permissions: Wrangler version, optional Terraform/Pulumi, Cloudflare API reachability, token scopes, selected account/zone, and whether billing/analytics collectors can run.
- Report collection gaps separately from product risks.

Cloudflare Doctor check examples:
- `CFDOC-PREFLIGHT-TOKEN-SCOPES`: token lacks read scopes for requested dashboard/account state.
- `CFDOC-PREFLIGHT-IAC-MISSING`: user asked for drift audit but no IaC/live export provided.
- `CFDOC-PREFLIGHT-DOCS-NOT-REFRESHED`: current Cloudflare docs could not be fetched.

### Runtime attribution and “why did this happen?”

Sources: React Profiler, React DevTools, React Scan, why-did-you-render.

Pattern:
- Prefer measured attribution over generic advice.
- Explain why a request missed cache, which route consumed CPU/subrequests, which DO shard is hot, which rule matched/skipped, or which job retried.

Cloudflare Doctor check examples:
- Synthetic request captures `CF-Cache-Status`, cache headers, route match, and Worker invocation evidence.
- API/analytics evidence shows top routes by CPU/subrequests/errors, D1 rows, R2/KV ops, Queue retries, DO duration.

### Rule metadata and stable findings

Sources: ESLint/React Doctor rule IDs, Semgrep, Checkov, tfsec, Snyk IaC.

Pattern:
- Every check has stable metadata: `id`, `title`, `pillar`, `resource_types`, `inputs`, `severity_floor`, `confidence`, `evidence_required`, `docs`, `remediation`, `autofix_safety`, `version`.
- Every finding is stable enough for baselines, suppressions, CI gates, JSON/SARIF, and diffing over time.

Cloudflare Doctor output requirements:
- Include check ID and version when possible.
- Include source provenance and evidence source in every finding.
- Support suppressions only with owner, reason, expiry, and ticket/reference.

### Scorecards and prioritized remediation cards

Sources: Lighthouse, AWS Trusted Advisor, AWS Well-Architected.

Pattern:
- Separate scores/summary from findings/evidence.
- Show category/pillar scorecards but do not let averages hide critical risks.
- Top actions should be remediation cards with severity, confidence, impact, effort, reversibility, source basis, and verification.

Recommended Cloudflare Doctor sections:
1. Run context / data freshness.
2. Pillar scorecards: Security, Reliability, Performance, Cost, Hygiene.
3. Top actions.
4. Cost proxy summary.
5. Drift/IaC summary.
6. Findings.
7. Not evaluated / missing evidence.
8. Suppressions / accepted risks.
9. Raw evidence appendix.

### Collect/eval split and account-state graph

Sources: Cloud Custodian, Lighthouse CI, IaC scanners.

Pattern:
- `collect`: build a redacted fact snapshot from Cloudflare API/GraphQL/IaC/Wrangler/screenshots.
- `eval`: run rules against that snapshot, offline/reproducibly.
- `diff`: compare against a baseline or prior run.
- `verify`: re-check a fixed finding.

Cloudflare fact graph should include:
- accounts, zones, DNS, TLS, WAF/rulesets/rate limiting/bot, cache rules, Workers/routes/deployments/crons/previews, Pages projects, KV/D1/R2/DO/Queues/Workflows, Dynamic Workers, Agents SDK resources, Artifacts, Access/Zero Trust, AI Gateway/Workers AI/Vectorize/Images/Stream/Browser Run, billing/usage, GraphQL analytics, IaC resources.

### Cost allocation, deltas, and unit economics

Sources: Duckbill/Last Week in AWS framing, AWS Cost Optimization Pillar, Infracost, Datadog Cloud Cost.

Pattern:
- Start with allocation: which account/zone/workload/route/product/owner drives spend?
- Prefer unit economics and deltas over generic “turn it off.”
- Show month-to-date, projected month-end, top deltas vs baseline, owner/tag attribution, assumptions, and confidence.

Cloudflare cost proxies:
- Workers requests and CPU are direct Standard-plan meters. Duration and subrequests are limits/amplification proxies under current Standard pricing; subrequests can trigger separately metered downstream products. Verify Enterprise/legacy contracts.
- D1 rows read/written and storage.
- KV reads/writes/lists and key churn.
- R2 storage + Class A/B operations + lifecycle gaps.
- DO requests/duration/storage writes/hot shards.
- Queue messages/retries/DLQ/backlog; Workflow invocations/steps/retained-state storage.
- Workers AI neurons/requests, AI Gateway tokens/cache hits/costs.
- Vectorize queried/stored dimensions.
- Images unique transformations/variants plus uncached binding executions, Stream delivered minutes, Browser Run session time/concurrency.
- Dynamic Worker requests/CPU/unique workers and Agent tool/browser/sandbox/model loops.
- Artifacts storage/operations/token/repo lifecycle metrics.
- Logpush/analytics volume and retention.

### IaC + live-cloud convergence

Sources: Checkov/Snyk IaC/Semgrep, Cloud Custodian.

Pattern:
- Repo/IaC and dashboard/API are different evidence planes.
- Label findings as:
  - `pre_deploy`: seen in IaC/code before deployment.
  - `live_drift`: live state differs from IaC/code intent.
  - `live_only`: exists only in dashboard/API state.
  - `iac_only`: declared but not observed live.

Cloudflare Doctor behavior:
- Do not claim dashboard state from repo files.
- Ask for live API/export/screenshots where needed.
- Report collection gaps explicitly.

### Safe remediation and governance

Sources: Cloud Custodian dry-run/action model, Well-Architected improvement plans, Checkov/tfsec suppressions.

Pattern:
- Default to dry-run and exact remediation instructions.
- Autofix only deterministic low-blast-radius changes.
- For dangerous dashboard/security/cost controls, provide dashboard path/API/IaC hint, rollback note, validation command, and ask for confirmation.
- Exceptions require reason, owner, expiry, and ticket/reference.

## Concrete finding schema

```yaml
id: CFDOC-COST-ASYNC-LOOP
check_version: 0.1.0
pillar: cost
severity: high
confidence: medium
evidence_quality: partial
resource:
  type: cloudflare_queue_consumer
  ref: wrangler.jsonc + src/consumer.ts
observed: consumer can enqueue same logical job without idempotency key
expected: idempotency key + max attempts + DLQ + run-summary metrics
source_basis:
  official:
    - https://developers.cloudflare.com/queues/configuration/batching-retries/
    - https://developers.cloudflare.com/queues/configuration/dead-letter-queues/
  war_story:
    - https://serverlesshorrors.com/all/cloudflare-36k
remediation:
  priority: fix_now
  effort: medium
  reversibility: high
  steps:
    - Add logical job ID and processed-job table/cache.
    - Bound retries and add DLQ.
    - Emit run summary with inputs/retries/DLQ/fanout/storage ops.
verify:
  - Unit/integration test duplicate message replay.
  - Queue metrics show retries/DLQ bounded after synthetic failure.
```
