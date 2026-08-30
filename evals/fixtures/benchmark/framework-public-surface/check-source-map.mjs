import { readFile } from "node:fs/promises";

const sourceFiles = [
  "src/app.html",
  "src/routes/+layout.server.js",
  "src/routes/+layout.svelte",
  "src/routes/+page.svelte",
  "src/routes/about/+page.svelte",
  "src/routes/categories/+page.server.js",
  "src/routes/categories/+page.svelte",
  "src/routes/product/[slug]/+page.server.js",
  "src/routes/product/[slug]/+page.svelte",
  "src/routes/sitemap.xml/+server.js",
];

const sections = await Promise.all(sourceFiles.map(async (path) => {
  const contents = await readFile(new URL(path, import.meta.url), "utf8");
  return `===== FILE: ${path} =====\n${contents.trimEnd()}`;
}));
const expected = `${sections.join("\n\n")}\n`;
const actual = await readFile(new URL("source-map.txt", import.meta.url), "utf8");

if (actual !== expected) {
  throw new Error("source-map.txt does not match the path-preserving fixture sources");
}

console.log(`source-map.txt matches ${sourceFiles.length} fixture sources`);
