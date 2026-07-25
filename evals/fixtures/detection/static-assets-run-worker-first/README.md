# static-assets-run-worker-first

Known-bad fixture: a Static Assets Worker sets `assets.run_worker_first: true`.

- `CFDOC-COST-ASSETS-RUN-WORKER-FIRST` — free static-asset requests are routed
  through the billable Worker for every request. Scope `run_worker_first` to
  only the paths that need the Worker, or use negative globs.
