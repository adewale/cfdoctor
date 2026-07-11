# Verified Cloudflare best-practices docs

This file is a source map, not a substitute for live documentation. The auditor must prefer current Cloudflare docs over model memory.

## Current-docs rule

Before making or finalizing a Cloudflare best-practice, limit, pricing, product-fit, or configuration claim:

1. Fetch Cloudflare's current documentation index:
   ```bash
   curl -fsSL https://developers.cloudflare.com/llms.txt
   ```
2. Fetch the relevant product index, for example:
   ```bash
   curl -fsSL https://developers.cloudflare.com/workers/llms.txt
   curl -fsSL https://developers.cloudflare.com/d1/llms.txt
   ```
3. Fetch the relevant page as Markdown. Cloudflare documents support Markdown retrieval via `index.md` links in `llms.txt`, or with an `Accept: text/markdown` header:
   ```bash
   curl -fsSL https://developers.cloudflare.com/workers/best-practices/workers-best-practices/index.md
   curl -fsSL -H 'Accept: text/markdown' https://developers.cloudflare.com/workers/best-practices/workers-best-practices/
   ```
4. Cite the URL(s) used in findings when the claim depends on product behavior, pricing, limits, or a best practice.
5. If live docs cannot be fetched, say so explicitly: **"Cloudflare docs were not refreshed; this claim needs current-doc verification."** Do not present memory-only claims as verified current guidance.

## Verification note

The list below was discovered from official Cloudflare `llms.txt` product indexes. Critical pricing/semantics pages for Workers, Workers Cache, D1, Durable Objects/migrations, Queues, Workflows, and Images were content-verified on 2026-07-11; the repo-only `evals/link-check-policy.json` records the semantic anchors and review deadline. Runtime reference links were also rechecked and canonical redirects updated. Treat this as a starting set to fetch at audit time, not a frozen copy of Cloudflare guidance.

## Application/security/account docs

- [Account and domain management best practices](https://developers.cloudflare.com/fundamentals/reference/best-practices/index.md) — Protect your Cloudflare account and domains by decentralizing access, managing billing, and planning for continuity.
- [Terraform Best practices](https://developers.cloudflare.com/terraform/advanced-topics/best-practices/index.md) — Recommended directory structure, state management, and workflow practices for Cloudflare Terraform.
- [Get started with API Shield](https://developers.cloudflare.com/api-shield/get-started/index.md) — Set up API Shield to identify and address API security best practices.
- [Rate limiting best practices](https://developers.cloudflare.com/waf/rate-limiting-rules/best-practices/index.md) — Typical rate limiting configurations for login protection, API abuse, and more.
- [Proactive DDoS defense](https://developers.cloudflare.com/ddos-protection/best-practices/proactive-defense/index.md) — Strengthen your application against DDoS attacks before they happen.
- [Third-party services and DDoS protection](https://developers.cloudflare.com/ddos-protection/best-practices/third-party/index.md) — DDoS rule interactions with third-party services.
- [Deploy content security rules in production](https://developers.cloudflare.com/client-side-security/best-practices/deploy-rules-in-production/index.md) — Safe practices for deploying and updating content security rules.
- [Handle a client-side resource alert](https://developers.cloudflare.com/client-side-security/best-practices/handle-an-alert/index.md) — Investigation guidance for client-side resource alerts.
- [Designing ZTNA access policies for Cloudflare Access](https://developers.cloudflare.com/reference-architecture/design-guides/designing-ztna-access-policies/index.md) — Best practices and guidelines for building Access policies.

## Workers, Pages, Workflows, and data platform docs

- [Workers Best Practices](https://developers.cloudflare.com/workers/best-practices/workers-best-practices/index.md) — Code patterns and configuration guidance for fast, reliable, observable, and secure Workers.
- [Workers Cache](https://developers.cloudflare.com/workers/cache/index.md) and [Workers Cache limitations](https://developers.cloudflare.com/workers/cache/limitations/index.md) — Declarative per-Worker cache: enabling `cache.enabled`, tiered cache, request collapsing, the billing-surface change (hits still bill a request; normally-free static-asset and worker-to-worker requests become billed), per-entrypoint `cache.enabled = false` for auth/gateway entrypoints, and how it differs from the Cache API.
- [Workers RPC](https://developers.cloudflare.com/workers/runtime-apis/rpc/index.md), [RPC TypeScript](https://developers.cloudflare.com/workers/runtime-apis/rpc/typescript/index.md), and [RPC visibility/security](https://developers.cloudflare.com/workers/runtime-apis/rpc/visibility/index.md) — JavaScript-native RPC surface for Workers and Durable Objects, including generated TypeScript exposure and visibility rules.
- [Wrangler configuration](https://developers.cloudflare.com/workers/wrangler/configuration/index.md) — Current config-file formats; Cloudflare recommends `wrangler.jsonc` for new projects while still supporting JSON and TOML.
- [Pages C3 CLI](https://developers.cloudflare.com/pages/get-started/c3/index.md) — New-project setup guide that follows Cloudflare and framework best practices.
- [Rules of Workflows](https://developers.cloudflare.com/workflows/build/rules-of-workflows/index.md) — Best practices for resilient Workflows, idempotency, state management, and error handling.
- [Agents: long-running agents](https://developers.cloudflare.com/agents/concepts/agentic-patterns/long-running-agents/index.md) — Wake-on-demand, restart survival, and long-running work patterns for Cloudflare Agents.
- [Agents: retries](https://developers.cloudflare.com/agents/runtime/execution/retries/index.md) — Built-in retry behavior with backoff/jitter for Agents SDK operations.
- [Agents: observability](https://developers.cloudflare.com/agents/runtime/operations/observability/index.md) — Diagnostics and structured events for Agent state, RPC, schedules, workflows, and MCP connections.
- [Dynamic Workers: egress control](https://developers.cloudflare.com/dynamic-workers/usage/egress-control/index.md) — Restrict, intercept, and audit outbound network access for dynamically loaded Workers.
- [Dynamic Workers: custom limits](https://developers.cloudflare.com/dynamic-workers/usage/limits/index.md) — Limit resource usage of Dynamic Workers.
- [D1: Import and export data](https://developers.cloudflare.com/d1/best-practices/import-export-data/index.md) — Import/export practices for D1.
- [D1: Local development](https://developers.cloudflare.com/d1/best-practices/local-development/index.md) — Run D1 locally before deploying to production.
- [D1: Query a database](https://developers.cloudflare.com/d1/best-practices/query-d1/index.md) — Query D1 through bindings, REST API, or Wrangler.
- [D1: Global read replication](https://developers.cloudflare.com/d1/best-practices/read-replication/index.md) — Reduce read latency and scale throughput with read replication.
- [D1: Remote development](https://developers.cloudflare.com/d1/best-practices/remote-development/index.md) — Develop remotely against D1.
- [D1: Retry queries](https://developers.cloudflare.com/d1/best-practices/retry-queries/index.md) — Retry transient D1 write-query errors with exponential backoff.
- [D1: Use indexes](https://developers.cloudflare.com/d1/best-practices/use-indexes/index.md) — Improve D1 query performance with indexes.
- [Durable Objects: Access Durable Objects Storage](https://developers.cloudflare.com/durable-objects/best-practices/access-durable-objects-storage/index.md) — Read/write persistent data in Durable Objects.
- [Durable Objects: Invoke methods](https://developers.cloudflare.com/durable-objects/best-practices/create-durable-object-stubs-and-send-requests/index.md) — Call RPC methods or fetch Durable Objects through stubs.
- [Durable Objects: Error handling](https://developers.cloudflare.com/durable-objects/best-practices/error-handling/index.md) — Handle exceptions, retryable errors, and overload.
- [Durable Objects: Rules of Durable Objects](https://developers.cloudflare.com/durable-objects/best-practices/rules-of-durable-objects/index.md) — Design guidelines for correct Durable Object applications.
- [Durable Objects: Use WebSockets](https://developers.cloudflare.com/durable-objects/best-practices/websockets/index.md) — Serve WebSockets using standard and Hibernation APIs.
- [R2 SQL: Limitations and best practices](https://developers.cloudflare.com/r2-sql/reference/limitations-best-practices/index.md) — Supported features, known limitations, and R2 SQL query best practices.
- [R2 SQL: Reference](https://developers.cloudflare.com/r2-sql/reference/index.md) — R2 SQL reference documentation for limitations, best practices, and Wrangler commands.
- [Vectorize: Create indexes](https://developers.cloudflare.com/vectorize/best-practices/create-indexes/index.md) — Create Vectorize indexes and choose dimensions/distance metrics.
- [Vectorize: Insert vectors](https://developers.cloudflare.com/vectorize/best-practices/insert-vectors/index.md) — Insert/upsert vectors and use namespaces.
- [Vectorize: List vectors](https://developers.cloudflare.com/vectorize/best-practices/list-vectors/index.md) — Enumerate vector identifiers with pagination.
- [Vectorize: Query vectors](https://developers.cloudflare.com/vectorize/best-practices/query-vectors/index.md) — Query vectors with metadata filters and namespaces.
- [Artifacts: Best practices for Artifacts](https://developers.cloudflare.com/artifacts/concepts/best-practices/index.md) — Repo, token, metadata, and namespace patterns.

## DNS and migration docs

- [DNS: Migrate DNS from BIND](https://developers.cloudflare.com/learning-paths/dns-best-practices/concepts/index.md) — Best practices for migrating DNS from BIND to Cloudflare.
- [DNS best practices: Phase 1 Planning & Inventory](https://developers.cloudflare.com/learning-paths/dns-best-practices/concepts/phase-1/index.md) — Plan and inventory DNS migration.
- [DNS best practices: Phase 2 Preparation](https://developers.cloudflare.com/learning-paths/dns-best-practices/concepts/phase-2/index.md) — Prepare for DNS migration with minimal downtime.
- [DNS best practices: Phase 3 Execution](https://developers.cloudflare.com/learning-paths/dns-best-practices/concepts/phase-3/index.md) — Execute the nameserver cutover.
- [DNS best practices: Phase 4 Post-migration and DNSSEC re-activation](https://developers.cloudflare.com/learning-paths/dns-best-practices/concepts/phase-4/index.md) — Verify and stabilize after migration.
- [DNS best practices: Key considerations and summary](https://developers.cloudflare.com/learning-paths/dns-best-practices/concepts/summary-considerations/index.md) — Review DNS migration best-practice summary.

## Zero Trust, Gateway, and network security docs

- [Cloudflare One traffic policies: Get started](https://developers.cloudflare.com/cloudflare-one/traffic-policies/get-started/index.md) — Best practices for phased Gateway policy deployment.
- [Cloudflare One packet filtering: Best practices](https://developers.cloudflare.com/cloudflare-one/traffic-policies/packet-filtering/best-practices/index.md) — Gateway packet-filtering best practices.
- [Cloudflare One packet filtering: Extended ruleset](https://developers.cloudflare.com/cloudflare-one/traffic-policies/packet-filtering/best-practices/extended-ruleset/index.md) — Configure an extended ruleset.
- [Cloudflare One packet filtering: Magic Transit egress](https://developers.cloudflare.com/cloudflare-one/traffic-policies/packet-filtering/best-practices/magic-transit-egress/index.md) — Configure Magic Transit egress.
- [Cloudflare One packet filtering: Minimal ruleset](https://developers.cloudflare.com/cloudflare-one/traffic-policies/packet-filtering/best-practices/minimal-ruleset/index.md) — Configure a minimal ruleset.
- [Email Security: Detection settings best practices](https://developers.cloudflare.com/cloudflare-one/email-security/settings/detection-settings/best-practices/index.md) — Email Security detection settings.
- [Cloudflare Mesh: Tips and best practices](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-mesh/tips/index.md) — Zero Trust networking tips and best practices.
- [Proxy endpoints: PAC file best practices](https://developers.cloudflare.com/cloudflare-one/networks/resolvers-and-proxies/proxy-endpoints/best-practices/index.md) — PAC file best practices.
- [Network Firewall: Best practices](https://developers.cloudflare.com/cloudflare-network-firewall/best-practices/index.md) — Configure Network Firewall.
- [Network Firewall: Extended ruleset](https://developers.cloudflare.com/cloudflare-network-firewall/best-practices/extended-ruleset/index.md) — Extended ruleset configuration.
- [Network Firewall: Magic Transit egress](https://developers.cloudflare.com/cloudflare-network-firewall/best-practices/magic-transit-egress/index.md) — Magic Transit egress configuration.
- [Network Firewall: Minimal ruleset](https://developers.cloudflare.com/cloudflare-network-firewall/best-practices/minimal-ruleset/index.md) — Minimal ruleset configuration.
- [Clientless Access: Access application best practices](https://developers.cloudflare.com/learning-paths/clientless-access/access-application/best-practices/index.md) — Recommended clientless Access deployment practices.
- [Clientless Access: Connect private applications best practices](https://developers.cloudflare.com/learning-paths/clientless-access/connect-private-applications/best-practices/index.md) — Recommended private application connection practices.
- [Clientless Access: Migrate applications best practices](https://developers.cloudflare.com/learning-paths/clientless-access/migrate-applications/best-practices/index.md) — Recommended migration practices.
- [Secure Internet Traffic: Egress IP best practices](https://developers.cloudflare.com/learning-paths/secure-internet-traffic/build-egress-policies/deploy-egress-ips/index.md) — Deploy dedicated egress IPs effectively.

## Specialized product docs

- [Waiting Room best practices](https://developers.cloudflare.com/waiting-room/reference/best-practices/index.md) — Configure and test waiting rooms.
- [BYOIP dynamic advertisement best practices](https://developers.cloudflare.com/byoip/concepts/dynamic-advertisement/best-practices/index.md) — Manage dynamic IP prefix advertisement.
- [BYOIP IRR entries best practices](https://developers.cloudflare.com/byoip/concepts/irr-entries/best-practices/index.md) — Create and maintain IRR entries.
- [Pulumi: Manage secrets with Pulumi ESC](https://developers.cloudflare.com/pulumi/tutorial/manage-secrets/index.md) — Develop with Wrangler while following security best practices.
- [Cloudflare docs Writing guidelines](https://developers.cloudflare.com/style-guide/documentation-content-strategy/writing-guidelines/index.md) — Cloudflare documentation writing best practices; relevant only when auditing docs/content workflows.
