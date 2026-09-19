# Materialized public articles

`safe.example` serves a public article catalogue. Publishing writes the aggregate embedded as `TOTAL_ARTICLES`; requests never recompute it. The release measurement in `query-plan.txt` is from a production-shaped D1 database with 35,000 rows. No account controls or deployed traffic are supplied.
