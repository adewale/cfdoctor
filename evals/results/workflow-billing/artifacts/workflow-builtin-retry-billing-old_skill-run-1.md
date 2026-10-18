The step-only monthly overage is **$36.00**. Built-in retries add **$0** to the Workflow step fee because Cloudflare explicitly excludes retries from step count. Therefore, changing the retry policy is **not justified by the step fee alone**.

Scope inspected: supplied usage/code and the three supplied official Cloudflare documentation captures.
Scope not inspected: invoice/dashboard usage, CPU telemetry, paid-API pricing, actual stored-state volume, and configured/effective retention.
Docs refreshed: supplied official captures dated October 18, 2026; no independent fetch was needed.

### Calculation

- Workflow starts: 1,000,000/month.
- Forward steps: 5/start.
- Billed steps: `1,000,000 × 5 = 5,000,000`.
- Included steps: 500,000/month.
- Overage: `4,500,000 ÷ 100,000 × $0.80 = $36.00`.
- Each step reaches three attempts, producing 15,000,000 attempt executions, but retries are excluded from the step meter.

```json
{
  "workflow_starts": 1000000,
  "billed_steps": 5000000,
  "step_overage_usd": 36.0,
  "retry_extra_step_fee_usd": 0.0,
  "retry_cpu_and_downstream_cost_guaranteed_zero": false
}
```

### Severity: medium — Retries amplify costs outside the step meter

- **Category:** cost footgun
- **Evidence:** The code performs five `step.do` operations per run, each reaching three attempts ([builtin-retries.json](</private/var/folders/58/zrc_1j8n0f74krswfhmrtkrw0000gn/T/codex-ws-2s5j9pwt/inputs/builtin-retries.json:4>)). Cloudflare excludes retries from step count but separately meters CPU, invocations, storage, and steps ([workflow-pricing.md](</private/var/folders/58/zrc_1j8n0f74krswfhmrtkrw0000gn/T/codex-ws-2s5j9pwt/inputs/workflow-pricing.md:23>)).
- **Why it matters:** The retries imply 15 million `callPaidAPI` invocations—10 million more than a one-attempt baseline. Their external charges are unknown. Active CPU across those attempts is also unmeasured; waiting for the API does not consume CPU, but execution before and after waiting can.
- **Fix:** Do not reduce retries merely to save Workflow step fees. First measure per-attempt CPU and downstream API charges. Then tune retries according to failure type, idempotency, reliability needs, and total cost.
- **Cost / trade-off:** With zero other account usage, one million Workflow invocations remain inside the 10-million request allowance. CPU has a shared 30-million-ms allowance; 15 million attempts would consume it at an average of 2 ms per attempt, before other Workflow CPU. Storage is also unknown: the supplied pricing page says 30-day Paid retention, while the supplied changelog says new Workflows created on or after September 10, 2026 default to seven days; creation date and overrides were not supplied.
- **Verify:** Obtain Workflow CPU analytics, vendor billing per API call, stored GB-months, Workflow creation date, and configured success/error retention. Confirm the five-million step count through `stepCount` analytics.
- **Source basis:** [Cloudflare Workflows pricing](https://developers.cloudflare.com/workflows/reference/pricing/), [billing-start changelog](https://developers.cloudflare.com/changelog/post/2026-07-07-workflows-billing-updates/), and [retention changelog](https://developers.cloudflare.com/changelog/post/2026-09-10-paid-retention-default/).
- **Confidence:** High for the step calculation and zero retry step fee; low for total cost because CPU, storage, and downstream pricing are unmeasured.
