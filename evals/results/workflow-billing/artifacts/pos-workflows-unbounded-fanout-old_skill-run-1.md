Scope inspected: User-supplied architecture statement: one Cloudflare Workflows step starts child work for every input row without a bound.

Scope not inspected: Implementation, input-size limits, child IDs, retries, downstream capacity, Wrangler configuration, deployment/account metrics, and billing plan. No static scan was possible because no project files were supplied.

Docs refreshed: [Trigger Workflows](https://developers.cloudflare.com/workflows/build/trigger-workflows/), [Workflows limits](https://developers.cloudflare.com/workflows/reference/limits/).

### Severity: high — Unbounded per-row Workflow fan-out

- **Category:** reliability / cost footgun
- **Evidence:** User-supplied architecture statement. The fan-out count equals the unrestricted input row count.
- **Why it matters:** Child Workflows run independently after creation, so the parent supplies no natural backpressure. A large input can overwhelm the downstream dependency, exhaust concurrent or queued-instance capacity, and exceed Workflow creation-rate limits, which produces HTTP `429` errors. A partially successful launch step may then retry; without deterministic child IDs, that can duplicate already-started work. Requests, compute, steps, persisted state, and downstream operations all grow with row count.
- **Fix:** Enforce hard per-run and per-tenant row limits before launching anything. Process input in fixed-size pages with a small, explicit concurrency limit and durable checkpoints. Give every child a deterministic ID derived from the parent instance and stable row identity, treating an existing ID as already admitted. Configure bounded retry/backoff for launch failures. If children must remain independent, add an admission mechanism that limits active children and releases capacity only when they reach a terminal state; merely batching creation calls does not bound total fan-out.
- **Cost / trade-off:** Throughput may decrease and backlog latency may increase, but peak load and runaway-cost exposure become predictable. Total work remains proportional to valid rows unless work is consolidated; the remediation primarily bounds simultaneous work and duplicate execution.
- **Verify:** Test with an input larger than the configured cap and confirm it is rejected or paginated. Instrument rows received, children requested/created, duplicates, retries, `429`s, active children, and terminal outcomes. Inject a failure after partial creation and verify retries produce no additional child instances. Confirm observed concurrency never exceeds the chosen budget.
- **Source basis:** Cloudflare documents that a child continues independently once created and that failed child creation causes the parent step to retry: [Trigger Workflows](https://developers.cloudflare.com/workflows/build/trigger-workflows/). Current creation-rate, concurrency, queued-instance, and retry limits are documented in [Workflows limits](https://developers.cloudflare.com/workflows/reference/limits/).
- **Confidence:** High that the unbounded fan-out is unsafe; medium on its present blast radius because row volumes and deployed controls were not supplied.
