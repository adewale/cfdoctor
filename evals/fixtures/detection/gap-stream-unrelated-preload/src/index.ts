export default {
  fetch(): Response {
    return new Response('<video preload="auto" src="/local-training.mp4"></video>', {
      headers: { "content-type": "text/html" },
    });
  },
};
