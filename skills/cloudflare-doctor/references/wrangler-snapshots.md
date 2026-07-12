# Wrangler deployed-state snapshots

Use this reference only when the user supplies a Wrangler snapshot or asks to collect effective Worker/Pages deployment state. This is authenticated account evidence, not a routine repo audit step.

## Existing snapshot evidence

If the user already supplied artifacts, inspect them without repeating authenticated reads.

For Workers, reconcile three layers:

1. checked-in repository intent;
2. the optional `init --from-dash` dashboard approximation; and
3. `deployments status` plus `versions view` metadata for **every** version receiving traffic.

A status response with two weighted version IDs is incomplete when only one version view is supplied. Request only the missing version metadata. Do not assume the newest or highest-numbered version is the sole active version.

For Pages, compare checked-in intent, optional `pages download config`, and the Pages deployment list. A Pages deployment row does not prove Worker-style active versions, bindings, compatibility settings, or runtime limits.

Treat the entire snapshot as sensitive. Even metadata-only commands can create `.wrangler/cache` account metadata; downloaded config can contain plain vars, routes, names, and identifiers; Worker import can include deployed source. Keep snapshots outside Git and redact before sharing. When answering from supplied artifacts, say that they remain private and request only the smallest missing artifact. Truncate deployment/version IDs (for example, `1000…0000`) whenever the shortened form still distinguishes the evidence; repeat a full identifier only when it is necessary for an exact user-approved command or to disambiguate otherwise indistinguishable records.

## Collection approval boundary

A static snapshot plan or reconciliation of supplied artifacts normally does not need a documentation refresh. Use this routed reference and the supplied evidence directly. Fetch current official docs only when the user asks, or when the availability or semantics of a command are materially disputed; do not browse merely to restate the command shapes below.

Before any authenticated Wrangler read, show the static command shapes and obtain explicit user approval. Explicitly state that no authenticated command will run before that approval, mark **all** metadata and download commands as pending, then end the plan by asking whether the user approves those authenticated reads; merely saying that nothing ran is not approval. Runtime version IDs are discovered after `deployments status`, so the plan is not an exact concrete transcript. Invoke an already installed, project-pinned Wrangler executable directly (for example, `./node_modules/.bin/wrangler`)—never suggest a package runner or fallback installer such as `npx`, `npm exec`, `pnpm dlx`, or `bunx`, and never introduce `@latest` or a package install as part of collection.

Resolve and confirm the concrete deployed name before planning. A top-level Wrangler `name` is not proof that an `env.<name>` deployment or a second config in the same repository uses that name. Keep each deployed Worker/Pages project as a separate collection target.

Default to metadata-only collection. Source/config download is a separate, more sensitive opt-in and should appear explicitly in the reviewed plan.

After approval, a Worker metadata-only snapshot uses:

```bash
wrangler deployments status --name <WORKER> --json
wrangler deployments list --name <WORKER> --json
wrangler versions list --name <WORKER> --json
wrangler versions view <ACTIVE_VERSION_ID> --name <WORKER> --json
wrangler secret list --name <WORKER> --format json
```

Run `versions view` once for every active version ID from deployment status. It captures version metadata; it does not download deployed source.

A full Worker snapshot may additionally use:

```bash
wrangler init --from-dash <WORKER> --no-delegate-c3
```

**Static Assets rule:** explicitly state that the direct dashboard importer cannot currently clone Workers with Static Assets, skip `init --from-dash`, and use the metadata-only commands instead. Also skip it unless the user explicitly opts into source/config download. The repository wrapper therefore defaults to metadata-only mode and requires `--include-source-config` for the download step.

After approval, a Pages snapshot uses:

```bash
wrangler pages deployment list --project-name <PROJECT> --json
wrangler pages secret list --project-name <PROJECT>
wrangler pages download config <PROJECT> --force
```

Pages config download is experimental. Omit it unless the user explicitly opts into source/config download.

If active-version metadata exposes Service Bindings, do not silently recurse into the referenced Workers. Mark each referenced service as an unresolved deployment target and request a separately planned, separately approved snapshot only when that dependency matters to the audit.

Secret-list commands expose names/types, not values, but names are still sensitive. None of these reads authorizes deploy, rollback, delete, secret mutation, or any other Cloudflare change.
