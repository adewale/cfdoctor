# Fixture: d1-indexed-layout-cached

Remediated twin of `d1-unindexed-hot-queries`, mirroring the fixes that cut the
whatmedicaidpays.com D1 bill by ~95%: composite indexes matching the hot query
predicates, a reminder to run `ANALYZE`/`PRAGMA optimize` after batch index
changes so the planner has `sqlite_stat1` statistics, and KV cache-aside for
layout-level navigation data under a versioned key with explicit invalidation.
War story: https://fullstacksveltekit.com/blog/cloudflare-d1-bill

False-positive guard: the scanner must emit zero findings here — in particular
neither `CFDOC-COST-D1-NO-INDEXES` nor `CFDOC-COST-D1-LAYOUT-HOTPATH`.
