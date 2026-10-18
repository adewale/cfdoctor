Scope inspected: User-supplied architecture statement: one Workflow step starts child work for every input row.

Scope not inspected: Implementation, Wrangler configuration, row cardinality, child-work type, deployed concurrency settings, idempotency, retries, metrics, and account plan. No scanner was run because no project files were supplied.

Docs refreshed: [Workflows limits](https://developers.cloudflare.com/workflows/reference/limits/), [Workflows pricing](https://developers.cloudflare.com/workflows/reference/pricing/).

### Severity: high — Unbounded per-row fan-out

- **Category:** reliability / cost footgun
- **Evidence:** User-supplied prompt states that the step starts unbounded child work for every input row.
- **Why it matters:** Work grows linearly with the result set, with no application-level backpressure. Large or unexpectedly growing inputs can overwhelm downstream services and exhaust Workflow creation-rate, running-instance, or queued-instance limits. Creation above the platform rate limit returns HTTP 429. If children are Workflow instances, each is a separate invocation with its own CPU, steps, retained state, and downstream operations; automatic retries can multiply duplicated work unless creation is idempotent.
- **Fix:** Process the input through a persisted cursor in bounded pages. Set explicit limits for rows per page, concurrent children, total children per parent run, tenant/day quota, and deadline. Start the next page only after capacity returns. Give each child a deterministic ID derived from the parent generation and row identity, handle partial creation failures, and use bounded exponential backoff with jitter for 429s. Add a kill switch. Choose limits from downstream capacity and an explicit spend budget—not Cloudflare’s account-wide maximums.
- **Cost / trade-off:** Exposure is approximately `input rows × (child invocation + child steps + CPU + state + downstream units)`, further multiplied by duplicate attempts. Bounding work increases completion latency and requires checkpoint state, but prevents a single oversized input from creating a reliability or billing spike.
- **Verify:** Test an input larger than every configured cap. Assert that no more than the chosen concurrency is active, each controller iteration starts at most one bounded page, restart/retry creates no duplicate side effects, injected 429s back off and resume, and cancellation stops further creation. Record rows discovered, children created/skipped/failed, retries, active/queued counts, and Workflow invocation, step, CPU, storage, and downstream-product usage.
- **Source basis:** Cloudflare documents finite creation, concurrency, and queue limits—and HTTP 429 when creation rate is exceeded—in [Workflows limits](https://developers.cloudflare.com/workflows/reference/limits/). It documents that Workflow instances are billed across invocations, CPU, storage, and steps in [Workflows pricing](https://developers.cloudflare.com/workflows/reference/pricing/).
- **Confidence:** High for the unbounded-fan-out defect; impact magnitude remains unquantified without input volumes and code/configuration.
