# Fixture: do-stub-call-cycle

Models the 2026-08 StandardAgents runaway-loop bill (evidence
`CFDOC-EVD-STDAGENTS-DO-LOOP`): two Durable Objects — a session coordinator and
a task runner — call each other's stubs through detached `waitUntil` work with
no hop budget, idempotency key, or kill switch, while every hop re-reads the
whole `events` table with an unbounded `storage.sql.exec` SELECT. In the real
incident the loop ran for roughly three weeks and SQLite storage rows read were
98.5% of an $8,846.78 invoice, while compute requests and duration stayed under
$50.

The scanner should report `DO-STUB-CALL-CYCLE` with the class cycle path and
`DO-SQL-SCAN-HOTPATH` for the unbounded SELECT.

This is intentionally bad code, committed only as a detection eval fixture for
`scripts/cfdoctor_static_scan.py`. Do not copy any of it into a real project.
