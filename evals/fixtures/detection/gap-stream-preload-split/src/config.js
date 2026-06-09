// Delivery hosts for course media.
export const STREAM_BASE = "https://customer-f33zs165nr7gyfy4.cloudflarestream.com";

export function lessonManifest(videoId) {
  return `${STREAM_BASE}/${videoId}/manifest/video.m3u8`;
}
