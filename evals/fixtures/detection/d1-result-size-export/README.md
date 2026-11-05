# Fixture: d1-result-size-export

Models the failure mode behind emdash-cms/emdash#4610 (evidence
`CFDOC-EVD-EMDASH-D1-SNAPSHOT`) under the D1 maximum query result size
announced in the 2026-10-30 changelog (evidence
`CFDOC-EVD-CF-D1-RESULT-LIMIT`): an authenticated admin backup export loops
over content tables and reads each one with a single `SELECT * FROM ${table}`.
That works while tables are small and then fails with `D1 query result
exceeded the maximum response size limit of 50 MB` once revision history
grows. A second admin route lists every revision with no LIMIT.

The scanner should report `CFDOC-REL-D1-RESULT-SIZE` at high severity (the
file is backup/export-shaped) with the interpolated table query as evidence,
plus the existing `CFDOC-PERF-D1-SELECT-STAR` projection lead.

This is intentionally bad code, committed only as a detection eval fixture for
`scripts/cfdoctor_static_scan.py`. Do not copy any of it into a real project.
