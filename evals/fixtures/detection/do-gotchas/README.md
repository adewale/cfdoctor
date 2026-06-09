# Fixture: do-gotchas

Models three Durable Object gotchas from the coey.dev "Durable Objects Gotchas"
quiz: `storage.list()` runs on every presence heartbeat, the alarm handler
unconditionally reschedules itself forever (recurring wake-ups while idle), and
the chat room accepts WebSockets with `server.accept()` instead of the
hibernation API, so idle sockets keep billing wall-clock duration.

This is intentionally bad code, committed only as a detection eval fixture for
`scripts/cfdoctor_static_scan.py`. Do not copy any of it into a real project.
