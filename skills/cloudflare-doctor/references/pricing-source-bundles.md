# Pricing source bundles

Use this reference only after a concrete cost hypothesis identifies a product/meter. Never quote a mutable rate from this file: fetch the current official pages in the selected bundle and record the observation date.

## Required evidence record

For every pricing claim record:

```text
product:
claim_type: actual-charge | public-rate | meter-semantics | quota | transition | estimate
plan_or_contract:
region:
volume_and_unit:
retention:
observed_at:
effective_at:
source_urls:
conflicts:
assumptions:
```

Resolve sources by claim type, in this order:

1. **Actual customer charge:** invoice, contract/order form, then account billing export.
2. **Public unit rate:** current product pricing page.
3. **What is metered:** product billing/behavior documentation; do not infer it from a price table heading.
4. **Included quota/limit:** product limits page plus plan/entitlement evidence.
5. **Future or changed pricing:** changelog/announcement plus explicit effective date; do not apply it early.
6. **Estimated bill:** current rates and meter semantics combined with user-supplied usage assumptions. Return a range when plan, region, retention, or volume is uncertain.

Never average conflicting figures or silently prefer the newest-looking page. Record both figures, scope, effective date, and unresolved conflict.

## Product bundles

| Product | Public rate | Meter semantics / behavior | Limits | Usage / observability |
|---|---|---|---|---|
| Workers | https://developers.cloudflare.com/workers/platform/pricing/ | https://developers.cloudflare.com/workers/platform/pricing/ | https://developers.cloudflare.com/workers/platform/limits/ | https://developers.cloudflare.com/workers/observability/metrics-and-analytics/ |
| Workers Static Assets | https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/ | https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/ | https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/ | Workers metrics plus account usage |
| KV | https://developers.cloudflare.com/kv/platform/pricing/ | https://developers.cloudflare.com/kv/concepts/how-kv-works/ | https://developers.cloudflare.com/kv/platform/limits/ | account usage / Workers metrics |
| D1 | https://developers.cloudflare.com/d1/platform/pricing/ | https://developers.cloudflare.com/d1/observability/billing/ | https://developers.cloudflare.com/d1/platform/limits/ | https://developers.cloudflare.com/d1/observability/metrics-analytics/ |
| R2 | https://developers.cloudflare.com/r2/pricing/ | https://developers.cloudflare.com/r2/pricing/ | https://developers.cloudflare.com/r2/platform/limits/ | https://developers.cloudflare.com/r2/platform/metrics-analytics/ |
| Durable Objects | https://developers.cloudflare.com/durable-objects/platform/pricing/ | https://developers.cloudflare.com/durable-objects/platform/pricing/ | https://developers.cloudflare.com/durable-objects/platform/limits/ | https://developers.cloudflare.com/durable-objects/observability/metrics-and-analytics/ |
| Queues | https://developers.cloudflare.com/queues/platform/pricing/ | https://developers.cloudflare.com/queues/reference/delivery-guarantees/ | https://developers.cloudflare.com/queues/platform/limits/ | https://developers.cloudflare.com/queues/observability/ |
| Workflows | https://developers.cloudflare.com/workflows/reference/pricing/ | https://developers.cloudflare.com/workflows/build/rules-of-workflows/ | https://developers.cloudflare.com/workflows/reference/limits/ | account Workflow analytics |
| Workers AI | https://developers.cloudflare.com/workers-ai/platform/pricing/ | https://developers.cloudflare.com/workers-ai/platform/pricing/ | https://developers.cloudflare.com/workers-ai/platform/limits/ | Workers AI / AI Gateway usage |
| Vectorize | https://developers.cloudflare.com/vectorize/platform/pricing/ | https://developers.cloudflare.com/vectorize/platform/pricing/ | https://developers.cloudflare.com/vectorize/platform/limits/ | account Vectorize usage |
| Dynamic Workers | https://developers.cloudflare.com/dynamic-workers/pricing/ | https://developers.cloudflare.com/dynamic-workers/pricing/ | https://developers.cloudflare.com/dynamic-workers/usage/limits/ | loader/tenant usage and audit logs |
| Browser Run | https://developers.cloudflare.com/browser-run/pricing/ | https://developers.cloudflare.com/browser-run/pricing/ | https://developers.cloudflare.com/browser-run/limits/ | session metrics and close reasons |
| Containers | https://developers.cloudflare.com/containers/pricing/ | https://developers.cloudflare.com/containers/pricing/ | https://developers.cloudflare.com/containers/platform-details/limits/ | account container usage |
| Pipelines | https://developers.cloudflare.com/pipelines/platform/pricing/ | https://developers.cloudflare.com/pipelines/platform/pricing/ | https://developers.cloudflare.com/pipelines/platform/limits/ | account pipeline usage |
| Workers VPC | https://developers.cloudflare.com/workers-vpc/reference/pricing/ | https://developers.cloudflare.com/workers-vpc/reference/pricing/ | https://developers.cloudflare.com/workers-vpc/reference/limits/ | account VPC usage |
| Email Service | https://developers.cloudflare.com/email-service/platform/pricing/ | https://developers.cloudflare.com/email-service/api/send-emails/workers-api/ | https://developers.cloudflare.com/email-service/platform/limits/ | account email usage |
| Analytics Engine | https://developers.cloudflare.com/analytics/analytics-engine/pricing/ | https://developers.cloudflare.com/analytics/analytics-engine/sampling/ | product docs/current plan | account Analytics Engine usage |
| Images | https://developers.cloudflare.com/images/pricing/ | https://developers.cloudflare.com/images/optimization/binding/ | product limits/current plan | Images analytics/account usage |
| Stream | https://developers.cloudflare.com/stream/pricing/ | https://developers.cloudflare.com/stream/pricing/ | product limits/current plan | Stream analytics/delivered minutes |

## Compound bills

Build a meter graph rather than one blended rate. A Worker request may also trigger Worker CPU, D1 rows read/written, KV/R2 operations, Queue operations, AI inference, Browser sessions, third-party API charges, and logs. Calculate each meter separately, state shared assumptions once, then sum only compatible plan/region/effective-date estimates.

## Conflict handling examples

- **Future changelog versus current pricing page:** use the current page before the effective date; show the future estimate separately.
- **Enterprise contract versus public page:** contract/invoice governs actual charges; public pricing is only a comparison baseline.
- **Legacy entitlement:** mark unknown until account/contract evidence establishes whether migration occurred.
- **Dashboard estimate versus invoice:** dashboard is provisional usage evidence; invoice/contract controls settled charges.
