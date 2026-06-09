# Fixture: gap-dashboard-queue-consumer

False-negative gap fixture: the code exports a `queue()` consumer handler with
unbounded `message.retry()`, but the consumer binding (and any DLQ/retry
settings) live only in the dashboard — the repo config has no `consumers`
block, so a config-only heuristic sees nothing to flag.

This is intentionally bad code, committed only as a detection eval fixture for
`scripts/cfdoctor_static_scan.py`. Do not copy any of it into a real project.
