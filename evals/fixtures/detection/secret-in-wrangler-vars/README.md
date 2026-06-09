# Fixture: secret-in-wrangler-vars

Models the classic committed-credentials incident: credential-named values pasted
into Wrangler `vars` to unblock a deploy, and a `.env` file with a database
connection string (inline password) checked into the repo.

Every value in this fixture is a fake placeholder shaped like a credential. It is
intentionally bad configuration, committed only as a detection eval fixture for
`scripts/cfdoctor_static_scan.py`. Do not copy any of it into a real project.
