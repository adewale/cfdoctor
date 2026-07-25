// Minimal Worker fronting Static Assets. With assets.run_worker_first = true,
// every request runs this Worker (billed) instead of being served as a free
// static asset.
export default {
  async fetch(request, env) {
    return env.ASSETS.fetch(request);
  },
};
