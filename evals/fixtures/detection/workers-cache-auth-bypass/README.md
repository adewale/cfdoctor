# workers-cache-auth-bypass

Models the cost and security footguns introduced by enabling **Workers Cache**
(`cache.enabled` in Wrangler) on a Worker whose default entrypoint performs
authentication.

Grounded in the Workers Cache launch:
- Blog: https://blog.cloudflare.com/workers-cache/ (2026-07-06)
- Docs: https://developers.cloudflare.com/workers/cache/ and
  https://developers.cloudflare.com/workers/cache/limitations/

## The footguns

- **Auth bypass.** On a cache HIT the Worker does not run, so the `authenticate()`
  check in `src/index.js` is skipped. A cached tenant-scoped response can be
  served to another caller. The fix is to disable caching on the gateway/default
  entrypoint (`exports.default.cache.enabled = false`) and cache only inner
  entrypoints whose responses are safe to share, carrying the tenant in
  `ctx.props` so cached entries are not shared across tenants.
- **Billing surface change.** A cache hit still bills a request at the standard
  Workers rate (only CPU is saved), and enabling caching bills traffic that is
  normally free — static-asset requests and worker-to-worker invocations through
  service bindings or `ctx.exports`.

## Expected detection

`CFDOC-COST-WORKERS-CACHE-BILLING` — surfaced from the Wrangler `cache.enabled`
setting as a lead to verify the billing surface and auth-entrypoint exclusion.
