# Sharing Cloudflare state with Cloudflare Doctor

Cloudflare Doctor cannot see the user's Cloudflare dashboard by default. Dashboard/account state must come from user-provided evidence or explicitly approved authenticated read-only commands. Never infer dashboard settings from repository files alone.

## Ask for an evidence package

When dashboard/account settings matter, ask the user for the smallest evidence package that would change the diagnosis. Good options:

1. **IaC first**: Terraform/Pulumi/CDK files, state snippets, plans, or `cf-terraforming` output for Cloudflare resources.
2. **Dashboard exports/screenshots**: screenshots or copied config from the exact product pages listed below.
3. **Cloudflare API JSON**: read-only API responses for zones, rulesets, Access apps, R2 bucket settings, etc.
4. **Wrangler read-only output**: project/deployment/binding/migration inventories.
5. **Billing/usage evidence**: plan, usage graphs, top routes/products, and overage line items.
6. **Architecture notes**: expected traffic, hot routes, user actions, data access patterns, which environments are production vs temporary, and whether Cloudflare fronts Vercel/Netlify/Railway/Render/Fly/Heroku/AWS/GCP/Azure/Firebase/Supabase/Fastly origins.

Prefer exact exports over prose. If the user only provides prose, treat it as an architecture statement, not proof of dashboard settings.

## Redaction and safety rules

Tell users to redact:

- API tokens, Global API keys, R2 access keys/secrets, OAuth secrets, JWT/private keys, database URLs/passwords, webhook signing secrets.
- Session cookies, Access JWTs, service tokens, account-scoped credentials.
- Sensitive customer data, object keys, tenant IDs, emails, IPs, logs with payloads, and request bodies unless needed.

Usually safe to share after review/redaction:

- Zone/account IDs if needed for matching resources, but allow users to hash/alias them.
- Resource names, route patterns, binding names, ruleset names, setting values, plan names, usage counts, and screenshots without secrets.
- Secret **names** are useful; secret **values** are not.

Never ask for credentials in chat. For authenticated checks, ask the user to run commands locally or explicitly approve read-only commands in their environment.

## Dashboard evidence checklist

Ask only for relevant sections; do not request everything by default.

### Account / billing

- Plan type, recent Free→Paid changes, spending caps/usage alerts if available.
- Product usage/overage line items: Workers, D1, R2, KV, Durable Objects, Queues, Workers AI, Vectorize, Images, Stream, Browser Run, Logpush/analytics, WAF/rate limiting, Zero Trust seats.
- Top products by spend and usage time window.

### DNS / zone / origin

- DNS records export: type, name, target, TTL, proxied status.
- Third-party/default origin hostnames: `*.vercel.app`, `*.netlify.app`, `*.railway.app`, `*.onrender.com`, `*.fly.dev`, `*.herokuapp.com`, cloud storage endpoints, Firebase/Supabase public URLs, or other direct origin URLs.
- SSL/TLS mode, HSTS, Always Use HTTPS, minimum TLS version.
- Origin protection evidence: origin firewall allowlists, Authenticated Origin Pulls, mTLS/API Shield when relevant, and whether direct/default origin URLs are disabled, blocked, or protected.
- DNSSEC/CAA where applicable.

### Security rules

- WAF managed rules status and overrides.
- Custom rules, skip/bypass rules, rate limiting rules, bot/Turnstile settings.
- Rules matching expensive paths before Workers/D1/R2/AI/browser/media work.
- Security events/analytics for false positives or active abuse.

### Access / Zero Trust

- Access applications, domains/path coverage, include/require/exclude policies.
- Session durations, MFA/device posture requirements, service tokens for machine access.
- Preview/admin/internal apps and whether direct-origin bypass is possible.

### Cache / Rules

- Cache Rules, Page Rules, Transform Rules, Redirect Rules affecting audited hostnames/routes.
- Cache key settings, query/cookie normalization, TTLs, origin Cache-Control behavior.
- Purge strategy: tags, prefix, hostname, everything.
- Cache Analytics: hit ratio, top uncached paths, large dynamic misses.

### Workers / Pages

- Worker routes/custom domains/workers.dev status, deployments, previews, rollbacks/gradual deployments.
- Cron triggers by environment.
- Observability/log settings, tail/logpush/traces, top routes by CPU/subrequests/errors.
- Pages preview deployment settings and project environment variables/bindings.

### Storage and data products

- KV namespaces per environment, TTL/key lifecycle strategy, operation counts.
- D1 databases, migrations, backups/time travel, rows read/written, slow/hot queries.
- R2 buckets, public access/custom domains, CORS, lifecycle rules, multipart cleanup, operation counts.
- Durable Objects namespaces/classes, metrics, hot objects, WebSocket hibernation evidence.
- Queues producers/consumers, retry settings, DLQs, backlog, poison-message evidence.

### AI, media, browser, vector

- Workers AI usage by model/task, limits, retries, caching/idempotency, AI Gateway usage.
- AI Gateway caching, rate limiting, logs/cost analytics.
- Vectorize index dimensions, namespaces, topK/query patterns, stored/queried dimension usage.
- Images variants/flexible variants, transformation URLs, cache hit/miss, source restrictions.
- Stream delivered minutes, player preload/autoplay settings, analytics.
- Browser Run sessions, timeouts, close reasons, retries, browser hours/concurrency.

## Read-only command examples

Only run authenticated commands after explicit user approval. Prefer the user running them and pasting redacted output.

```bash
wrangler --version
wrangler whoami
wrangler deployments list
wrangler secret list
wrangler d1 list
wrangler d1 migrations list <database>
wrangler kv namespace list
wrangler r2 bucket list
wrangler queues list
```

For Cloudflare API checks, prefer scoped read-only API tokens. Ask for JSON exports for the specific resource family rather than broad account dumps.

## How to reflect missing evidence in the audit

Use this format:

```markdown
Scope inspected: repo files, Terraform zone resources, redacted WAF rules screenshot, D1 billing screenshot
Scope not inspected: Access policies, R2 lifecycle/CORS, Cache Rules, Workers AI usage, Browser Run sessions
Questions / evidence needed:
- Provide Cache Rules export or screenshot for `example.com/api/*`; this would determine whether D1 reads are cacheable before the Worker.
- Provide Queue consumer retry/DLQ settings; this would determine whether the retry-storm risk is confirmed.
```

If a recommendation depends on missing dashboard state, label it as **needs verification** rather than a confirmed finding.
