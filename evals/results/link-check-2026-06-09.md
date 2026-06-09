# Link check — 2026-06-09

Run: `python3 scripts/check_links.py --json evals/results/link-check-2026-06-09.json`
Scope: README.md, references/, research/, docs/, evals/ (recursive). 397 unique URLs.

## Counts

| Classification | Count |
|---|---|
| ok (2xx) | 337 |
| redirect-ok | 32 |
| unverifiable-automated (bot-blocked domains; check manually) | 3 |
| dead (404/410/DNS failure) | 20 |
| error (timeout/5xx/403 from non-allowlisted domain) | 5 |

## Dead links (404/410/DNS)

- https://aquasecurity.github.io/tfsec/v1.28.1/getting-started/configuration/ignores/ — research/doctor-patterns-research.md (tfsec is archived; docs moved into Trivy)
- https://developers.cloudflare.com/cache/advanced-configuration/cache-analytics/ — references/official-source-map.md
- https://developers.cloudflare.com/cache/concepts/cache-keys/ — references/official-source-map.md
- https://developers.cloudflare.com/dns/additional-options/caa/ — references/official-source-map.md
- https://developers.cloudflare.com/pages/functions/limits/ — references/official-source-map.md
- https://developers.cloudflare.com/queues/configuration/delivery-guarantees/ — references/official-source-map.md, references/recommendation-provenance.md
- https://developers.cloudflare.com/r2/api/s3/multipart-uploads/ — references/official-source-map.md
- https://developers.cloudflare.com/r2/observability/ — references/official-source-map.md
- https://docs.netlify.com/accounts-and-billing/ — research/serverless-horror-stories.md
- https://docs.netlify.com/accounts-and-billing/monitor-usage/ — research/serverless-horror-stories.md
- https://docs.netlify.com/functions/limits/ — research/serverless-horror-stories.md
- https://docs.railway.com/guides/usage-limits — research/serverless-horror-stories.md
- https://fireship.io/lessons/firebase-costs/ — research/serverless-horror-stories.md
- https://github.com/adewale/skill-eval-harness.git@v0.1.1 — evals/shared-harness.md (pip-style VCS pin, not a hyperlink; 404 over plain HTTP is expected)
- https://render.com/docs/billing — references/war-story-scenario-checklist.md, research/serverless-horror-stories.md
- https://supabase.com/docs/guides/platform/usage — research/serverless-horror-stories.md
- https://vercel.com/blog/introducing-spend-management — research/serverless-horror-stories.md
- https://www.fastly.com/documentation/guides/compute/limitations/ — research/serverless-horror-stories.md
- https://www.maciejpocwierz.com/posts/anatomy-of-a-aws-bill-shock/ — references/war-story-scenario-checklist.md, research/serverless-horror-stories.md (DNS failure)
- https://www.netlify.com/blog/addressing-recent-billing-concerns/ — research/serverless-horror-stories.md

## Unverifiable-automated (bot-blocked; check manually, not dead)

- https://medium.com/@PurpleGreenLemon/how-not-to-get-a-30k-bill-from-firebase-37a6cb3abaca (403)
- https://old.reddit.com/r/webdev/comments/1b14bty/netlify_just_sent_me_a_104k_bill_for_a_simple/ (403)
- https://www.reddit.com/r/CloudFlare/comments/1t1e8nh/i_accidentally_generated_16_billion_durable/ (403)

## Errors (inconclusive, not proven dead)

- https://metacast.app/blog/engineering/postmortem-llm-bots-image-optimization (403 from non-allowlisted domain; effectively bot-blocked, check manually)
- 4x https://web.archive.org/web/... snapshot URLs added as citation annotations. These 403 only because this environment's egress proxy blocks the web.archive.org hostname (`x-block-reason: hostname_blocked`); each snapshot URL was returned verbatim by the archive.org availability API (http://archive.org/wayback/available) with `"status": "200", "available": true`. Expect them to resolve normally outside this sandbox.

## Archive annotations applied (war-story citations)

Verified Wayback snapshots (via availability API, status 200) appended as `(archived: ...)`:

- https://www.reddit.com/r/CloudFlare/comments/1t1e8nh/... → snapshot 20260506025828
- https://old.reddit.com/r/webdev/comments/1b14bty/... → snapshot 20250908035924
- https://medium.com/@PurpleGreenLemon/how-not-to-get-a-30k-bill-from-firebase-37a6cb3abaca → snapshot 20200429160249
- https://metacast.app/blog/engineering/postmortem-llm-bots-image-optimization → snapshot 20260304063157

No snapshot found (availability API queried 3-4x each; annotated `(no archive snapshot found as of 2026-06-09)`): the 11 dead war-story citations in research/serverless-horror-stories.md and references/war-story-scenario-checklist.md (docs.netlify.com x3, docs.railway.com usage-limits, fireship.io firebase-costs, render.com/docs/billing, supabase.com platform/usage, vercel.com blog spend-management, fastly.com compute/limitations, maciejpocwierz.com, netlify.com billing-concerns blog).

Dead links in references/official-source-map.md, references/recommendation-provenance.md, research/doctor-patterns-research.md, and evals/shared-harness.md are not war-story citations and were left unannotated; they should be re-pointed at current doc paths in a follow-up.
