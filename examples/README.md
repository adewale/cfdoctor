# Examples

This directory gives quick copy-paste examples for using Cloudflare Doctor.

## Example 1: local static scan

On a Cloudflare project:

```bash
./scripts/cfdoctor_static_scan.py /path/to/project
```

On this repository, exclude the intentionally bad detection fixtures:

```bash
./scripts/cfdoctor_static_scan.py . --exclude evals/fixtures
```

Expected for this repository at the time of writing:

```text
## Findings (0)

No scanner findings. This does not mean the project is healthy; account/dashboard settings and access patterns still need audit.
```

Each finding carries a stable check ID (see
[`references/check-coverage-matrix.md`](../references/check-coverage-matrix.md)).
Use `--list-checks` for the registry and `--json` for machine-readable leads.

## Example 2: prompt for a Cloudflare Worker repo

```text
Cloudflare Doctor this repo and focus on Cloudflare Workers cost. Check CPU time, subrequests, public Worker-to-Worker fetches, retry loops, cron triggers, preview bindings, logs, and whether expensive routes have cache/rate-limit/kill-switch controls.
```

## Example 3: prompt for Durable Objects

```text
Audit our Durable Objects implementation. Look for global object IDs, WebSocket hibernation gaps, missing close/error cleanup, storage.list in hot paths, unbatched storage writes, alarm recursion, fanout to many DOs, and object-per-idempotency-key designs.
```

## Example 4: prompt for account evidence

```text
Before you make dashboard-level Cloudflare recommendations, list the exact redacted screenshots/API exports/IaC snippets you need and mark everything else not inspected.
```
