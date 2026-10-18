Scope inspected: `builtin-retries.json` and the three supplied Cloudflare documentation snapshots.

Scope not inspected: Workflow analytics/invoices, CPU telemetry, retained-state volume/configuration, and paid-API pricing.

Docs refreshed: Supplied official Cloudflare docs captured October 18, 2026.

No confirmed retry-policy cost finding. The configured retries do not increase the Workflow step meter.

```json
{
  "workflow_starts": 1000000,
  "billed_steps": 5000000,
  "step_overage_usd": 36,
  "retry_extra_step_fee_usd": 0,
  "retry_cpu_and_downstream_cost_guaranteed_zero": false
}
```

Calculation:

- 1,000,000 starts × 5 logical steps = 5,000,000 billed steps.
- Built-in `WorkflowStepConfig.retries` attempts are excluded from step count.
- Overage: 5,000,000 − 500,000 included = 4,500,000 steps.
- Estimated charge: 4,500,000 ÷ 100,000 × $0.80 = **$36 per month**.
- Removing the two retries would leave the same five billed steps per run, so the retry policy adds **$0 in step fees**.

The estimate assumes step billing is active under the supplied October 2026 pricing documentation; invoice evidence would be needed to establish the actual charge.

Remaining costs:

- **Workflow requests:** One million starts are within the Paid plan’s 10-million monthly allowance, producing $0 request overage given the stated zero other account usage.
- **CPU:** Unmeasured. The workload executes 15 million callback attempts—5 steps × 3 attempts × 1 million runs—including 10 million retry attempts. Idle network waits do not consume CPU, but executing retry callbacks can.
- **Downstream services:** Unmeasured. `callPaidAPI` runs 15 million times. Although Workflow subrequests do not add Workflow request charges, the API or any invoked Cloudflare products may have their own charges.
- **Workflow state storage:** Unmeasured. Required inputs include daily peak persisted bytes, Workflow creation date, and retention overrides. New Paid Workflows created on or after September 10, 2026 default to seven-day completed/error retention; older Workflows retain their previous setting.

**Decision:** Changing the retry policy is **not justified by the Workflow step fee alone**, because the step-fee saving would be zero. Any change should instead be based on measured CPU and downstream spend, failure recovery requirements, API rate limits, and idempotency. The existing policy is at least bounded and uses exponential backoff.

Source basis: [Workflow pricing](https://developers.cloudflare.com/workflows/reference/pricing/), [billing-start announcement](https://developers.cloudflare.com/changelog/post/2026-07-07-workflows-billing-updates/), and [retention change](https://developers.cloudflare.com/changelog/post/2026-09-10-paid-retention-default/).
