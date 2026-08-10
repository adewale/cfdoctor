# Fixture: d1-shared-cache-safe

Near-miss precision control for `d1-isolate-cache-rescan` (the kentcdodds.com
PR #890 shape). The same full-table D1 aggregate exists, but the cache
architecture is the corrected one: the aggregate key uses a shared KV-backed
cachified adapter, a hand-rolled L1 `Map` sits *in front of* the shared KV
layer rather than replacing it, and the per-isolate `lruCache` is reserved for
a value that is cheap to recompute. `CFDOC-COST-D1-ISOLATE-CACHE` must stay
quiet here, and the fixture must produce zero findings overall.

Committed only as a detection eval control for
`scripts/cfdoctor_static_scan.py`.
