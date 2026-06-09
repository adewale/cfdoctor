# Fixture: gap-do-sharding-indirect

False-negative gap fixture: the Worker funnels every request into a single
Durable Object, but the singleton name lives in a constant
(`const COORDINATOR_KEY = "main"`) rather than a string literal inside the
`idFromName(...)` call, which the original heuristic required.

This is intentionally bad code, committed only as a detection eval fixture for
`scripts/cfdoctor_static_scan.py`. Do not copy any of it into a real project.
