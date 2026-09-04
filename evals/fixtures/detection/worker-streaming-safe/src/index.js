import { handleUpload } from "./upload.js";
import { handleProxy } from "./proxy.js";
import { handleWebhook } from "./webhook.js";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/upload" && request.method === "PUT") return handleUpload(request, env);
    if (url.pathname === "/webhooks/media" && request.method === "POST") return handleWebhook(request, env);
    if (url.pathname.startsWith("/media/")) return handleProxy(request, env);
    return new Response("not found", { status: 404 });
  },
};
