# Fixture: do-sql-unbounded-scan

Isolates the rows-read amplification mechanism from the 2026-08 StandardAgents
bill (evidence `CFDOC-EVD-STDAGENTS-DO-LOOP`) without the loop: a usage-ledger
Durable Object whose hot dashboard endpoint re-reads the entire `usage_events`
table with an unbounded `storage.sql.exec` SELECT while writes keep growing the
table. SQLite-backed Durable Object storage bills rows read, so this read path
compounds with table size even though requests and duration stay small.

The scanner should report `DO-SQL-SCAN-HOTPATH` for the unbounded SELECT, must
not flag the bounded WHERE/LIMIT cleanup query in the alarm, and must not
report `DO-STUB-CALL-CYCLE` because there is no second Durable Object.

This is intentionally bad code, committed only as a detection eval fixture for
`scripts/cfdoctor_static_scan.py`. Do not copy any of it into a real project.
