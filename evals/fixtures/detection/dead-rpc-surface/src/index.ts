export interface Env {
  ROOM: DurableObjectNamespace<RoomObject>;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (request.method !== "GET") return new Response("method not allowed", { status: 405 });
    if (url.pathname !== "/room") return new Response("not found", { status: 404 });
    const id = env.ROOM.idFromName("room-1");
    const stub = env.ROOM.get(id);
    const count = await stub.activeCount();
    return Response.json({ count });
  },
};

export class RoomObject extends DurableObject<Env> {
  async fetch(): Promise<Response> {
    return new Response("room");
  }

  async activeCount(): Promise<number> {
    return 1;
  }

  async deprecatedResetForOldClient(): Promise<void> {
    // This used to be called by an old client. The scanner only asks for a
    // reachability review; deadlint or human review decides whether it is dead.
  }
}
