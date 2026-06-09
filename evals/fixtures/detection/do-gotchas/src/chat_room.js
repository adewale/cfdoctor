import { DurableObject } from "cloudflare:workers";

export class ChatRoom extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sockets = new Set();
  }

  async fetch(request) {
    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);
    // In-memory accept keeps this object pinned while the socket is open.
    server.accept();
    this.sockets.add(server);
    server.addEventListener("message", (event) => {
      for (const socket of this.sockets) {
        socket.send(event.data);
      }
    });
    server.addEventListener("close", () => {
      this.sockets.delete(server);
    });
    return new Response(null, { status: 101, webSocket: client });
  }
}
