# Wrangler-first deployed-state snapshots

Date: 2026-07-11

## Decision

Use Wrangler's existing authenticated read commands before designing a custom account collector or universal facts schema. Wrangler already owns authentication profiles, current Cloudflare API compatibility, and product-specific normalization.

The repository wrapper is `scripts/capture_wrangler_snapshot.py`. It does not install Wrangler. It defaults to metadata-only collection, prints the static command plan and the runtime active-version command shape, requires explicit approval, runs an allowlist of read commands, writes a private local snapshot, and records command/file hashes. Source/config download requires the separate `--include-source-config` opt-in. The wrapper never evaluates findings or calls a mutation command.

## Worker snapshot

The wrapper uses:

```bash
wrangler deployments status --name <WORKER> --json
wrangler deployments list --name <WORKER> --json
wrangler versions list --name <WORKER> --json
wrangler versions view <ACTIVE_VERSION_ID> --name <WORKER> --json
wrangler secret list --name <WORKER> --format json
# Only with --include-source-config:
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
# Only with --include-source-config:
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
- forwards only an allowlist of Wrangler/Cloudflare authentication, home/config, locale, certificate, proxy, and temporary-directory environment variables; unrelated cloud/CI credentials and Node injection options are not forwarded;
- records no environment variables, credentials, cookies, or secret values itself;
- disables subprocess stdin so missing authentication fails instead of prompting;
- stores stderr only inside the private snapshot;
- rejects non-empty output directories, removes downloaded symlinks, and marks the snapshot partial;
- defaults to metadata-only collection and requires `--include-source-config` before downloading Worker source/config or Pages config; `--metadata-only` remains an explicit spelling of the default.

Authenticated reads still require the user's explicit approval under the skill's command policy. The user must review/redact the snapshot before sharing it with a model or committing any derived fixture.

## What this establishes

A Worker snapshot can give three useful state layers without inventing a new abstraction:

1. **Repository intent** — the checked-in Wrangler configuration and source.
2. **Optional downloaded dashboard approximation** — `init --from-dash`, only after explicit source/config opt-in.
3. **Actually active versions** — deployment status plus version-specific runtime metadata.

Confirm the concrete deployment name first: repositories can contain multiple Wrangler configs and `env.*` blocks with distinct deployed names. Service Bindings can also point at separately deployed Workers; do not recurse automatically. Treat each referenced Worker as a separate scope item and plan another approved snapshot only when the dependency matters.

For Pages, compare checked-in intent, experimental `pages download config` output, and the deployment list. Diff the relevant layers rather than assuming any one is complete. Downloaded config is an approximation, and an active Worker deployment can contain multiple versions.

## Known gaps

Wrangler does not provide one universal download for DNS, zone settings, WAF/rulesets, Access, Cache Rules, runtime analytics, billing, Queue consumer details, or every product's effective state. Fill those gaps only after a concrete audit hypothesis remains unresolved:

- prefer a product-specific Wrangler `list`/`get` command when available;
- otherwise request one narrowly scoped read-only API response;
- keep raw outputs private and record the Wrangler/API version and observation time;
- never treat an unavailable field as `false`.

The private mode-bit guarantees are tested on POSIX systems. Windows users must verify the snapshot directory's ACLs before capture; `chmod`-style assertions do not establish Windows confidentiality.

The current Worker direct downloader rejects Workers with Assets. A 2026-07-11 review of all accessible `adewale/*` default branches found Assets in 13 of 20 public deployable-project configs (and 16 of 24 when private projects were included), which reinforced metadata-only as the safe and broadly compatible default. `init --from-dash` does not continuously synchronize dashboard changes, so each audit needs a fresh temporary snapshot. Plain vars may be present; secret values should not be, but all output still requires review.

## Live validation

On 2026-07-11, after explicit approval, the wrapper was run against existing non-production/public example projects using the exact Wrangler versions resolved by their lockfiles:

- `tasche/readability-worker` with Wrangler 4.71.0 exercised the complete Worker path, including deployment/version reads and direct config/source download.
- `atlas` with Wrangler 4.94.0 exercised the complete Pages path, including deployment listing and experimental config download.
- `keyboardia-staging` with Wrangler 4.53.0 exercised the metadata-only Worker path for a Worker with Assets.

Every planned command returned zero and every manifest reported a complete snapshot. A Worker snapshot now requires a valid non-empty active-version list and one successful version-view capture per discovered active version; absent version data cannot be reported as complete. Raw snapshots stayed in a mode-`0700` temporary directory and were deleted after shape-only review. No credential, secret value, account dump, downloaded source, route, deployment/version identifier, or cache file was retained.

The review found two details now represented by sanitized fixtures and tests: Pages deployment JSON uses capitalized display keys (`Id`, `Environment`, `Branch`, `Source`, `Deployment`, `Status`, and `Build`), while Worker version JSON includes top-level `number`, `annotations`, and `resources` in addition to `id` and `metadata`. Wrangler also writes `.wrangler/cache` account metadata beneath the command working directory; the wrapper keeps and hashes those files inside the private snapshot, so the whole directory remains sensitive even when source download is disabled.

No broader collector should be built until this path proves insufficient for a concrete diagnosis.
