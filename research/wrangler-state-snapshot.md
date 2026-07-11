# Wrangler-first deployed-state snapshots

Date: 2026-07-11

## Decision

Use Wrangler's existing authenticated read commands before designing a custom account collector or universal facts schema. Wrangler already owns authentication profiles, current Cloudflare API compatibility, and product-specific normalization.

The repository wrapper is `scripts/capture_wrangler_snapshot.py`. It does not install Wrangler. It prints an exact plan, requires explicit approval, runs an allowlist of read commands, writes a private local snapshot, and records command/file hashes. It never evaluates findings or calls a mutation command.

## Worker snapshot

The wrapper uses:

```bash
wrangler deployments status --name <WORKER> --json
wrangler deployments list --name <WORKER> --json
wrangler versions list --name <WORKER> --json
wrangler versions view <ACTIVE_VERSION_ID> --name <WORKER> --json
wrangler secret list --name <WORKER> --format json
wrangler init --from-dash <WORKER> --no-delegate-c3
```

`deployments status` identifies every version currently receiving traffic, including gradual-deployment percentages. `versions view` supplies version-specific bindings, compatibility date/flags, CPU limits, usage model, handlers, and deployment metadata. `secret list` supplies names/types, not values.

`init --from-dash` is the documented Worker-cloning capability. The current Wrangler implementation's direct downloader reconstructs an approximate `wrangler.jsonc` from bindings, routes, custom domains, workers.dev state, service metadata, cron triggers, compatibility settings, migrations, tail consumers, observability, limits, and placement, and downloads deployed source modules. The wrapper uses Wrangler's current hidden `--no-delegate-c3` switch to avoid invoking the package scaffolder; this is deliberately version-coupled and fails rather than silently falling back if Wrangler removes it.

Official command documentation:

- https://developers.cloudflare.com/workers/wrangler/commands/workers/#init
- https://developers.cloudflare.com/workers/wrangler/commands/workers/#deployments-status
- https://developers.cloudflare.com/workers/wrangler/commands/workers/#versions-view
- https://developers.cloudflare.com/workers/wrangler/commands/workers/#secret-list

## Pages snapshot

The wrapper uses:

```bash
wrangler pages deployment list --project-name <PROJECT> --json
wrangler pages secret list --project-name <PROJECT>
wrangler pages download config <PROJECT> --force
```

`pages download config` is currently experimental but directly downloads the Pages project's Wrangler configuration.

Official documentation: https://developers.cloudflare.com/workers/wrangler/commands/pages/#pages-download-config

## Safety boundary

Snapshots are sensitive. They can contain deployed source, plain vars, binding/resource names, routes, domains, account metadata, and secret names.

The wrapper therefore:

- requires `--plan` review followed by `--approve-authenticated-read`;
- requires an existing pinned Wrangler executable and never invokes `npx` or a package installer;
- defaults to refusing output inside any Git worktree;
- creates the snapshot directory as `0700` and files as `0600`;
- records no environment variables, credentials, cookies, or secret values itself;
- stores stderr only inside the private snapshot;
- rejects non-empty output directories and symlinks in the resulting snapshot;
- supports `--metadata-only` to avoid downloading Worker source or Pages config.

Authenticated reads still require the user's explicit approval under the skill's command policy. The user must review/redact the snapshot before sharing it with a model or committing any derived fixture.

## What this establishes

A Worker snapshot gives three useful state layers without inventing a new abstraction:

1. **Repository intent** — the checked-in Wrangler configuration and source.
2. **Downloaded dashboard approximation** — `init --from-dash` or Pages `download config`.
3. **Actually active versions** — deployment status plus version-specific runtime metadata.

Diff these layers rather than assuming any one is complete. A downloaded config is an approximation, and the active deployment can contain multiple versions.

## Known gaps

Wrangler does not provide one universal download for DNS, zone settings, WAF/rulesets, Access, Cache Rules, runtime analytics, billing, Queue consumer details, or every product's effective state. Fill those gaps only after a concrete audit hypothesis remains unresolved:

- prefer a product-specific Wrangler `list`/`get` command when available;
- otherwise request one narrowly scoped read-only API response;
- keep raw outputs private and record the Wrangler/API version and observation time;
- never treat an unavailable field as `false`.

The current Worker direct downloader rejects Workers with Assets. `init --from-dash` does not continuously synchronize dashboard changes, so each audit needs a fresh temporary snapshot. Plain vars may be present; secret values should not be, but all output still requires review.

## Next validation step

Run the wrapper against an explicitly approved disposable Cloudflare test account using the project's pinned Wrangler version. Review the exact command plan first. Keep raw output outside the repository, then commit only minimal redacted fixtures needed to lock observed Wrangler output shapes. No broader collector should be built until this path proves insufficient for a real diagnosis.
