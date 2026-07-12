# Review of accessible `adewale/*` Wrangler JSONC configurations

Date: 2026-07-11

## Was this review already done?

No. Earlier work validated the snapshot workflow against three selected live projects and inspected repository fixtures, but it did not enumerate every accessible `github.com/adewale/*` repository or parse every default-branch `wrangler.jsonc`. The pricing source-bundle consolidation was also still only a proposed follow-up.

## Scope and method

The review enumerated all 86 repositories accessible through the authenticated GitHub session (81 public, five private), then requested each default branch's recursive Git tree. All 86 trees completed with no API failure and no truncated tree. The review fetched and parsed every matching file:

| Class | Configs | Repositories | Treatment |
|---|---:|---:|---|
| Deployable project configs | 24 | 23 | Primary project evidence |
| Maintained examples/compatibility tests | 60 | 5 | Design and parser-coverage evidence, not production prevalence |
| `cfdoctor` detection/benchmark fixtures | 20 | 1 | Intentional test data |
| `demoscene/corpus-cache` copies | 230 | 1 | Generated/vendored corpus; excluded from project prevalence |
| **Total** | **334** | **28** | All parsed |

One parse failure was the intentionally malformed `cfdoctor` fixture. No Git tree was skipped. Four deployable configs were from private repositories; only aggregate counts were used here, and no private repository name, path, identifier, or value was retained in this report.

The 20 public deployable configs came from 19 repositories: `MaintainerBot`, `agentic-mermaid`, `bobbin`, `demoscene`, `embed.oshineye.dev`, `fibonacci_durable_object`, `flux-search`, `keyboardia`, `lempicka`, `next-starter-template`, `oshineye-dev`, `planet_cf`, `pythonbyexample`, `sunrise`, `sunrise-deploy`, `swiss-poster-skill`, `tasche`, `vaders`, and `who-to-bother-at-on-x`. `tasche` contains two independent Worker configs. The example class covered `cfboundary`, `planet_cf`, `python-workers-examples`, `python-workers-issues`, and `xampler`.

This was a repository-only GitHub review. It performed no Cloudflare account read and no mutation.

## Observed public-project patterns

These counts describe this repository set only; they are not ecosystem prevalence claims.

- 13/20 configs used Workers Static Assets.
- 11/20 enabled observability; seven explicitly configured full (`1`) head sampling for at least one observability surface.
- Seven configured Queues, with 12 producer and ten consumer entries. Three consumer entries had no configured dead-letter queue.
- Seven used D1, six routes, six triggers, five Durable Object migrations, four version-metadata bindings, four Workers AI, three Vectorize, and three service-binding targets.
- Two public configs used `env.*` deployment overrides; one public repository contained two separate Wrangler configs.
- The broader example/corpus classes exercised newer keys that the scanner did not inventory: `containers`, `dispatch_namespaces`, `pipelines`, `ratelimits`, `secrets_store_secrets`, `send_email`, and `vpc_services`.
- Exact duplicates confirmed that `demoscene/corpus-cache` contains copies of owner projects. Counting or scanning those copies as live projects would double-count evidence and manufacture findings.

## Lessons for the PR and skill

### 1. Metadata-only should be the collection default

Static Assets appeared in 13/20 public deployable configs and 16/24 deployable configs including private projects. Wrangler's direct Worker dashboard importer currently rejects Workers with Assets, while source/config download also expands the privacy boundary. Metadata collection is both more broadly compatible and least-privilege. Source/config download should require a separate explicit opt-in in the reviewed plan.

### 2. Repository intent needs an explicit deployment identity

`env.*` blocks and multiple Wrangler configs make the top-level `name` ambiguous. Collection should require confirmation of the concrete deployed name and treat each Worker or Pages project as a separate target. Repository path, root name, and environment label are context; none alone proves deployed identity.

### 3. Service Bindings create a bounded dependency graph

Version metadata can reveal Service Bindings to separately deployed Workers. A snapshot of one Worker is not evidence about the target's active version or settings. Do not recursively expand authenticated scope. Mark referenced services unresolved and request separately planned snapshots only when a concrete hypothesis depends on them.

### 4. Generated corpora need scanner hygiene

A repository-wide scanner would otherwise traverse 230 cached corpus configs, including exact copies of owner projects. `corpus-cache` is now a default excluded directory. Maintained examples remain in scope because they are intentional source rather than generated copies.

### 5. Product inventory must track Wrangler's evolving schema

The scanner recognized core bindings but omitted several current top-level Wrangler families represented in maintained examples and the discovery corpus. Inventory now recognizes Static Assets, Containers, Dynamic Workers dispatch namespaces, Pipelines, Rate Limiting bindings, Secrets Store, email bindings, and Workers VPC. These are inventory signals, not automatic findings.

### 6. Frequent configuration is not automatically a defect

Full observability sampling occurred repeatedly, but repository config alone does not establish traffic, retained volume, plan, or cost impact. The skill should request usage and billing evidence before making a cost finding. Likewise, absence of a field is not proof of absent dashboard state.

Queue consumers without a configured DLQ remain useful static reliability leads because current Queue retry/deletion semantics are documented, but the report must state defaults precisely and distinguish repository intent from effective account state.

### 7. Pricing coverage follows detected product families

Containers, Pipelines, Workers VPC, Static Assets, Rate Limiting bindings, Secrets Store, and email bindings showed that pricing/limits navigation was narrower than the Wrangler surface. The official source map now includes the applicable current docs, pricing, and limits entry points. Exact cost claims still require the product-specific source bundle: pricing, meter semantics, limits, plan/contract, observability, changelog/effective date, and observation date.

## Changes made from this review

- Changed `capture_wrangler_snapshot.py` to default to metadata-only and require `--include-source-config` for Worker source/config or Pages config download.
- Added tests for the safer default and retained explicit full-download boundary tests.
- Added deployed-name, environment, multi-config, Service Binding, and Static Assets guidance to the Wrangler snapshot reference.
- Excluded `corpus-cache` from default scanner traversal and added an adversarial test.
- Expanded modern Wrangler product inventory and its test coverage.
- Added current official source-map routes for the newly observed product families.

## Evidence handling

Raw repository config copies and private-repository metadata were kept only in a temporary local analysis directory and deleted after the aggregate report was produced. This report retains only public names and aggregate private counts. No source file, config value, resource identifier, route, secret name, account metadata, or Cloudflare credential from a private repository is included.
