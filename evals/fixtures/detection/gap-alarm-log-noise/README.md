# Fixture: gap-alarm-log-noise

False-negative gap fixture: the alarm handler always calls `setAlarm()` with no
idle check, max attempts, or kill switch — but an unrelated `if (this.verbose)`
logging guard after the reschedule made the original heuristic assume the
reschedule was conditional.

This is intentionally bad code, committed only as a detection eval fixture for
`scripts/cfdoctor_static_scan.py`. Do not copy any of it into a real project.
