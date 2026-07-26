# Cloudflare compute landscape refresh — 2026-07-26

## Scope and method

Triggered by a third-party explainer of Cloudflare's compute services
([cipher.co.th](https://www.cipher.co.th/en/blogs/cloudflare-compute-services-explained/)).
The article itself is **not usable as a source** under
[`recommendation-provenance.md`](../skills/cloudflare-doctor/references/recommendation-provenance.md):
it is a secondary explainer, so it fails both the pricing/limits rule (official
Cloudflare docs only) and the war-story bar (first-hand operational context, not
a generic blog summary). It was treated as a **coverage checklist** — a list of
compute primitives to test our runtime guidance against — and nothing more.

Method:

- verified every load-bearing claim in the article against current official docs
  fetched with `Accept: text/markdown`;
- searched Hacker News stories and comments through the Algolia API from
  2026-01-01, then fetched the linked operator write-ups in full;
- fetched the Containers pricing, limits, lifecycle, Container class, and
  Wrangler configuration pages to establish current semantics;
- deduplicated candidates against `research/incident-claim-ledger.json` by
  causal source cluster.

General web search was low-signal for this topic: results were dominated by SEO
explainers restating the same docs, several with cold-start figures that conflict
with both Cloudflare's documented range and first-hand operator reports. Those
were rejected. GitHub issue mining was **not** performed this pass — this
session's repository scope is limited to `adewale/cfdoctor`, so the
`cloudflare/workers-sdk` sweep used in the 2026-07-11 refresh was out of scope.
That is a known gap in this refresh, not a finding of absence.

## Verification of the triggering article

Every checkable claim matched official docs. Recording this because the useful
output is the *confirmation*, not new facts:

| Claim | Official source | Verdict |
|---|---|---|
| Containers billed per 10ms active; max instance 4 vCPU / 12 GiB / 20 GB | `containers/pricing/`, `containers/platform-details/limits/` | accurate (`standard-4`) |
| Workflows $0.80 per 100k steps, 500k included, billing starts August 2026 | `workflows/reference/pricing/` | accurate; docs give the precise date, **August 10, 2026** |
| Browser Run 10 hrs + 10 concurrent included, $0.09/hr, $2.00/browser | `browser-run/pricing/` | accurate |
| Durable Objects ~1,000 req/s soft limit per object | `durable-objects/platform/limits/` | accurate |
| WebSocket Hibernation cut a bill from ~$138 to ~$10/month | none cited | **rejected** — no primary source |

The article is a faithful restatement of official docs. It contains no
Cloudflare-specific mechanism that our runtime guidance did not already cover,
**except** by omission: it treats Containers as a first-class compute primitive,
which exposed that we did not.

## What is working

Evidence below is first-hand unless marked.

### 1. Containers as a bounded escape hatch from the isolate

Two independent production write-ups describe the same successful shape: a
Worker-shaped app with one genuinely container-shaped job hanging off it.

- **VideoToBe** runs FFmpeg in Containers with R2 mounted via FUSE, keeping bytes
  on Cloudflare's internal network rather than the public internet
  (`CFDOC-EVD-VIDEOTOBE-CONTAINER-FFMPEG`). The R2 FUSE mount pattern has since
  become an official documented example, which is corroboration that the pattern
  is supported rather than a hack.
- **Kent C. Dodds** moved podcast FFmpeg work off a shared app server that was
  spiking to 400–500% load with CPU throttling; after the move the same box peaked
  at 60–80% (`CFDOC-EVD-KCD-CONTAINER-FFMPEG`).

The common factor is not the workload type — both are media transcoding — but
that the job is **bursty, bounded, and already adjacent to R2**.

### 2. Workflows for non-critical durable execution

Operators report Workflows working well for onboarding and payment flows, and
specifically value the generated flowchart visualizer for reasoning about what a
workflow does. The step meter and dashboard visualizer are real adoption drivers.

### 3. Durable Objects where per-key coordination is the actual requirement

No new negative evidence this pass. The existing `CFDOC-EVD-WIRE-DO-EXIT` record
remains the most careful critique, and its author explicitly says workloads
without their specific constraints should stay on Durable Objects.

## What is not working

### 1. The Container idle window is the platform's least-obvious billing surface

This is the material finding of this refresh.

Containers bill memory and disk on the instance's **provisioned** size for every
10ms the instance is **awake**, with only CPU tracking actual use. An instance
stays awake until the `sleepAfter` timer expires with no requests — currently
defaulting to `"10m"` on the Container class. So every wake carries an idle tail
billed at full provisioned memory and disk.

Both production accounts hit this independently, from opposite directions:

- VideoToBe's Worker terminated the container **mid-job** after returning 202,
  until the call was wrapped in `ctx.waitUntil(container.monitor())`;
- Kent C. Dodds added heartbeat pings to prevent premature shutdown, then added
  immediate stop-if-idle signalling "instead of relying on timeout windows" —
  explicitly to avoid paying for idle.

Both write-ups also repeat the platform's scale-to-zero framing ("the container
does not cost anything when it is asleep"). That is true and is exactly what
makes the gap easy to miss: the claim is about the *asleep* state, while the
money is spent in the *awake-but-idle* window before it. Neither the triggering
article nor any SEO explainer surveyed mentions this.

**Effect on cfdoctor:** added `CFDOC-COST-CONTAINER-IDLE-WINDOW` as a scanner
lead, plus `CFDOC-COST-CONTAINER-DUTY-CYCLE` and
`CFDOC-REL-CONTAINER-DETACHED-DISPATCH` as prompt-only rows.

### 2. "Cloudflare has no egress fees" does not survive contact with Containers

`cost-footguns.md` already warns against reading R2's no-egress promise as "no
bill." Containers go further: they bill network egress outright, at a documented
per-GB rate varying by region. An engineer carrying the R2 intuition into a
Container cost model will be wrong, and this is the only Cloudflare compute
primitive where that is true.

### 3. Operators disagree about Containers for the same workload

In a single thread, one operator calls Containers "the most expensive product
they have" for FFmpeg and routes to spot instances or a dedicated Hetzner box,
while others report bursty jobs as "not even noticeable in billing"
(`CFDOC-EVD-CONTAINER-DUTY-CYCLE-SPLIT`, retained **unverified** — no invoices).

The disagreement is not noise: it is duty cycle. Containers price well for work
that sleeps and badly for work that does not, and workload *type* does not
predict which. This is why the duty-cycle check is prompt-only — it needs
request-rate and awake-seconds evidence a regex cannot supply.

### 4. Cold-start figures in circulation are unreliable

Cloudflare documents roughly 1–3 seconds, image-dependent. SEO articles claim
180–320ms for typical production images. One first-hand report puts a
"very lightweight image" at 6–7 seconds. We should quote Cloudflare's range and
treat cold start as a measurable per-project property, never a constant. Note
that cold start is billed active time as well as latency.

### 5. Keep-warm pings are a silent billing-model change

The widely-recommended fix for container cold starts is scheduled pings. Because
activity resets the `sleepAfter` timer, that converts a scale-to-zero workload
into an always-on one. It is a legitimate latency-for-cost trade, but it should
be priced deliberately — and if the answer is "always warm," the product-fit
question against a rented VM deserves re-asking.

### 6. Operators are building their own cost observability

An operator published a CLI querying Cloudflare's GraphQL Analytics API for usage
and cost estimates across Workers, Durable Objects, Containers, Workers AI, R2,
D1, KV, and Queues, motivated by not wanting to be surprised by the bill. Along
with recurring prepaid-billing/spend-cap requests, this supports the existing
spend-controls cluster and the "no cost proxies in run summaries" footgun:
per-run cost accounting is still something operators have to build themselves.

## Calendar item

Workflows step and storage billing starts **August 10, 2026** — 15 days after
this refresh. `cost-footguns.md` already carries the date and the instruction to
re-check the changelog before making a current-invoice claim. That guard becomes
load-bearing rather than theoretical once the date passes; the next refresh
should verify billing actually started rather than assuming the announced date
held.

## Resulting repository actions

- Added a Containers section to
  [`product-fit-rubric.md`](../skills/cloudflare-doctor/references/product-fit-rubric.md)
  and [`cost-footguns.md`](../skills/cloudflare-doctor/references/cost-footguns.md).
- Registered `CFDOC-COST-CONTAINER-IDLE-WINDOW` in the scanner with the
  `container-idle-window` detection fixture; suppression requires a `sleepAfter`
  declaration or an `onActivityExpired()`/`renewActivityTimeout()` call, not a
  prose mention.
- Added `CFDOC-COST-CONTAINER-DUTY-CYCLE` and
  `CFDOC-REL-CONTAINER-DETACHED-DISPATCH` as prompt-only matrix rows.
- Expanded the evidence ledger from 29 to 32 records, retaining exactly 23
  runtime checklist scenarios.

## Known gaps in this refresh

- No `cloudflare/workers-sdk` issue sweep (repository scope limitation).
- No Pipelines or Workers VPC runtime guidance; both remain detection-and-pricing
  only, the same gap Containers had before this change.
- The duty-cycle threshold where Containers stop beating a VM is unquantified. It
  needs a real awake-seconds-per-job measurement, which no public write-up supplies.
