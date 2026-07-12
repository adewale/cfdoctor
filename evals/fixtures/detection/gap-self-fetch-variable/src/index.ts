export default {
  async fetch(request: Request): Promise<Response> {
    const internalTarget = new URL("/internal/retry", request.url);
    const retryTarget = internalTarget;
    return fetch(retryTarget);
  },
};
