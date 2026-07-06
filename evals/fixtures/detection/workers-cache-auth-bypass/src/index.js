// Gateway Worker that authenticates every request before returning
// tenant-scoped data. Workers Cache is enabled on this default entrypoint
// (see wrangler.jsonc), which is the footgun: on a cache HIT the Worker does
// not run, so the auth check below is skipped and a cached tenant response
// can be served to a different caller. The fix is to disable caching on this
// gateway entrypoint (exports.default.cache.enabled = false) and cache only
// an inner entrypoint whose responses are safe to share, carrying the tenant
// in ctx.props so cached entries are not shared across tenants.
export default {
  async fetch(request, env) {
    const token = request.headers.get("Authorization");
    const tenant = await authenticate(token, env);
    if (!tenant) {
      return new Response("Unauthorized", { status: 401 });
    }

    const body = JSON.stringify({ tenant, data: await loadDashboard(tenant, env) });
    return new Response(body, {
      headers: {
        "Content-Type": "application/json",
        // Cached in front of the Worker, so a hit is returned without the
        // authenticate() call above ever running for the next caller.
        "Cache-Control": "public, max-age=300",
      },
    });
  },
};

async function authenticate(token, env) {
  if (!token) return null;
  return env.SESSIONS.get(token);
}

async function loadDashboard(tenant, env) {
  return env.SESSIONS.get(`dashboard:${tenant}`);
}
