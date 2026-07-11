# Web and Cloudflare documentation refresh — 2026-07-11

## Scope and method

This refresh used live HTTP/GitHub data, not model memory:

- fetched the Cloudflare developer changelog as Markdown;
- inspected 125 `cloudflare/cloudflare-docs` commits since 2026-07-01 and fetched the relevant commit patches;
- fetched current official pricing/configuration pages with `Accept: text/markdown`;
- searched Hacker News through the Algolia and Firebase APIs;
- searched recent GitHub issues globally and in `cloudflare/workers-sdk`;
- fetched and read candidate operator posts and first-party Cloudflare postmortems;
- deduplicated candidates against `research/incident-claim-ledger.json` by causal source cluster.

Bing results were mostly generic/low-signal and were rejected. Reddit's search API returned HTTP 403, so no Reddit-only candidate was accepted without another reachable primary source. Search coverage is broad but not exhaustive or authenticated.

## Material Cloudflare documentation changes

### 1. Workflows now has a step meter and announced storage/step billing

**Decision: update runtime guidance and semantic anchors.**

Cloudflare's July 7 update says Workflows uses Workers request/CPU meters plus persisted storage and executed steps. A step includes durable operations such as sleeping or waiting for events. Paid-plan step and storage billing starts **no earlier than August 10, 2026**; current-invoice claims must continue to check the changelog rather than assume the announced date has passed.

Sources:

- https://developers.cloudflare.com/workflows/reference/pricing/
- https://developers.cloudflare.com/changelog/post/2026-07-07-workflows-billing-updates/

Effect on cfdoctor:

- Add Workflow step count and retained state to cost proxies.
- Treat trivial/excessive steps, unbounded child workflows, and long state retention as review targets.
- Do not claim that idle sleep time consumes CPU; it is a step and persisted-state concern instead.
- Do not add a raw `step.do` count scanner warning: semantic step boundaries and runtime `stepCount` evidence are needed.

### 2. Workflows supports dynamic retry-delay functions

**Decision: update retry guidance.**

As of July 9, `retries.delay` can derive the next delay from `ctx.attempt` and the thrown error, including provider `Retry-After` behavior. `NonRetryableError` remains the explicit terminal-failure path.

Source: https://developers.cloudflare.com/workflows/build/sleeping-and-retrying/

Effect on cfdoctor: recommend bounded adaptive delays for transient failures and `NonRetryableError` for permanent failures, rather than generic exponential-backoff boilerplate.

### 3. New KV-backed Durable Object namespaces are restricted

**Decision: update configuration guidance, but keep this prompt-only.**

As of July 9, accounts without an existing KV-backed Durable Object namespace cannot create one with `new_classes`; new namespaces must use `new_sqlite_classes`. Existing KV-backed namespaces remain supported, and accounts already using that backend may still create new ones for now.

Sources:

- https://developers.cloudflare.com/changelog/post/2026-07-09-restrict-new-kv-backed-namespaces/
- https://developers.cloudflare.com/durable-objects/reference/durable-objects-migrations/

Effect on cfdoctor:

- Prefer `new_sqlite_classes` for genuinely new namespaces.
- Never tell users to rewrite an applied historical migration.
- A static `new_classes` match is not proof of a defect because account and deployment history are required; track it as `CFDOC-CONFIG-DO-NEW-KV-RESTRICTED` (`skill-prompt-only`).

### 4. Images binding billing changed materially

**Decision: correct Images cost language.**

As of July 1/8, Images binding calls use the same unique-transformation model as URL transformations. The same source-and-parameter combination is counted once per calendar month; repeated calls are not separate Images transformation units, and `.info()` is free. Binding responses are not automatically cached: repeating an uncached transformation still reruns decode/encode and the Worker, so Workers Cache can reduce latency and CPU while introducing its own request/auth/cache-key semantics.

Sources:

- https://developers.cloudflare.com/changelog/post/2026-07-01-binding-unique-transformations/
- https://developers.cloudflare.com/images/pricing/
- https://developers.cloudflare.com/images/optimization/binding/

Effect on cfdoctor: retain unique-variant explosion checks, but remove any implication that every binding call is a separately billed transformation.

### 5. Scheduled Workers KV API route deprecation

**Decision: record as upcoming, not yet active on the crawl date.**

A merged docs commit schedules deprecation of `/accounts/{account_id}/workers/namespaces/*` on July 15, 2026 and end-of-life on October 15, 2026 in favor of `/accounts/{account_id}/storage/kv/namespaces/*`. Because the changelog entry was future-dated relative to this crawl, cfdoctor should not describe it as currently deprecated before publication.

Source patch: https://github.com/cloudflare/cloudflare-docs/commit/227282b7

Potential follow-up: add a narrowly scoped API/IaC check after the deprecation is officially published.

## New evidence candidates

### Accepted into the ledger

1. **`CFDOC-EVD-D1-134-BILL`** — first-hand D1 row-read incident. Two layout queries repeatedly scanned a roughly 765k-row table; the operator reports 127B row reads and a $134 bill before composite indexes, `ANALYZE`, and caching. This is more directly Cloudflare-specific than generic Firebase analogs.
   - https://fullstacksveltekit.com/blog/cloudflare-d1-bill
2. **`CFDOC-EVD-WIRE-DO-EXIT`** — first-hand product-fit report. Wire retained Workers but moved its retrieval data plane because Vectorize was a separate hot-path state copy, DO placement was creation-time, compute was shared, and self-hosting was unavailable. The author explicitly says workloads without those constraints should stay on Durable Objects.
   - https://usewire.io/engineering/why-were-moving-wire-off-cloudflare-durable-objects/
   - https://usewire.io/why-wire/architecture-benchmark/
3. **`CFDOC-EVD-CF-BYOIP-20260220`** — first-party Cloudflare outage. A malformed cleanup query selected all BYOIP prefixes and propagated withdrawals/dependent-binding deletion, supporting staged rollout, blast-radius, rollback, and desired-vs-operational-state checks.
   - https://blog.cloudflare.com/cloudflare-outage-february-20-2026/
4. **`CFDOC-EVD-DO-ALARM-34K`** — retained as **unverified**, discovery-only evidence. A first-hand HN post supplies the recursive alarm code shape and claims extreme SQLite row reads across 60+ preview deployments, but account metrics and invoice are not independently available.
   - https://news.ycombinator.com/item?id=47787042

### Useful supporting candidates not promoted to standalone ledger authority

- `withastro/flue#354`: concrete open-source design discussion showing SSE/long-polling keeps Durable Objects active while hibernatable WebSockets can avoid idle duration. It supports `DO-WEBSOCKET-DURATION`, but it is primarily a design issue rather than an independently measured incident.
  - https://github.com/withastro/flue/issues/354
- `BeechCMS#220`: oversized Queue messages are caught and swallowed, returning success while losing work. This is a useful fixture design for payload-limit/mock-fidelity/error-propagation review, but the issue was newly filed and uncorroborated during this crawl.
  - https://github.com/fdemusso/BeechCMS/issues/220
- HN usage circuit-breaker report: relevant supporting implementation for self-protection and hysteresis, but the ledger already has a spend-controls causal cluster.
  - https://news.ycombinator.com/item?id=47322794

### Rejected/noise

- Generic search-result summaries without a reachable first-hand source.
- Product announcements relabeled as incidents.
- Repository issues that merely propose adopting Cloudflare products.
- Status mirrors and automated issue feeds without a postmortem or project evidence.
- Future-dated docs treated as already-active behavior.

## Resulting repository actions

- Expanded the evidence ledger from 23 to 27 records while retaining exactly 23 runtime checklist scenarios.
- Added 3 critical semantic anchors (Workflows pricing, DO migration restrictions, Images unique-transform billing), bringing the policy to 11 sources.
- Updated runtime cost, reliability, configuration, source-map, and recommendation-provenance guidance.
- Added prompt-only matrix rows for Workflow step economics and the account-history-dependent DO backend restriction rather than introducing noisy regex findings.
