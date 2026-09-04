# Fixture: do-module-scope-schema-weight

Models the 2026-08 Polylane incident (evidence `CFDOC-EVD-POLYLANE-DO-MEMORY`):
one Durable Object per agent thread, all instances of one class, whose
isolate idled above the 128 MB limit and was reset about 300 times a day. The
weight was not request data but module-scope baseline: every tool declared its
input schema as a zod tree at module load, package barrels re-exported those
schema modules with `export *`, the packages had no `sideEffects` field, and
the Durable Object loaded the registry with a dynamic import of the package
root, which marks every export as used.

The scanner should report `CFDOC-PERF-MODULE-SCOPE-SCHEMA-WEIGHT` (26
module-scope schema builders with Durable Object bindings present, above the
25-builder lead threshold) and name the three tree-shaking amplifiers. It must
not report `CFDOC-PERF-BODY-BUFFERING`; nothing here buffers a body.

This is intentionally bad code, committed only as a detection eval fixture for
`scripts/cfdoctor_static_scan.py`. Do not copy any of it into a real project.
