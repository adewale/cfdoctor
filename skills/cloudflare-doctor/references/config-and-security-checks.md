# Configuration and security checks

## Wrangler/project configuration

Check every `wrangler.jsonc` (Cloudflare-recommended for new projects), `wrangler.json`, legacy `wrangler.toml`, and environment block.

- `compatibility_date` exists, is not in the future, and is intentionally maintained. Very old dates can hide behavior changes and missed platform improvements.
- `compatibility_flags` are justified. `nodejs_compat` can be necessary, but it may increase bundle/polyfill surface; confirm the code really needs Node APIs.
- `main`, `assets`, `pages_build_output_dir`, `workers_dev`, `routes`, and custom domains match the intended deployment model.
- `routes` are not broader than intended (`*`, whole-zone catchalls, production domains in preview envs).
- Binding names are stable and environment-specific resources point to the right account/database/bucket/namespace.
- `[env.*]` blocks preserve required bindings, vars, migrations, observability, and routes. Env drift is a common production-only bug.
- `vars` contain only non-secret configuration. Anything named like `SECRET`, `TOKEN`, `KEY`, `PASSWORD`, `PRIVATE`, `CLIENT_SECRET`, or containing credential-shaped values belongs in Cloudflare secrets or another secret manager.
- Durable Object bindings have corresponding `migrations` entries for new/renamed/deleted classes.
- Queue consumers define retry/dead-letter behavior appropriate to the workload and have a poison-message story.
- Cron triggers are not accidentally too frequent or duplicated across environments.
- Preview, workshop, demo, branch, and temporary environments are not left routed to production domains or connected to paid/production services after their intended lifetime.
- Observability/logging settings are intentional and bounded.
- Expensive or failure-amplifying features have kill-switch configuration: disable crons, queue consumers, AI/browser/media jobs, demo routes, or high-fanout workflows without redeploying.

## Secrets and repository hygiene

Flag immediately:
- Cloudflare API tokens, Global API keys, account IDs paired with tokens, R2 access keys, Artifacts repo tokens, database URLs with credentials, JWT/private keys, OAuth client secrets, or webhook signing secrets in source, Wrangler config (`wrangler.jsonc`, `wrangler.json`, or `wrangler.toml`), committed `.env`, tests, docs, or CI logs.
- `vars` used for credentials. Wrangler vars are configuration, not secret storage.
- Production secrets reused in preview/dev environments.
- Publicly documented admin URLs, bypass tokens, or preview URLs with weak auth.

Recommended fix:
- Rotate exposed credentials, move to `wrangler secret put`/dashboard secrets/CI secret store, and add secret scanning/pre-commit checks.

## Worker/API security

Check request handlers and routes:
- Authentication and authorization happen before sensitive data access, expensive work, or side effects.
- Tenant/user IDs from URL/body are verified against authenticated identity.
- CORS is not `Access-Control-Allow-Origin: *` with credentials or sensitive endpoints. Avoid reflecting arbitrary `Origin`; use an allowlist.
- Public mutation endpoints have CSRF/replay/idempotency considerations where browser credentials or webhooks are involved.
- Webhook handlers verify signatures and timestamps before enqueueing/processing.
- OAuth/OIDC flows use redirect URI allowlists, timing-safe secret/token comparisons where applicable, encrypted token storage, refresh-token rotation/expiry handling, and idempotency for callback/webhook side effects.
- Rate limiting, Turnstile, WAF, or bot protections cover abuse-prone endpoints before expensive Worker/storage work.
- Do not trust arbitrary `X-Forwarded-For`/`CF-Connecting-IP` unless the traffic path guarantees Cloudflare is the only ingress.
- Error responses/logs do not leak secrets, tokens, stack traces, SQL, object keys, or tenant data.
- Browser/geolocation/device-fingerprint/IP-derived analytics are disclosed, minimized, consented where required, and not cached/logged into long-lived high-cardinality stores without retention limits.

## Cache/security interaction

- Private or personalized responses use `Cache-Control: private/no-store` or a per-user/tenant cache key with strict auth guarantees.
- Public cached responses vary on the right dimensions (`Accept-Encoding`, locale, device, auth absence) and do not include cookies accidentally.
- Workers Cache API entries are not shared across incompatible request variants.
- HTML/API responses with auth-sensitive data are not cached by broad Cache Rules.
- When Workers Cache (`cache.enabled`) is on, auth/gateway entrypoints set `cache.enabled = false` so a cache hit cannot serve a protected response without running the auth check; only inner, safely cacheable entrypoints are cached. Cloudflare auto-bypasses `Set-Cookie` responses and `Authorization` requests, but that is a backstop, not the authorization boundary.
- Workers Cache tenant/user separation is carried by `ctx.props` (part of the cache key), not by hostname or cookies; multi-tenant callers over service bindings must set distinct `ctx.props` or they share cached responses.

## Dynamic Workers, Artifacts, and sandboxed execution

- Dynamic Workers that run user-submitted or LLM-written code have explicit egress policy, bindings, secrets, custom limits, and per-run audit logs. Prefer deny-by-default egress/bindings and grant only the capability the code needs.
- Code execution inputs are size-limited and validated; outputs/logs are bounded and redacted.
- Dynamic Worker code identity is tracked by code hash/version so repeated identical executions can be deduped and investigated.
- Agents/MCP/code-mode/browser/sandbox tools require explicit tool allowlists, approval boundaries for side effects, tenant auth, cancellation, and traceability.
- Artifacts repos and repo-scoped tokens are separated by environment/tenant/app where appropriate; tokens are not embedded in client firmware or app bundles unless scoped/rotatable and expected.
- App/firmware update flows backed by Cloudflare Artifacts or Workers should verify signatures, support rollback/A-B deploy, and avoid one shared mutable "latest" object with no provenance.

## R2/public assets

- Public buckets contain only intentionally public objects.
- Private objects are served through Workers with auth, signed URLs, or short-lived tokens.
- Uploads validate content type/size, virus/malware requirements if applicable, object key traversal, tenant prefix, and overwrite/idempotency behavior.
- Download paths support streaming/range where needed and avoid buffering entire objects in Worker memory.

## Account/zone dashboard checks

These usually require Terraform/export/screenshots/API output:

- DNS records: proxy status (orange-cloud) intentional; no accidental direct-origin bypass for protected services.
- SSL/TLS: mode should normally be Full (strict) for production origins; avoid Flexible unless there is a deliberate constrained reason.
- Origin exposure: origin IP/hostnames are not publicly reachable around Cloudflare when WAF/Access is expected to protect them.
- WAF/rate limiting/bot rules cover expensive and sensitive paths.
- Cache Rules/Page Rules/Transform Rules do not conflict with Worker routes or leak private content.
- Access/Zero Trust policies protect admin/internal apps, previews, and dashboards where appropriate.
- Logpush destinations, retention, and sampled analytics match privacy and cost expectations.

## CI/CD and deployment safety

- Deployment requires explicit environment selection; production is not the default for every branch.
- Preview/staging/resources for demos and workshops are separate from production resources unless sharing is intentional, safe, and cost-bounded.
- D1 migrations are applied in a controlled order with rollback/backup story.
- Worker/Pages deploys include generated types (`wrangler types`) or equivalent validation for bindings where practical.
- Tests exercise local Worker runtime behavior (`wrangler dev`, Miniflare/Vitest integration) rather than only Node mocks for platform APIs.
- Load/chaos tests or scripted drills prove circuit breakers, kill switches, DLQs, and idempotency caches work before production incidents.
