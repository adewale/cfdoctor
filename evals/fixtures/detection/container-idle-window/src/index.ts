import { Container, getContainer } from "@cloudflare/containers";

interface Env {
  TRANSCODER: DurableObjectNamespace<TranscodeContainer>;
}

// No sleepAfter and no onActivityExpired override: the instance stays awake for
// the platform default after the last request, billing standard-4 memory and
// disk the whole time even though the transcode itself is short.
export class TranscodeContainer extends Container {
  defaultPort = 8080;

  override async fetch(request: Request): Promise<Response> {
    return await this.containerFetch(request);
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname !== "/transcode") {
      return new Response("not found", { status: 404 });
    }

    const clipId = url.searchParams.get("clip");
    if (!clipId) {
      return new Response("missing clip", { status: 400 });
    }

    const container = getContainer(env.TRANSCODER, clipId);
    return await container.fetch(request);
  },
};
