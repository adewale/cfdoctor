import { lessonManifest } from "./config.js";

function lessonPage(videoId) {
  return `<!doctype html>
<html>
  <body>
    <h1>Lesson</h1>
    <video controls preload="auto" src="${lessonManifest(videoId)}"></video>
  </body>
</html>`;
}

export default {
  async fetch(request) {
    const videoId = new URL(request.url).pathname.split("/").pop();
    return new Response(lessonPage(videoId), {
      headers: { "content-type": "text/html; charset=utf-8" },
    });
  },
};
