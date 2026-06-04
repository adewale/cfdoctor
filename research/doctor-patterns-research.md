# Research: Borrowable doctor/audit patterns for Cloudflare Doctor

## Summary
Cloudflare Doctor should behave like a versioned audit engine, not a loose checklist: collect account/zone facts, evaluate explicit rules, attach reproducible evidence, and return prioritized remediation cards. The strongest borrowable patterns come from React’s dev-only/runtime diagnostics, Lighthouse/AWS score-and-risk reporting, IaC scanners’ provenance/suppression discipline, and cost tools’ allocation/diff/forecast workflows.

## Research angles
1. **React/doctor/debugging tools** — doctor commands, runtime instrumentation, profiler evidence, lint-style rule metadata, developer workflows.
2. **Cloud cost audit practice** — allocation, savings quantification, commitment caution, unit economics, forecast/diff reports.
3. **Adjacent audit engines** — Lighthouse, AWS Trusted Advisor/Well-Architected, Cloud Custodian, Checkov/tfsec/Semgrep/Snyk IaC, Infracost, Datadog Cloud Cost.
4. **Cloudflare-specific collection** — Cloudflare API/GraphQL/Observatory as fact sources; dashboard/IaC drift; cost/performance/security proxies.

## Findings
1. **Doctor UX should start with preflight checks, not deep audit.** React Native CLI’s doctor package and Expo Doctor validate local/project environment assumptions before users debug symptoms; borrow this for `cf doctor preflight` that checks token scopes, account/zone access, API reachability, optional Wrangler/Terraform presence, and whether required collectors can run before producing risk findings. [React Native CLI Doctor](https://github.com/react-native-community/cli/tree/main/packages/cli-doctor), [Expo Doctor](https://docs.expo.dev/develop/tools/#expo-doctor)
2. **React-style runtime instrumentation suggests “explain what actually happened.”** StrictMode deliberately reruns render/effect/ref logic to surface hidden bugs; Profiler/DevTools capture measured render cost; why-did-you-render/react-scan flag avoidable re-renders with component attribution. Cloudflare Doctor can analogously run synthetic requests and API/analytics probes to explain “why this request missed cache,” “why this rule matched,” “which Worker route is expensive,” or “which zone setting creates exposure,” with sampled evidence instead of static advice only. [React StrictMode](https://react.dev/reference/react/StrictMode), [React Profiler](https://react.dev/reference/react/Profiler), [React DevTools](https://react.dev/learn/react-developer-tools), [why-did-you-render](https://github.com/welldone-software/why-did-you-render), [React Scan](https://github.com/aidenybai/react-scan)
3. **Checks need machine-readable rule metadata.** ESLint React Hooks, Semgrep, Checkov, tfsec, and Snyk IaC all make findings traceable through rule IDs, severity, messages, file/resource locations, suppressions, and often SARIF/JSON outputs. Define every Cloudflare Doctor check with `id`, `title`, `pillar`, `resource_types`, `inputs`, `severity_floor`, `confidence`, `evidence_required`, `remediation`, `docs`, `autofix_safety`, and `version`; findings should be stable enough for baselines and CI gates. [eslint-plugin-react-hooks](https://react.dev/reference/eslint-plugin-react-hooks), [Semgrep rule syntax](https://semgrep.dev/docs/writing-rules/rule-syntax), [Checkov docs](https://www.checkov.io/), [tfsec ignores](https://aquasecurity.github.io/tfsec/v1.28.1/getting-started/configuration/ignores/), [Snyk IaC](https://docs.snyk.io/scan-with-snyk/snyk-iac)
4. **Report structure should separate score, evidence, and next action.** Lighthouse reports combine category scores, audit details, diagnostics, and opportunities; AWS Trusted Advisor groups checks by cost/security/fault tolerance/performance/service limits; Well-Architected reviews produce risks and improvement plans. Cloudflare Doctor should report: executive summary, run context/data freshness, pillar scorecards, top risks, cost proxy summary, findings, remediation backlog, suppressed/not-evaluated checks, and raw evidence appendix. [Lighthouse overview](https://developer.chrome.com/docs/lighthouse/overview/), [AWS Trusted Advisor](https://docs.aws.amazon.com/awssupport/latest/user/trusted-advisor.html), [AWS Well-Architected Tool](https://docs.aws.amazon.com/wellarchitected/latest/userguide/intro.html)
5. **Severity should be risk-based, but confidence must remain visible.** Lighthouse uses weighted 0–100 scoring and color bands while warning that performance scores vary; AWS Well-Architected distinguishes high/medium risks instead of hiding them in an average. Use separate `severity`, `confidence`, and `evidence_quality`: e.g. `severity = impact × likelihood × exposure × asset_criticality`, with policy floors for known dangerous states; do not let many low risks dilute one critical finding. [Lighthouse performance scoring](https://developer.chrome.com/docs/lighthouse/performance/performance-scoring/), [AWS Well-Architected Tool](https://docs.aws.amazon.com/wellarchitected/latest/userguide/intro.html)
6. **Trigger/eval design should support manual, scheduled, CI, and event-driven modes.** Cloud Custodian’s policy model separates resources, filters, actions, and execution modes; Lighthouse CI supports automated assertions/budgets. Borrow a two-phase design: `collect` account/IaC facts into a snapshot, then `eval` rules against the snapshot; support `doctor run`, `doctor ci`, `doctor diff --baseline`, `doctor scheduled`, and `doctor verify <finding>`. [Cloud Custodian policy docs](https://cloudcustodian.io/docs/policy/index.html), [Lighthouse CI configuration](https://github.com/GoogleChrome/lighthouse-ci/blob/main/docs/configuration.md)
7. **Evidence should be first-class and source-provenanced.** IaC tools cite file path/line; cloud tools cite resource IDs; performance tools cite measured metrics. Each Cloudflare finding should include resource reference, observed value, expected predicate, source type (`cloudflare_api`, `graphql_analytics`, `terraform`, `wrangler`, `observatory`, `synthetic_probe`), endpoint/query or file path/line, timestamp, collector version, token-scope caveats, and redaction status. [Cloudflare API docs](https://developers.cloudflare.com/api/), [Cloudflare GraphQL Analytics API](https://developers.cloudflare.com/analytics/graphql-api/), [Checkov suppression docs](https://www.checkov.io/2.Basics/Suppressing%20and%20Skipping%20Policies.html)
8. **Dashboard/account-state collection should create an inventory graph.** Cloudflare Doctor needs a reusable snapshot layer across account, zones, DNS, TLS, rulesets, WAF, cache, Workers, Access/Zero Trust, analytics, and optional IaC sources; rules should query this graph rather than calling APIs ad hoc. Cloudflare’s API and GraphQL analytics are the primary live sources; Terraform/Wrangler configs are source-of-truth candidates for drift checks. [Cloudflare API docs](https://developers.cloudflare.com/api/), [Cloudflare GraphQL Analytics API](https://developers.cloudflare.com/analytics/graphql-api/), [Cloudflare Terraform provider](https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs)
9. **Cost audit patterns start with allocation and unit economics, not generic “turn things off.”** Duckbill/Corey Quinn’s public cost-audit framing emphasizes understanding what drives spend and avoiding premature commitment purchases; AWS Cost Optimization formalizes expenditure awareness, cost-effective resources, demand/supply management, and continuous optimization. For Cloudflare, produce cost proxies by product/zone/workload: Workers invocations+CPU, R2 storage/class A/B ops, Images/Stream, Argo/traffic, cache miss bandwidth, Logpush volume, and plan/feature entitlements, with confidence labels when exact billing APIs are unavailable. [The Duckbill Group](https://www.duckbillgroup.com/), [Last Week in AWS blog](https://www.lastweekinaws.com/blog/), [AWS Cost Optimization Pillar](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html)
10. **Cost reports should show deltas, forecasts, and ownership.** Infracost is useful because it comments on cost diffs in PRs and models usage-based resources; Datadog Cloud Cost Management emphasizes allocation, tagging, recommendations, and trend exploration. Adapt this as `cost_proxy`: month-to-date estimate, projected month-end, top deltas vs baseline, owner/tag/account/zone attribution, and “savings estimate × confidence ÷ effort” prioritization. [Infracost docs](https://www.infracost.io/docs/), [Infracost usage-based resources](https://www.infracost.io/docs/features/usage_based_resources/), [Datadog Cloud Cost Management](https://docs.datadoghq.com/cloud_cost_management/)
11. **IaC-first and live-cloud scans must converge.** Checkov/Snyk IaC/Semgrep catch proposed misconfigurations before deploy; Cloud Custodian evaluates live cloud state. Cloudflare Doctor should compare Terraform/Wrangler/repo intent to Cloudflare dashboard/API reality and label findings as `pre_deploy`, `live_drift`, `live_only`, or `iac_only`; this prevents dashboard drift from being invisible and keeps CI from requiring production API credentials. [Checkov docs](https://www.checkov.io/), [Snyk IaC](https://docs.snyk.io/scan-with-snyk/snyk-iac), [Cloud Custodian docs](https://cloudcustodian.io/docs/)
12. **Remediation should be prioritized, reversible, and verifiable.** Well-Architected creates improvement plans; Cloud Custodian has dry-run/policy execution concepts; IaC scanners support skip/suppress workflows. Cloudflare Doctor should output remediation cards with impact, effort, blast radius, reversibility, exact dashboard path/API/Terraform snippet, validation command, rollback note, and exception mechanism requiring reason+owner+expiry. [AWS Well-Architected Tool](https://docs.aws.amazon.com/wellarchitected/latest/userguide/intro.html), [Cloud Custodian quickstart](https://cloudcustodian.io/docs/quickstart/index.html), [Checkov suppression docs](https://www.checkov.io/2.Basics/Suppressing%20and%20Skipping%20Policies.html)
13. **Performance audits can piggyback on Lighthouse/Cloudflare Observatory but add Cloudflare-specific diagnosis.** Cloudflare Observatory runs page tests and surfaces web-performance recommendations; Lighthouse provides comparable categories/audits. Cloudflare Doctor should accept a URL set, import Observatory/Lighthouse metrics when available, then map findings to Cloudflare actions: cache rules, compression, Polish/Images, Early Hints, Brotli, Workers route latency, origin TTFB, TLS settings, and cache-status evidence. [Cloudflare Observatory](https://developers.cloudflare.com/speed/observatory/), [Lighthouse overview](https://developer.chrome.com/docs/lighthouse/overview/)
14. **User-facing workflows should include baselines and exceptions to reduce alert fatigue.** Mature scanners allow severity thresholds, ignores/suppressions, CI exit codes, and machine-readable outputs. Add `--severity-threshold`, `--fail-on`, `--baseline`, `--suppressions`, `--json`, `--sarif`, `--markdown`, and exit codes: `0` pass/no threshold findings, `1` policy failure, `2` collection/eval error. [Semgrep docs](https://semgrep.dev/docs/), [Checkov CLI docs](https://www.checkov.io/2.Basics/CLI%20Command%20Reference.html), [tfsec docs](https://aquasecurity.github.io/tfsec/v1.28.1/)

## Actionable recommendations for Cloudflare Doctor
1. **Introduce a versioned check/evidence contract.** Store checks as data/code modules with stable IDs, input fact requirements, severity formula, confidence logic, docs links, and remediation templates. Output findings as Markdown plus JSON/SARIF.
2. **Split collection from evaluation.** Implement `cf doctor collect --account --zones --sources api,graphql,iac,observatory --redact` to create `facts.json`; run `cf doctor eval facts.json` locally/offline for reproducibility and tests.
3. **Build a Cloudflare account-state graph.** Minimum collectors: accounts/zones, DNS records, TLS/certs/HTTPS/HSTS/min TLS, rulesets/WAF/rate limiting/bot, cache/page/transform/redirect rules, Workers/scripts/routes/KV/R2/D1/Queues where accessible, Access/Zero Trust high-level policies, GraphQL analytics, Observatory URLs, Terraform/Wrangler configs.
4. **Require evidence for every non-informational finding.** No finding without resource ID, observed value, expected predicate, source provenance, timestamp, and confidence. Use `not_evaluated` when token scope or plan prevents confirmation.
5. **Adopt a report shape users can act on.** Sections: run context; top 5 actions; pillar scorecards; critical/high findings; cost proxy summary; drift summary; all findings; suppressed/accepted risks; raw evidence/provenance appendix.
6. **Use risk scoring with separate confidence.** Severity bands: Critical/High/Medium/Low/Info. Inputs: exposure, traffic/revenue criticality, exploitability, blast radius, misconfiguration certainty, and policy floor. Keep confidence separate from severity.
7. **Add cost proxy summaries before exact billing integration.** Show top zones/products by usage, cache-hit/miss cost implications, Workers/R2/Images/Stream/Logpush usage, MTD forecast, baseline deltas, and savings estimates with confidence/assumptions.
8. **Prioritize remediation by impact, effort, reversibility, and evidence quality.** Create buckets: `Fix now`, `Quick win`, `Cost investigation`, `Needs owner decision`, `Monitor`, `Accepted risk`. Include verification commands/probes.
9. **Support four workflows.** Interactive first run; CI/IaC gate; scheduled drift/cost scan; incident/investigation mode (`doctor explain <resource|finding>` with probes and analytics context).
10. **Add suppressions with governance.** `cfdoctor.yaml` should allow suppressing specific check/resource pairs only with reason, owner, expiry, and ticket URL; expired suppressions fail CI.
11. **Prefer safe recommendations over automatic mutation.** Offer `--fix` only for deterministic, low-blast-radius changes and default to dry-run/Terraform patch suggestions; never auto-change security/TLS/WAF behavior without explicit confirmation.
12. **Make source provenance visible to users.** Label citations and evidence as official Cloudflare docs/API, first-party project docs, third-party tool practice, or war-story/blog; include retrieval date and checker version.

## Proposed finding schema
```yaml
finding:
  id: CFDOC-SEC-001
  check_version: 1.2.0
  title: Zone allows weak TLS minimum version
  pillar: security
  severity: high
  confidence: high
  status: fail
  resource:
    type: cloudflare_zone_setting
    account_id: redacted
    zone_id: redacted
    name: example.com
  evidence:
    observed: min_tls_version = "1.0"
    expected: min_tls_version >= "1.2"
    source_type: cloudflare_api
    source_ref: GET /zones/{zone_id}/settings/min_tls_version
    collected_at: 2026-06-04T00:00:00Z
    token_scopes: [Zone Settings Read]
  risk:
    impact: high
    likelihood: medium
    exposure: internet_facing
    rationale: Public zone accepts legacy TLS clients.
  remediation:
    priority: fix_now
    effort: low
    reversibility: high
    dashboard_path: SSL/TLS > Edge Certificates > Minimum TLS Version
    api_or_iac_hint: set minimum TLS version to 1.2 or higher
    verify: cf doctor verify CFDOC-SEC-001 --zone example.com
  provenance:
    docs:
      - type: official
        url: https://developers.cloudflare.com/api/
```

## Concrete report structure
1. **Header/run context** — account/zone scope, sources enabled, token scopes observed, checker version, data freshness, redaction mode.
2. **Executive summary** — score bands by Security, Reliability, Performance, Cost, Hygiene; critical/high counts; collection gaps.
3. **Top actions** — 5–10 remediation cards sorted by severity, savings/risk reduction, confidence, effort.
4. **Cost proxy** — MTD/projected usage, top deltas, cache miss indicators, usage assumptions, unknowns.
5. **Drift/IaC** — desired vs live conflicts, dashboard-only resources, IaC-only resources.
6. **Findings** — grouped by pillar and severity; each has evidence, source, remediation, verification.
7. **Exceptions** — accepted risks/suppressions with owner/expiry.
8. **Appendix** — raw fact inventory, API/GraphQL queries, Observatory/Lighthouse snapshots, citations.

## Sources
- Kept: React Native CLI Doctor (`https://github.com/react-native-community/cli/tree/main/packages/cli-doctor`) — first-party project docs/source for doctor-style preflight checks.
- Kept: Expo Doctor (`https://docs.expo.dev/develop/tools/#expo-doctor`) — official project docs for dependency/config validation workflow.
- Kept: React StrictMode/Profiler/DevTools (`https://react.dev/reference/react/StrictMode`, `https://react.dev/reference/react/Profiler`, `https://react.dev/learn/react-developer-tools`) — official React diagnostics patterns.
- Kept: why-did-you-render and React Scan (`https://github.com/welldone-software/why-did-you-render`, `https://github.com/aidenybai/react-scan`) — first-party project docs for runtime attribution/noise reduction ideas.
- Kept: Lighthouse docs/scoring/CI (`https://developer.chrome.com/docs/lighthouse/overview/`, `https://developer.chrome.com/docs/lighthouse/performance/performance-scoring/`, `https://github.com/GoogleChrome/lighthouse-ci/blob/main/docs/configuration.md`) — official/first-party scoring, budgets, report patterns.
- Kept: AWS Trusted Advisor, Well-Architected, Cost Optimization Pillar (`https://docs.aws.amazon.com/awssupport/latest/user/trusted-advisor.html`, `https://docs.aws.amazon.com/wellarchitected/latest/userguide/intro.html`, `https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html`) — official risk/check/improvement-plan models.
- Kept: Cloud Custodian (`https://cloudcustodian.io/docs/`, `https://cloudcustodian.io/docs/policy/index.html`) — first-party project docs for resource/filter/action policy engine and live-cloud governance.
- Kept: Checkov, tfsec, Semgrep, Snyk IaC (`https://www.checkov.io/`, `https://aquasecurity.github.io/tfsec/v1.28.1/`, `https://semgrep.dev/docs/`, `https://docs.snyk.io/scan-with-snyk/snyk-iac`) — first-party/official scanner docs for rule metadata, suppressions, CI outputs.
- Kept: Infracost and Datadog Cloud Cost (`https://www.infracost.io/docs/`, `https://docs.datadoghq.com/cloud_cost_management/`) — first-party/official cost diff, allocation, recommendation workflows.
- Kept: Cloudflare API, GraphQL Analytics, Terraform provider, Observatory (`https://developers.cloudflare.com/api/`, `https://developers.cloudflare.com/analytics/graphql-api/`, `https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs`, `https://developers.cloudflare.com/speed/observatory/`) — official/first-party Cloudflare collection and performance sources.
- Kept: The Duckbill Group / Last Week in AWS (`https://www.duckbillgroup.com/`, `https://www.lastweekinaws.com/blog/`) — war-story/blog category for cloud-cost audit framing and practitioner heuristics.
- Dropped: Generic “top cloud cost tools” listicles — too SEO-heavy and thin on check/evidence design.
- Dropped: Vendor marketing pages without docs/API/report examples — insufficient implementation detail.
- Dropped: Old React performance blog posts superseded by current `react.dev` docs — stale compared with current official guidance.

## Gaps
- Runtime did not expose `web_search`/fetch tools, so URLs and recent project changes were not live-verified during this pass; link-check before publishing externally.
- Cloudflare exact billing/usage API availability varies by plan/product and may not expose enough cost detail; validate with real accounts and token scopes.
- Severity and cost formulas need calibration against real Cloudflare incidents, user traffic, and billing samples.
- Current `cfdoctor` implementation was not inspected; map these recommendations to existing architecture before planning changes.
