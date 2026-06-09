import { ChatRoom } from "./chat_room.js";
import { PresenceTracker } from "./presence_tracker.js";

export { ChatRoom, PresenceTracker };

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const room = url.searchParams.get("room") ?? "lobby";
    if (url.pathname === "/ws") {
      const id = env.CHAT_ROOM.idFromName(room);
      return env.CHAT_ROOM.get(id).fetch(request);
    }
    if (url.pathname === "/presence") {
      const id = env.PRESENCE.idFromName(room);
      return env.PRESENCE.get(id).fetch(request);
    }
    return new Response("not found", { status: 404 });
  },
};
