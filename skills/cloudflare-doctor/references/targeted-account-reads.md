# Targeted account reads for Wrangler gaps

Use this reference only after repository evidence and the Wrangler snapshot leave a concrete hypothesis unresolved. Do not enumerate an account broadly. Every read needs a named hypothesis, the smallest discriminating fields, a reviewed command shape, and explicit approval.

## Common boundary

Before a read, state:

```text
hypothesis:
why repository/Wrangler evidence is insufficient:
resource scope:
read-only command or API method/path:
fields retained:
redactions:
stop condition:
```

Use an existing pinned product CLI when it exposes the field. Otherwise ask the user to export the exact dashboard panel or approve one scoped API GET. Never ask for a token in chat, print authorization headers, follow pagination beyond the named resource without approval, or convert an unavailable field to `false`.

## Smallest reads by hypothesis

| Hypothesis | Smallest discriminating evidence | Do not expand into |
|---|---|---|
| A hostname bypasses Cloudflare | One DNS record by exact name: type, target, `proxied`, TTL; origin firewall/AOP statement if direct-origin reachability matters | Full zone DNS dump |
| A WAF/Cache/Redirect rule changes one route | The named zone ruleset phase entrypoint, then only rules matching the hostname/path under review | Every ruleset/account rule |
| An Access policy leaves one app exposed | The Access application matching the exact hostname/path plus its attached policies | All Zero Trust apps/users/logs |
| An R2 bucket is public | The named bucket's managed-domain/custom-domain status, CORS, and lifecycle rules needed by the hypothesis | Object listing or object bodies |
| A Queue can delete poison messages | The named consumer's retry count/delay, DLQ, batch size/timeout, and concurrency | All queues/messages |
| A preview deployment is public and paid | The named project/environment deployment, routes, bindings, and lifecycle/last-active evidence | Every Pages/Workers project |
| Logging is materially expensive | Product usage for the named Worker/time window, sampling config, retained bytes/events, retention, and invoice line item | Raw logs or request payloads |
| A cost estimate needs entitlement | Plan/contract name and only the relevant product entitlement/line item, with negotiated values redacted when possible | Full invoice/account contract |
| A meter is running away right now | Billable usage for the current cycle (dashboard export or the account billable-usage API), filtered to the suspect product/meter and date range | Full invoice history or unrelated products |
| Billing alerts could not have caught this | Budget alert configuration (thresholds, recipients, enabled state — note the auto-created $10 default) and the notification history for the affected cycle | All account notification settings |
| Durable Objects are reset for memory because of baseline, not data | The namespace's memory usage chart or `durableObjectsPeriodicGroups` quantiles (`memoryUsageBytesP50`/`P99`) over a week with deployment markers, plus the exceeded-memory/reset count per bucket for the same window; flat-at-idle means baseline | Every namespace, per-object dumps, or request logs |
| A Worker is near its memory or startup limits | The Worker's memory usage chart (P50–P999) around the suspect deployment, `exceededMemory` invocation counts, and the `startup_time_ms` / `Total Upload` lines from the last `wrangler deploy` or `versions upload` output | Full analytics exports or raw Logpush |

## API command-shape examples

These are templates for plan review, not authorization. Use the current official API documentation before execution because paths and response shapes change.

```bash
# Exact DNS name only
curl --fail-with-body --silent --show-error \
  --get "https://api.cloudflare.com/client/v4/zones/<ZONE_ID>/dns_records" \
  --data-urlencode "name=<HOSTNAME>" \
  --data-urlencode "per_page=100" \
  --header "Authorization: Bearer $CLOUDFLARE_API_TOKEN"

# One zone ruleset phase entrypoint
curl --fail-with-body --silent --show-error \
  "https://api.cloudflare.com/client/v4/zones/<ZONE_ID>/rulesets/phases/<PHASE>/entrypoint" \
  --header "Authorization: Bearer $CLOUDFLARE_API_TOKEN"

# Durable Objects memory percentiles for one namespace (GraphQL; verify field names against the current schema)
curl --fail-with-body --silent --show-error \
  "https://api.cloudflare.com/client/v4/graphql" \
  --header "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"query":"query($account:String!,$from:Time!,$to:Time!,$ns:String!){viewer{accounts(filter:{accountTag:$account}){durableObjectsPeriodicGroups(limit:1000,filter:{datetime_geq:$from,datetime_leq:$to,namespaceId:$ns}){dimensions{datetimeFifteenMinutes}quantiles{memoryUsageBytesP50 memoryUsageBytesP99}}}}}","variables":{"account":"<ACCOUNT_ID>","from":"<ISO_START>","to":"<ISO_END>","ns":"<NAMESPACE_ID>"}}'

# Current-cycle billable usage for a runaway-meter hypothesis (data updates daily)
curl --fail-with-body --silent --show-error \
  --get "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/billable-usage" \
  --data-urlencode "from=<YYYY-MM-DD>" \
  --data-urlencode "to=<YYYY-MM-DD>" \
  --header "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
```

Do not paste the token or literal authorization header into reports. Store raw output in a private temporary directory, extract only the fields needed to decide the hypothesis, hash the retained artifact, and delete the raw response after review.

For products whose current Wrangler version has an exact `list`/`get`/`info` command, prefer that command after checking `wrangler <product> --help`. Do not install or upgrade Wrangler to gain a command during collection. If the command is absent, stop and offer the exact dashboard export or one API GET instead.

## Official API navigation

- DNS records API: https://developers.cloudflare.com/api/resources/dns/subresources/records/methods/list/
- Rulesets API: https://developers.cloudflare.com/api/resources/rulesets/
- Access applications API: https://developers.cloudflare.com/api/resources/zero_trust/subresources/access/subresources/applications/
- R2 API: https://developers.cloudflare.com/api/resources/r2/
- Queues API: https://developers.cloudflare.com/api/resources/queues/
- GraphQL Analytics API: https://developers.cloudflare.com/analytics/graphql-api/
- Durable Objects memory usage metric and `durableObjectsPeriodicGroups` dataset: https://developers.cloudflare.com/durable-objects/observability/metrics-and-analytics/#memory-usage
- Workers memory usage chart and `exceededMemory` outcome: https://developers.cloudflare.com/workers/observability/metrics-and-analytics/ and https://developers.cloudflare.com/workers/platform/limits/#memory
- Billable usage dashboard/data source: https://developers.cloudflare.com/billing/manage/billable-usage/
- Budget alerts (informational only; no pause/cap): https://developers.cloudflare.com/billing/manage/budget-alerts/

## Reporting

Report the read as **account evidence observed at `<timestamp>`**, not a permanent truth. Name fields that were not returned, pagination that was not followed, and products not inspected. A negative result proves only that the scoped response lacked the field/resource at that observation time.
