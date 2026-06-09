# Fixture: clean-baseline

A deliberately healthy Worker project: recent ISO `compatibility_date`,
observability enabled, a narrowly scoped route, only non-sensitive vars, and a
trivial handler. This fixture is the false-positive guard for the detection
eval: `scripts/cfdoctor_static_scan.py` must report zero findings here, and the
eval fails if any check starts firing on it.
