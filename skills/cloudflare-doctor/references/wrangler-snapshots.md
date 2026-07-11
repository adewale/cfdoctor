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

Treat the entire snapshot as sensitive. Even metadata-only commands can create `.wrangler/cache` account metadata; downloaded config can contain plain vars, routes, names, and identifiers; Worker import can include deployed source. Keep snapshots outside Git and redact before sharing. When answering from supplied artifacts, say that they remain private, avoid repeating identifiers that are not needed for the conclusion, and request only the smallest missing artifact.

## Collection approval boundary

Before any authenticated Wrangler read, show the static command shapes and obtain explicit user approval. Mark **all** metadata and download commands as pending that approval, then end the plan by asking whether the user approves those authenticated reads; merely saying that nothing ran is not approval. Runtime version IDs are discovered after `deployments status`, so the plan is not an exact concrete transcript. Use an already installed, project-pinned Wrangler executable—never introduce `npx`, `@latest`, or a package install as part of collection.

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

**Static Assets rule:** explicitly state that the direct dashboard importer cannot currently clone Workers with Static Assets, skip `init --from-dash`, and use the metadata-only commands instead. Also skip it whenever the user declines source/config download.

After approval, a Pages snapshot uses:

```bash
wrangler pages deployment list --project-name <PROJECT> --json
wrangler pages secret list --project-name <PROJECT>
wrangler pages download config <PROJECT> --force
```

Pages config download is experimental. Omit it when the user requests metadata only.

Secret-list commands expose names/types, not values, but names are still sensitive. None of these reads authorizes deploy, rollback, delete, secret mutation, or any other Cloudflare change.
