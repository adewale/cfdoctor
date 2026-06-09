export default {
  async fetch(request) {
    const url = new URL(request.url);
    // Callers pick any width/dpr/format they want via query params.
    const width = Number(url.searchParams.get("w")) || 800;
    const dpr = Number(url.searchParams.get("dpr")) || 1;
    const format = url.searchParams.get("fmt") || "auto";
    const origin = `https://assets.photoview.invalid${url.pathname}`;
    return fetch(origin, {
      cf: { image: { width, dpr, format, fit: "scale-down" } },
    });
  },
};
