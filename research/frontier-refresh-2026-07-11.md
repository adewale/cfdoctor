# Cloudflare docs/Workers SDK frontier refresh

Date: 2026-07-11

## Scope

This discovery pass inspected 544 `cloudflare/cloudflare-docs` commits since 2026-06-01 and 1,160 `cloudflare/workers-sdk` issues updated since 2026-01-01. Commit history is first-party documentation-change evidence. Workers SDK issues are discovery/mechanism leads only; an issue title or report is not authority for current product semantics, prevalence, or pricing.

## Documentation fossils worth preserving

| Signal | Primary history | Audit implication |
|---|---|---|
| New KV-backed Durable Object namespaces restricted | https://github.com/cloudflare/cloudflare-docs/commit/4f4e60f1ac5113e9c90645e3d5ce65bddc12425f | Migration recommendations need account/deployment history; never rewrite applied migrations. |
| Images binding billing/cache behavior changed | https://github.com/cloudflare/cloudflare-docs/commit/10547a0f8f2d4cd061a136d4c70b550ea48093ab | Fetch current meter semantics before estimating transformations. |
| Workflows step pricing documented | https://github.com/cloudflare/cloudflare-docs/commit/f0dc1a0cc9225ad7fd1a67ebf5353252d1973d92 | Separate Workflow steps/storage/requests/CPU and effective dates. |
| Legacy Workers KV API routes deprecated | https://github.com/cloudflare/cloudflare-docs/commit/227282b7718a3e4c390c222f9404dc1694990bf3 | API collectors must follow current product APIs rather than freeze legacy paths. |
| AI Gateway account spend-limit language removed | https://github.com/cloudflare/cloudflare-docs/commit/5973fb7ed2e651a362ad8962eeda7879d9b7de7c | Never claim an account-level hard cap from stale docs; request current account evidence. |
| AI Gateway credits can go negative | https://github.com/cloudflare/cloudflare-docs/commit/17e3ce93e3d82e6eda5d2fed46dee4423bde876d | Credits/alerts are not automatically a hard execution stop. |
| Durable Object outbound connections can keep objects alive | https://github.com/cloudflare/cloudflare-docs/commit/f0c1f2c17b4566d1a16f681b64107e31bd5a9b9a | Duration/lifecycle review must include outbound sockets, not only WebSockets. |
| Stream warns about caching manifests | https://github.com/cloudflare/cloudflare-docs/commit/a56f785530d8e4c152472a017cef125055b03172 | Generic CDN-cache advice can break media semantics; use product-specific guidance. |
| Access JWT group claims can be dropped near cookie limits | https://github.com/cloudflare/cloudflare-docs/commit/703bf2df4882ddbde2e521d9fc312f0c40afb9ac | Authorization reviews should test effective claims, not only configured groups. |
| R2 object-permission API limitation documented | https://github.com/cloudflare/cloudflare-docs/commit/1014234c9d59b8de469f9fd3a9122f1f1c37695d | Targeted account reads must report unavailable fields rather than infer `false`. |

## Workers SDK issue leads

These remain discovery-only until reproduced and reconciled with current docs/releases:

- Environment/custom-domain inheritance can affect the wrong Worker: https://github.com/cloudflare/workers-sdk/issues/13925 and https://github.com/cloudflare/workers-sdk/issues/13439.
- A delete-only secret operation was reported to create a Worker: https://github.com/cloudflare/workers-sdk/issues/14052. This reinforces strict mutation separation.
- Secret bindings were reported missing at runtime despite version metadata: https://github.com/cloudflare/workers-sdk/issues/14004. Version metadata is evidence, not an end-to-end secret-availability test.
- Container development sidecars were reported to leak after deletion: https://github.com/cloudflare/workers-sdk/issues/14242.
- Inspector proxy workers were reported to grow without a DevTools client: https://github.com/cloudflare/workers-sdk/issues/14191.
- Pages deploy was reported to exit successfully after an error: https://github.com/cloudflare/workers-sdk/issues/14584. Automation should verify postconditions, not only exit status.
- `wrangler containers info` lacked JSON output: https://github.com/cloudflare/workers-sdk/issues/14035. Targeted reads must tolerate version-specific command gaps and stop rather than scrape unstable prose silently.

## Security and reliability expansion

Add these hypotheses only when matching evidence appears:

- **Environment-target drift:** compare selected config path, `env.*.name`, routes/custom domains, and deployed version identity before mutation.
- **Secret effective-state mismatch:** version metadata plus a user-approved non-secret health check; never request values.
- **Container lifecycle leak:** inventory named instances/sidecars and last-active timestamps; do not delete during diagnosis.
- **Access claim truncation:** inspect effective token claims using redacted samples when group-based authorization fails near size limits.
- **Media cache correctness:** do not apply generic Cache Rules to Stream manifests without current Stream guidance.
- **False-success deploy automation:** verify the intended deployment/version became active after a command reports success.

## New-product frontier

- Containers: resource/runtime/egress meters, instance cleanup, registries, Secrets Store references, observability volume.
- Pipelines: SQL transform and sink meters, fan-out, retention, replay, and open-beta limits.
- Workers VPC: beta/plan state, service reachability, request coupling, and future-effective pricing.
- Email Service: recipient volume, retries/bounces, abuse controls, and Workers/Queue amplification.
- Dynamic Workers: unique worker count, egress policy, custom limits, tenant denial-of-wallet, and code-hash reuse.
- Agents/Browser/Sandbox: max steps, cancellation, retries, session closure, tool egress, and downstream model/provider charges.

Current official navigation lives in `skills/cloudflare-doctor/references/official-source-map.md` and `pricing-source-bundles.md`.

## Missing-platform evidence matrix additions

| Platform | Current primary entry points | Cloudflare-fronted hypothesis |
|---|---|---|
| Deno Deploy | https://docs.deno.com/deploy/ and https://deno.com/deploy/pricing | Direct origin exposure, request/runtime/egress amplification, cache/rate-limit boundary |
| AWS Amplify | https://docs.aws.amazon.com/amplify/ and https://aws.amazon.com/amplify/pricing/ | Build/hosting/SSR usage, default-domain bypass, branch preview lifecycle |
| Dynamic Workers / Workers for Platforms | https://developers.cloudflare.com/dynamic-workers/ and https://developers.cloudflare.com/dynamic-workers/pricing/ | Tenant code capability bounds, unique-worker meters, egress, per-tenant quotas |

## Canonical workload profiles

These are synthetic stress-test assumptions, not observed ecosystem averages or price claims. Always show and let the user replace them. The public incidents motivate testing several orders of magnitude, not these exact values.

| Profile | Monthly edge requests | Paid binding operations/request | Duplicate/retry multiplier | Purpose |
|---|---:|---:|---:|---|
| Hobby | 100,000 | 1 | 1.01× | Detect minimum-plan/fixed-cost and accidental always-on resources |
| Launch | 10,000,000 | 2 | 1.05× | Normal launch traffic with modest retries and bindings |
| Production SaaS | 100,000,000 | 3 | 1.10× | Compound Worker/storage/Queue/log meters |
| Viral/abuse spike | 1,000,000,000 | 5 | 1.50× | Cache bypass, bot traffic, fan-out, and denial-of-wallet controls |

For each profile calculate requests, CPU/duration, every binding operation, retained logs, third-party charges, and retry/fan-out multipliers separately. Fetch current official rates and plan entitlements at evaluation time; never store a dollar total in the profile.

## ServerlessHorrors catalog sample

The `/all/` catalog exposed eight incident pages on 2026-07-11: AWS `$4.2k`, BigQuery `$22k`, Cloudflare `$36k`, Firebase `$100k` and `$70k`, Vercel `$46k` and `$700`, and Webflow `~$1.2k/month`. Every page is a secondary wrapper whose incident link is a Reddit or X post. The Cloudflare and Firebase `$100k` cases were already represented in the curated corpus; the other six did not pass the ledger's acceptance bar from catalog evidence alone. No rate, prevalence, or mechanism claim was promoted from the wrappers. Revisit only if a durable first-hand account, invoice/metrics, or independent corroboration becomes available.

Catalog: https://serverlesshorrors.com/all/

## Accepted reliability postmortems

Two first-party Cloudflare postmortems were added to the incident ledger:

- The 2025-06-12 outage showed how a third-party storage dependency in Workers KV propagated into Access, WARP, dashboard, and developer services. Audit implication: identify critical configuration/auth dependencies and verify independent degraded modes rather than assuming the edge is dependency-free.
- The 2025-11-18 outage showed an oversized generated feature file being rapidly propagated into core proxy software; alternating valid/invalid generations obscured diagnosis. Audit implication: validate generated configuration as hostile input, stage distribution, cap size/cardinality, retain a known-good artifact, and provide kill switches.

These establish mechanisms, not a claim that a customer repository currently has the same fault.

## Stop rules

- Do not promote SDK issue reports into accepted incidents without reproduction or corroborating primary evidence.
- Do not add a scanner check solely because an issue title contains a failure word.
- Do not quote rates from commit messages.
- Prefer one discriminating fixture/eval over a broad checklist item.
