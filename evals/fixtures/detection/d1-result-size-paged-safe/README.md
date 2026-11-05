# Fixture: d1-result-size-paged-safe

False-positive guard for `CFDOC-REL-D1-RESULT-SIZE` (evidence
`CFDOC-EVD-CF-D1-RESULT-LIMIT`, `CFDOC-EVD-EMDASH-D1-SNAPSHOT`): the
`d1-result-size-export` backup export rewritten the way emdash-cms/emdash#4610
fixed it. Each table is read in `WHERE rowid > ? ORDER BY rowid LIMIT ?`
pages with an explicit column list, a page that still hits D1's result-size
error is retried at half size up to a fixed attempt cap, and the stats route
uses a single-row `COUNT(*)` with `.first()`. The scanner must emit zero
findings here.
