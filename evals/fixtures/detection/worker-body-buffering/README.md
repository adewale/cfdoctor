# Fixture: worker-body-buffering

Models the documented Workers memory failure (evidence
`CFDOC-EVD-CF-ISOLATE-MEMORY-MODEL`): the isolate has a fixed 128 MB shared by
every concurrent request, and Cloudflare's own best-practices page says that
buffering an entire body with `await request.arrayBuffer()` or
`await response.text()` "will crash your Worker on large payloads", surfacing
as `Memory limit would be exceeded before EOF` or an `exceededMemory`
invocation outcome.

Two files carry the two shapes: `src/upload.js` reads a whole upload into
memory with no Content-Length guard before writing it to R2, and
`src/proxy.js` buffers an upstream media object before re-serving it. The
scanner should report `CFDOC-PERF-BODY-BUFFERING` for both. It must not report
`CFDOC-PERF-R2-BUFFERING` (nothing reads from R2) or
`CFDOC-PERF-MODULE-SCOPE-SCHEMA-WEIGHT`.

This is intentionally bad code, committed only as a detection eval fixture for
`scripts/cfdoctor_static_scan.py`. Do not copy any of it into a real project.
