# Fixture: gap-stream-preload-split

False-negative gap fixture: the lesson page renders a `<video preload="auto">`
player, but the `cloudflarestream.com` host is imported from `src/config.js`,
so a heuristic requiring the Stream hostname and the preload attribute in the
same file missed the paid delivered-minutes risk.

This is intentionally bad code, committed only as a detection eval fixture for
`scripts/cfdoctor_static_scan.py`. Do not copy any of it into a real project.
