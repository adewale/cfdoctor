import { COORDINATOR_KEY } from "./constants";

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.headers.get("authorization") !== env.INTERNAL_TOKEN) return new Response("forbidden", { status: 403 });
    const id = env.COORDINATOR.idFromName(COORDINATOR_KEY);
    return env.COORDINATOR.get(id).fetch(request);
  },
};
