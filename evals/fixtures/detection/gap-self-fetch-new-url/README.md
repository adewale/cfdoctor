# Fixture: gap-self-fetch-new-url

False-negative gap fixture: the Worker sits on `example.com/*` and fetches
`new URL("/api/related", request.url)` — same-zone self-fetch through a
constructed URL rather than `fetch(request.url)` / `fetch(request.clone())`,
which is all the original heuristic matched.

This is intentionally bad code, committed only as a detection eval fixture for
`scripts/cfdoctor_static_scan.py`. Do not copy any of it into a real project.
