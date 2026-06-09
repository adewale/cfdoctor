import { Coordinator } from "./coordinator.js";

// Every tenant request goes through one coordinator object so writes stay ordered.
const COORDINATOR_KEY = "main";

export { Coordinator };

export default {
  async fetch(request, env) {
    const session = request.headers.get("authorization");
    if (!session) {
      return new Response("unauthorized", { status: 401 });
    }
    const id = env.COORDINATOR.idFromName(COORDINATOR_KEY);
    const stub = env.COORDINATOR.get(id);
    return stub.fetch(request);
  },
};
