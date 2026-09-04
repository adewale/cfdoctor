# Lessons Learned

## What we learned in the eval-harness, Wrangler config, and scanner-role pass

This pass started as a PR review, then turned into a small but useful hardening loop: the shared eval harness made the audit contract more testable, the Wrangler examples were updated to match current Cloudflare docs, and the scanner documentation was tightened so users know what the Python tool can and cannot prove.

### Eval assertions must track the audit contract exactly

The skill had already made `Cost / trade-off` mandatory for every confirmed finding, but the first shared benchmark assertions only checked for `Evidence`, `Fix`, `Verify`, and `Source basis`. That left a gap: an answer could pass the benchmark while omitting one of the most important fields in the current output contract.

The lesson is: **contract evals must assert every mandatory contract field, not just the older or easiest-to-match ones**. When the audit format changes, update the skill text, examples, and eval assertions together.

### Current platform defaults should shape examples, not historical muscle memory

The README and trigger eval used `wrangler.toml` because that was the familiar historical config filename. Current Cloudflare docs say Wrangler supports JSON, JSONC, and TOML, but recommends `wrangler.jsonc` for new projects and notes that some newer Wrangler features are only available to JSON config users.

The lesson is: **examples teach defaults**. If the docs recommend `wrangler.jsonc` for new projects, public examples should use `wrangler.jsonc` while still making clear that JSON and legacy TOML remain supported audit inputs.

Source basis: https://developers.cloudflare.com/workers/wrangler/configuration/index.md

### Legacy support belongs in scanners even when examples move forward

Changing examples to `wrangler.jsonc` does not mean the scanner should ignore `wrangler.toml`. Real Cloudflare repos still contain TOML configs, and audit tools need to inspect what exists, not only what new projects should create.

The right split is:

- README/new-project examples: prefer `wrangler.jsonc`
- scanner and audit playbook: inspect `wrangler.jsonc`, `wrangler.json`, and legacy `wrangler.toml`
- recommendations: cite current docs before calling a format preferred, legacy, or feature-limited

The lesson is: **use current defaults for guidance, but broad compatibility for evidence collection**.

### The Python scanner is a triage layer, not the Doctor

The scanner walks local text, parses Wrangler config, inventories products/bindings, and flags heuristic risk patterns. It deliberately does not fetch current docs, inspect account/dashboard state, know traffic volume, know billing data, or prove a finding. That distinction needed to be explicit in the README, recipes, and script docstring.

The lesson is: **a scanner can make suspicious patterns cheap to find, but only the audit workflow can turn a lead into a sourced finding**. Scanner output should be framed as leads to confirm, suppress, or escalate.

### Fixtures should not pollute self-scan signal

Adding a Wrangler fixture for dashboard-claim eval coverage made the repo self-scan start treating the fixture as a real Worker config. That was correct scanner behavior but noisy validation behavior until the fixture declared intentional observability.

The lesson is: **fixture repos are still repo files**. If a self-scan traverses fixtures, either make fixtures intentionally clean or isolate them from scanner scope. Otherwise test data becomes a source of false repository-health noise.

### Bundled skill contents need an explicit mental model

Pi packages progressively disclose skills: the startup prompt sees the skill name and description, then the model reads `SKILL.md`, and only then loads references/scripts as needed. Because `cfdoctor` declares `"pi": { "skills": ["./skills/cloudflare-doctor"] }`, only `skills/cloudflare-doctor` is the installable skill directory; repo-only evals, research notes, and saved results stay outside the runtime bundle.

The lesson is: **document what is bundled and what is loaded**. Users need to know that references, docs, evals, examples, research, and helper scripts ship with the Git-installed package, but the model still has to read/run them on demand.

## What we learned in the check-ID, detection-fixture, and false-negative pass

This pass (2026-06-09) gave every scanner finding a stable check ID, built a
fixture-based detection eval, verified every citation link, routed SKILL.md
references by detected product, and then used the new fixtures to find and fix
five real scanner false negatives.

### Rank work by verifiability, not appeal

Ordering the improvements by "can a command prove this worked" pushed the
plumbing (check IDs, fixtures, consistency checkers) ahead of the more
exciting ideas (account-state collector), and that ordering was right: each
later item consumed the verified output of an earlier one, and the one item
nothing could verify (the collector) was the one worth deferring entirely.

### Fixtures must be written from the failure, not from the regex

The detection fixtures were written as idiomatic code modeling documented war
stories first, and only then checked against the scanner. That discipline is
what surfaced five false negatives — fixtures reverse-engineered from the
scanner's own patterns would have passed immediately and proven nothing. The
follow-up rule is now in the recipes: to fix a false negative, commit a
failing `gap-*` fixture first, then fix the heuristic.

### Heuristic fixes trade precision for recall — say so where users look

Widening the Stream-preload check to work across files also made it fire on
non-Stream video tags in repos that mention a Stream host anywhere. That
trade-off is acceptable for a leads-generator, but only because it is written
down next to the check in the coverage matrix. A widened heuristic with an
undocumented precision cost is a future trust bug.

### Plans are records — correct them in place

The plan assumed the holdout/holdback eval directories were empty
placeholders; they turned out to be intentionally gitignored with a working
split policy. The fix was to amend the plan item in place with the correction
dated, not to quietly skip it. The plan doc is only useful later if it says
what was actually true.

### Updated lesson list

1. Contract evals must assert every mandatory output field, including newly-added fields like `Cost / trade-off`.
2. Public examples should follow current platform defaults; for new Wrangler projects, use `wrangler.jsonc`.
3. Evidence collection should remain backward-compatible with real repos, including legacy `wrangler.toml`.
4. The Python scanner is a read-only lead generator, not a proof engine or replacement for sourced audit judgment.
5. Eval fixtures that live in the repo can affect self-scan results and should be intentionally clean or scoped out.
6. Pi skill packaging is progressive disclosure: `SKILL.md` is discovered, adjacent files are bundled, and references/scripts load on demand.
7. Rank improvement work by verifiability; defer what nothing in the environment can prove.
8. Detection fixtures must model the documented failure, not the detector — and false-negative fixes start with a failing fixture.
9. Document every precision/recall trade-off next to the check it affects, in the coverage matrix.
10. Plan documents are records: correct wrong premises in place, dated, instead of silently dropping items.

## What we learned in the launch-backlog and usage-documentation pass

The final launch cleanup looked administrative — license, CI, repository metadata, release tag, and usage docs — but it exposed one more product lesson: a skill repo is both a tool and a distribution artifact. Users need to know how to consume it; maintainers need to know how to verify it; neither group should have to reverse-engineer that from package metadata.

### A release tag is part of the API

`pi install https://github.com/adewale/cfdoctor` is convenient, but it tracks the moving default branch. Once the repo is public, users also need a stable install target like `@v0.1.0` so they can pin behavior and update intentionally.

The lesson is: **for installable skills, tags and releases are user-facing API, not ceremonial GitHub decoration**.

### Usage docs must separate user paths from maintainer paths

The README originally documented installation, scanner execution, and validation, but not the mental model connecting them. That left a reasonable question: is a normal user expected to run the shared benchmark, provide private holdout prompts, run the scanner, or just install the skill and ask for an audit?

The right split is explicit:

- normal users install the skill and ask for an audit from the target repo
- scanner-only users run the Python scanner for quick read-only triage
- maintainers run validation, shared benchmarks, trigger evals, and ablations
- private holdout/holdback prompts are maintainer eval assets, not usage prerequisites

The lesson is: **if a repo contains both product files and evaluation machinery, the README must say which parts are for users and which parts are for maintainers**.

### Repository settings are documentation surfaces

Topics, homepage, wiki state, license detection, and release state all shape how the project is understood before anyone reads `SKILL.md`. Leaving the wiki enabled, omitting topics, or lacking a license does not break the skill, but it creates ambiguity about where documentation lives and how the code can be used.

The lesson is: **repository metadata is part of launch readiness because it tells users where to look, what they may do, and whether the project is maintained intentionally**.

### CI should run the same checks maintainers ask humans to run

Adding CI was straightforward because the repo already had a small, deterministic validation loop: JSON manifests, Python compile, trigger eval, static self-scan, and `git diff --check`. That made the automated workflow less a new system and more a codified version of the existing release ritual.

The lesson is: **CI is most useful when it automates the exact validation commands documented for maintainers**.

### Updated lesson list addendum

11. Release tags are part of the install API for Git-installed skills.
12. READMEs for skill repos must distinguish normal usage, scanner-only triage, and maintainer eval workflows.
13. Private holdout/holdback eval prompts are not user prerequisites and should be documented as maintainer-only assets.
14. Repository metadata — topics, homepage, wiki state, license, release — is a documentation surface.
15. CI should codify the same deterministic checks maintainers are told to run locally.

## What we learned from deadlint and the cross-boundary RPC pass

The deadlint note was a useful reminder that Cloudflare-specific correctness gaps often live one abstraction layer above generic tooling. A normal dead-code checker sees a public method and stops. In Workers RPC, Durable Objects, Agents, and service bindings, that public method might be a real external entry point — or it might be a forgotten callable surface that no generic tool will flag.

### Public boundary methods are not ordinary public methods

`DurableObject`, `WorkerEntrypoint`, `WorkflowEntrypoint`, `RpcTarget`, and `Agent` classes expose public methods across stubs, service bindings, frontend proxies, and sometimes old deployed clients. That makes their reachability different from ordinary in-process TypeScript methods.

The lesson is: **cross-boundary methods need their own audit path**. A repo-only scanner can identify the review surface, but it cannot prove deletion safety without checking dynamic dispatch, companion frontend files, API docs, old versions, and cross-repo callers.

### Optional third-party analyzers need approval and framing

`deadlint` is useful because it combines TypeScript references with token scans for `.method()`, `["method"]()`, and `.call("method", ...)` caller shapes. But running it through `npx` executes third-party code, and its output is still a reachability lead, not final proof.

The lesson is: **recommend optional analyzers as gated tools, not hidden default steps**. Ask before `npx`, prefer pinned repo tooling when available, and report analyzer output as evidence to verify rather than evidence to delete.

### Fixture coverage should test the review surface, not pretend to solve reachability

The new scanner check deliberately says "cross-boundary public RPC methods need reachability review" instead of "dead method found". The detection fixture asserts that the scanner notices the boundary-class public methods. It does not assert deadness, because that would require a richer TypeScript/call-graph analyzer and external-caller evidence.

The lesson is: **name scanner checks after what they can actually prove**. Precision starts with honest wording.

### Updated lesson list addendum

16. Cross-boundary public methods need a Cloudflare-specific reachability review; generic dead-code tools stop too early.
17. `npx`-based analyzers are optional gated tools: ask approval or use pinned repo tooling before running them.
18. Dead-RPC scanner output is a lead to review dynamic/cross-repo callers, not deletion proof.
19. Fixture coverage should assert the detectable review surface, not a semantic claim the scanner cannot prove.

## What we learned from the provenance, precision, and three-way value pass

The 2026-07-11 hardening pass combined live Cloudflare documentation review,
incident-evidence provenance, parser and scanner fixes, structural oracle
upgrades, and a 24-case GPT-5.5 comparison of the local skill, GitHub
`origin/main`, and no skill. It showed that cfdoctor adds substantial diagnostic
value, but also that workflow overhead and benchmark artifacts can hide or
inflate that value.

### Current official documentation must govern current recommendations

Incident reports and operator war stories are excellent discovery sources:
they reveal failure mechanisms, amplification paths, and questions worth
asking. They are not reliable authority for current product semantics, limits,
pricing, or probability. Those details change independently of the historical
incident.

The lesson is: **use war stories to discover mechanisms, then verify every
current recommendation against current official Cloudflare documentation**.
Future-dated announcements must stay labeled as future changes until their
effective date, and historical migrations must not be rewritten to match a new
default.

### Provenance has to be reciprocal and machine-checkable

A prose bibliography did not make it easy to answer which source justified a
check, which scenario exercised it, or whether two URLs were duplicates of the
same source cluster. The incident claim ledger made evidence IDs, confidence,
freshness, official semantic sources, checks, scenarios, and fixtures explicit.
Requiring fixture-to-ledger and ledger-to-fixture reciprocity exposed lineage
mistakes that one-way links would have missed.

The lesson is: **evidence provenance is a graph, not a footnote list**. Validate
both directions, deduplicate source clusters, reject malformed records without
crashing, and preserve unverified claims as discovery-only instead of quietly
promoting them.

### Parser edge cases are product correctness, not implementation trivia

Wrangler JSONC parsing initially confused comments inside strings, trailing
commas, malformed files, and valid empty objects. That could suppress findings
or create false ones before any Cloudflare reasoning began.

The lesson is: **configuration parsing needs fixture-first language semantics**.
Distinguish valid empty config from parse failure, preserve URLs and comment-like
string content, and emit an actionable diagnostic when evidence cannot be
parsed.

### Static hygiene without impact evidence erodes trust

Checks for compatibility dates, `SELECT *`, `nodejs_compat`, `process.env`,
observability defaults, cron cadence, route breadth, or log sampling can be
useful hypotheses. They become noise when emitted as findings without workload
intent, runtime metrics, account history, or a concrete amplification path.

The lesson is: **absence of a preferred pattern is not automatically a
finding**. Static output remains a lead; explicit intent, tests, compensating
controls, dashboard state, and runtime evidence must be allowed to suppress or
reclassify it.

### Fixture path fidelity is part of oracle validity

Flattening `src/index.js` into `inputs/index.js` while leaving Wrangler's
`main` unchanged manufactured a missing-entrypoint problem in the supposedly
clean fixture. The model was being graded against damage introduced by the eval
staging process, not the source scenario.

The lesson is: **an eval fixture must preserve the operational relationships it
claims to test**. Validate staged entrypoints across every benchmark config, not
just the fixture that first exposed the bug.

### Near-miss controls need semantic, zero-finding oracles

The Queue DLQ-safe case originally overmatched benign wording and did not prove
that work happened before acknowledgement. A polished but contradictory answer
could therefore pass. The corrected oracle requires configured bounded retries,
an explicit DLQ, process-before-ack recognition, and zero finding blocks; a
contradictory ack-before-work answer is now a regression test.

The lesson is: **precision-critical controls need negative semantics, not just
keywords**. A safe fixture should fail if the model invents any confirmed
finding or describes the safety invariant backwards.

### Skill overhead is a measurable product defect

The GitHub skill's mandatory broad reference reading and full report scaffold
produced strong answers but used 134,984 mean tokens and 90.6 seconds per run.
Hypothesis-driven reference routing, a hard activation boundary, and concise
triage/no-finding modes cut the local result to 56,843 tokens and 45.0 seconds
while improving objective and combined scores.

The lesson is: **process instructions belong in the value function**. Measure
tokens, elapsed time, and command count alongside correctness. Do not invoke a
Cloudflare audit for standalone AWS, generic DNS, public status, brand-copy, or
no-input repo claims, and do not require a full report when there are no
confirmed findings.

### Benchmarks need old, new, and no-skill baselines

A local-versus-no-skill comparison measures whether the skill adds value, but
not whether a rewrite improved the skill. A local-versus-GitHub comparison
measures the rewrite, but not whether either skill beats the base model. The
three-way run answered both questions: local scored 97.22% objective and 97.57%
combined, versus GitHub at 60.28%/65.23% and no skill at 73.19%/70.50%.

The lesson is: **evaluate meaningful skill changes three ways**. Keep the
published baseline immutable, include no skill, and report quality and
efficiency together.

### Grade behavior, not evaluator passwords

Negative activation cases initially required phrases such as `NO_TRIGGER` or
“not a Cloudflare audit.” Correct answers that simply explained DNS or checked
the status page failed because they did not utter the evaluator's password.
Replacing those assertions with behavior-based exclusions of the Cloudflare
Doctor scaffold raised validity without changing the requested behavior.
Likewise, a `1.0` qualitative threshold mislabeled useful 0.92–0.96 answers;
`0.85` plus critical deterministic vetoes better matches the actual contract.

The lesson is: **oracles should recognize desired behavior, not mandatory
meta-language**. Use structured extraction and critical vetoes for hard
requirements, graded judge bands for qualitative quality, and adversarial tests
against keyword stuffing.

### Audit the benchmark after it reports success

An independent reviewer found both the activation-password problem and the
missing process-before-ack semantic check after the first three-way report was
complete. Fixing those issues materially changed the headline rates while
leaving the local-versus-no-skill objective lift intact.

The lesson is: **the evaluator is part of the system under test**. Run an
adversarial review of fixtures, staging, assertions, thresholds, arithmetic,
and claims before publishing results.

### Model evidence needs explicit uncertainty

The final run used one answer per case and GPT-5.5 to judge GPT-5.5. Hidden
holdout and holdback prompts were unavailable, several efficiency results were
close to visible thresholds, and dollar-cost telemetry was absent. The seeded
4,096-sample sign-flip test supports the paired lift, but it does not remove
run-to-run or judge-alignment risk.

The lesson is: **publish model-eval limitations beside the headline**. Repeated
runs, private holdouts, human or second-model judge-alignment samples, and
value-per-token measures are required before treating tune-set results as a
universal guarantee.

### PR audits must verify committed ranges and durable evidence

The multi-agent PR audit found that `git diff --check` on a clean checkout says
nothing about whitespace already committed in the PR, that JSON-only ledger
URLs were absent from Markdown link discovery, and that an aggregate assembled
from outputs generated across multiple skill revisions cannot represent one
current implementation. Re-running all local outputs from one pinned commit and
committing a machine-readable aggregate made the claims reproducible without
committing raw transcripts.

The lesson is: **validate the committed base-to-head range and pin every
benchmark variant to an immutable revision**. Durable result summaries should
include per-case scores, judge evidence, telemetry, failed assertions, and
artifact hashes; local `/tmp` paths are useful reproduction aids, not published
evidence.

The same audit also showed that fixture/evidence reciprocity needs at least one
matching required or forbidden check ID, and that declaring a freshness cadence
is insufficient unless the validator enforces the interval. URL discovery must
include machine-readable evidence stores as well as Markdown.

### Broad “fix it” requests do not authorize production mutation

An audit can recommend changes without being authorized to deploy, rotate
secrets, purge caches, change DNS/WAF policy, or mutate Cloudflare resources.
That boundary matters more as the skill becomes more capable.

The lesson is: **diagnosis and mutation are separate permissions**. Require an
exact target, evidence, blast radius, dry run or rollback plan, and final
confirmation before any authenticated production change.

### Updated lesson list addendum

20. Current official Cloudflare docs govern current semantics; war stories are mechanism-discovery evidence only.
21. Evidence provenance is a reciprocal, machine-validated graph with explicit confidence and freshness.
22. JSONC parsing correctness needs fixtures for strings, comments, trailing commas, empty config, and malformed input.
23. Static hygiene is a lead, not a finding, unless intent or impact evidence makes it material.
24. Benchmark staging must preserve entrypoint and configuration relationships across every fixture.
25. Safe near-miss oracles need zero-finding gates and explicit semantic invariants such as process-before-ack.
26. Token, latency, and command overhead are product-quality metrics, not incidental telemetry.
27. Major skill revisions should compare local, published baseline, and no skill.
28. Grade requested behavior rather than evaluator passwords or keyword presence.
29. Independently audit fixtures, assertions, thresholds, arithmetic, and claims before publishing benchmark results.
30. One-run, same-model judging, visible tune cases, and absent dollar telemetry must remain explicit limitations.
31. Audit/fix requests do not authorize production mutation without target, evidence, blast radius, rollback, and confirmation.
32. CI diff checks must compare the committed base-to-head range; a clean working-tree diff is vacuous.
33. Model outputs for one reported variant must come from one pinned skill revision.
34. Publish durable machine-readable eval aggregates; local raw-artifact paths are not sufficient evidence.
35. Ledger URLs, declared freshness cadence, and fixture-to-check provenance all need direct validation.

## What we learned from replacing the account collector with Wrangler

The first ground-truth design invented a general facts schema before checking
whether the official client could already retrieve the state we needed.
Wrangler can download Worker/Pages configuration and list secret names; for
Workers, it can also identify every active version and show version-specific
bindings/runtime limits. That is a
more current and testable normalization layer than a new API abstraction.

The lesson is: **use the product's maintained read surface before building a
collector**. Capture the raw official-client evidence privately, compare repo
Worker intent with downloaded configuration and active version metadata (or
Pages intent with downloaded config and deployments), then add one targeted API
read only for a remaining hypothesis.

Wrangler output is not harmless or complete: `init --from-dash` downloads
source, plain vars and resource metadata may be present, gradual deployments can
have multiple active versions, and downloaded config is an approximation rather
than continuous sync. Explicit approval, private output, version recording, and
review-before-sharing remain mandatory.

36. Prefer maintained Wrangler read commands over a custom universal account-state schema.
37. Effective Worker state requires deployment status plus every active version, not merely the latest version or downloaded config.
38. Wrangler snapshots are sensitive local evidence: keep them outside Git, hash the artifacts, and review/redact before sharing.

### Live Wrangler validation changed what we knew

A disposable account was not a technical requirement. After explicit approval,
existing projects covered the useful integration boundaries: a Worker without
Assets exercised complete source/config capture, a Pages project exercised the
experimental config downloader, and a staging Worker with Assets exercised the
metadata-only path. All commands completed across Wrangler 4.53.0, 4.71.0, and
4.94.0 without a Cloudflare mutation.

The live outputs caught mock-reality drift. Pages `--json` returned capitalized
display fields (`Id`, `Environment`, `Branch`, `Source`, `Deployment`, `Status`,
and `Build`), while Worker version output included `number`, `annotations`, and
nested `resources`. The fake was valuable for approval, allowlist, failure,
permission, and manifest behavior, but it could not establish Cloudflare's real
response contract. Sanitized fixtures must come from observed shapes.

The metadata-only label also understated the privacy boundary. Wrangler wrote
`.wrangler/cache` account metadata beneath its working directory even when no
source was downloaded. Full Worker capture produced a substantial deployed
bundle, and Pages download produced local config plus Wrangler cache files. The
correct retention unit is therefore the entire snapshot directory: keep it
private, extract only minimal schema evidence, and delete the raw directory.

Finally, project dependency declarations were not uniformly installable with
`npm ci` from the relevant subdirectories. Resolving each exact Wrangler version
from the repository lockfile and installing only that version in an isolated
temporary directory—with lifecycle scripts disabled—validated the intended
client without modifying projects or executing unrelated setup code.

39. Existing approved non-production projects can validate read-only collection; disposability is a safety option, not a correctness requirement.
40. Handwritten fakes prove wrapper behavior, not external response fidelity; derive committed contract fixtures from reviewed, sanitized live shapes.
41. Workers with Assets need a metadata-only path because `init --from-dash` cannot currently clone them.
42. “Metadata-only” does not mean non-sensitive: Wrangler cache files can contain account metadata.
43. Treat the complete snapshot directory as sensitive, including command stderr, downloaded config, source, and `.wrangler/cache`.
44. Use exact lockfile-resolved client versions in isolated tooling directories when project installs are not reproducible; disable lifecycle scripts for read-only validation setup.
45. Delete raw authenticated evidence after extracting the smallest durable schema facts needed for tests and documentation.

### The PR audit tightened the meaning of “private” and “complete”

Independent security, correctness, test-quality, and claim reviews agreed that
the Wrangler-first scope was sound, but found that two labels were stronger than
the implementation. A Worker snapshot with a successful status command but no
`versions` array could be marked complete without capturing active runtime
state. A downloaded symlink was recorded as rejected but remained on disk, where
later archive or copy tooling could follow it. Both cases show that a warning in
a manifest is not equivalent to enforcing the claimed postcondition.

The audit also exposed two defense-in-depth gaps. Nested directory privacy had
relied on the caller's umask even though files and the root directory were
explicitly chmodded. Wrangler inherited the complete parent environment,
including unrelated cloud credentials and Node injection options. Setting a
restrictive umask, recursively enforcing directory modes, forwarding a narrow
auth/config environment, and disabling subprocess stdin made the read boundary
match the documentation more closely.

Finally, prefix-matching fake commands were too permissive: they would accept
unexpected trailing flags even though plan review is meaningful only when tests
lock the complete argv. Exact command fakes plus fail-closed version and active
state tests now make safety regressions observable.

46. “Complete” is a verified postcondition: a Worker snapshot needs a non-empty active-version set and a successful view of every discovered version.
47. Rejecting a symlink means removing or quarantining it, not merely recording an error while leaving it in a shareable directory.
48. Private output requires a restrictive creation umask and recursive directory-mode assertions, not just root/file chmods.
49. A read-only child process should receive only the credentials and configuration it needs; unrelated parent secrets and runtime injection variables stay outside the boundary.
50. Command-allowlist tests must assert complete argv shapes because prefix fakes silently accept dangerous flag drift.
51. Reserved wrapper filenames must be excluded by exact root path, not basename, or legitimate downloaded files can escape permissions and inventory.
52. A plan containing runtime-discovered version IDs is a static command-shape review, not an exact concrete command transcript.

### Review the fixes, not only the original change

The first audit found real boundary failures; the post-fix audit then found a
newly visible basename bug. Skipping every file named `manifest.json` was meant
to exclude the wrapper's root manifest, but it also excluded legitimate
downloaded project manifests from chmod, hashing, and inventory. Scoping the
exception to the exact root path closed that gap. A final reviewer also caught
that documentation still described runtime-expanded commands as an exact plan
and blurred Worker active-version evidence into the Pages deployment model.

The lesson is: **a fix is a new change that needs independent verification**.
Run a fresh post-fix reviewer against the complete committed range, use focused
regression probes for each accepted finding, and repeat until no fix worth doing
now remains. Security-boundary tests should prove both directions: unrelated
credentials and stdin do not cross the process boundary, while the required
Cloudflare authentication still does.

53. Treat post-fix review as a distinct validation phase because remediation can introduce adjacent omissions.
54. Product capability claims must stay product-specific: Workers expose active-version metadata; Pages exposes deployments and downloaded config.
55. Boundary tests need positive and negative controls: preserve required authentication while excluding unrelated secrets, injection options, and stdin.

### A benchmark cannot value functionality it never exercises

The first GPT-5.5 PR round scored below current main even though their
`SKILL.md` files were byte-identical and none of the divergent cases loaded the
new Wrangler reference. Trace comparison showed autonomous trajectory variance:
one run searched the whole skill tree or read broad references while its paired
run stopped early. The non-significant paired result was a regression signal,
not causal evidence against the new guidance.

More importantly, the benchmark had no Wrangler snapshot cases. Adding four
focused cases changed the question from “did unrelated legacy answers vary?” to
“does the model safely reconcile and collect this new evidence?” A dedicated,
short routed reference then improved that four-case slice from 68.21% to 95%
objective under strengthened semantic oracles, while the fresh 24-case legacy slice stayed within 0.21 points of
main. The targeted slice is small, but it now guards the actual product behavior.

56. Add eval cases for a feature before using aggregate model scores to judge that feature's value.
57. When paired variants share identical loaded instructions and the changed reference was never read, inspect trajectory variance before claiming causation.
58. Compare traces, commands, reference reads, and token outliers—not only final percentages—to explain model regressions.
59. Route narrow workflows to dedicated references; burying them in broad guidance increases omission risk and unnecessary context.
60. Report legacy and new-feature slices separately so a broad aggregate cannot hide either regression or genuine feature lift.

### Survey real configuration fleets without confusing copies for projects

A complete default-branch review of 86 accessible `adewale/*` repositories found
334 Wrangler JSONC files, but only 24 were deployable-project configs. Sixty
were maintained examples or compatibility tests, 20 were intentional cfdoctor
fixtures, and 230 lived in a generated corpus cache. Several cached files were
byte-identical copies of separately counted owner projects. A raw file count
would therefore have overstated both product prevalence and scanner findings.

The deployable configs still changed the design. Workers Static Assets appeared
in two thirds of them, making Wrangler's Assets-incompatible dashboard importer
a poor default and strengthening the least-privilege case for metadata-only
capture. Environment overrides, multiple configs in one repository, and Service
Bindings also showed that repository path and top-level Worker name do not
fully identify deployed scope. Meanwhile, modern example/corpus configs exposed
valid product keys that the scanner had not inventoried.

61. Classify deployable source, maintained examples, intentional fixtures, and generated/vendored corpora before computing repository-fleet statistics.
62. Exclude known generated corpus caches from default scans; exact copies otherwise double-count evidence and manufacture findings.
63. Least-sensitive collection should be the default, especially when the more invasive path is unsupported by a common configuration such as Workers Static Assets.
64. Confirm the concrete deployed name for each config/environment; a repository can own several separately deployed Workers.
65. Service Bindings identify dependencies, not authorization to recurse into more account state; expand each target with a separate plan and approval.
66. Use broad corpora to discover parser/product-surface gaps, not as authority for defect prevalence or current semantics.
67. Repeated full observability sampling is a usage-evidence question, not a static defect: traffic, retention, plan, and billing data determine materiality.

### Bounded static analysis and matched evaluation beat broad claims

The 0.3.5 scanner pass closed five known gaps without pretending to solve arbitrary program analysis: it follows bounded constants/imports and URL aliases, matches literal Queue names, requires real alarm conditions, and links Stream preload through repo-visible symbols. The same calibration applied to prompt-only checks: explicit full sampling and webhook side effects can produce review leads, while effective origin, alert, and preview-public state still require account evidence.

A matched three-way evaluation also changed the evidentiary quality. Running the exact current tree, immutable main, and no skill three times per case made the Wrangler lift clear while showing that legacy behavior remained statistically compatible with main and pricing still needed efficiency work. A second-model judge sample agreed on 26/27 pass decisions, which is useful sensitivity evidence but not a substitute for human labels.

68. Resolve only bounded, repo-visible data flow; document the dynamic/helper-function boundary instead of calling the heuristic complete.
69. A prompt-only check can gain a calibrated static lead without converting unavailable account state into a repository finding.
70. When an incident source remains unavailable and uncorroborated at its review boundary, supersede it rather than perpetually warning or silently citing it.
71. Compare current, immutable baseline, and no-skill arms under one manifest, sample count, and interleaved protocol before claiming current lift.
72. Report feature, legacy, and new-eval slices separately: aggregate lift can coexist with a weak pricing slice or a non-significant legacy delta.
73. Cross-model judge agreement measures sensitivity between judges; human-labeled alignment remains a separate requirement.

## What we learned from the Polylane Durable Object memory pass

Polylane's engineering post on ~300 daily Durable Object memory resets arrived
as a tweet link. The first instinct was to treat it like the earlier billing
war stories: a scenario, a couple of scanner checks, a ledger record. Working
it through changed the shape of the change in four ways.

### Ask how much of an incident is platform-specific before deciding where it belongs

The fix Polylane shipped was generic JavaScript hygiene: plain JSON Schema
instead of zod trees, `sideEffects: false`, named re-exports, static imports.
What made it an outage was Cloudflare: a fixed 128 MB isolate budget with no
knob, memory measured per isolate and shared by every Durable Object of a
class, a reset with no stack trace that invalidates stubs, and no production
heap profiler. The repository's bar for a war story was never "Cloudflare
caused it"; half the checklist is Lambda, Firebase, Netlify, and Vercel. The
bar is a triggering shape the audit can confirm plus a Cloudflare product fact
it can cite. Separating mechanism (generic) from blast radius and
diagnosability (Cloudflare) is what decides which artifacts to write.

### Ground a war story in the platform's own documentation before writing checks

Grepping Cloudflare's per-product `llms-full.txt` exports for memory, heap,
OOM, eviction, and startup turned one anecdote into a documented failure
class: `Script startup exceeded memory limit` and the 1 s startup CPU limit
on plain Workers, with "a large schema at the top level" named as the common
cause; memory "measured per isolate, not per Durable Object"; duration billed
at the full 128 MB allocation even when objects share an isolate; an
`exceededMemory` invocation outcome in analytics, Logpush, Tail, and traces;
`maxOomRetries` in Cloudflare's own Agents SDK; D1, Containers, Snippets, and
Browser Run each with their own memory semantics. The docs survey was thrown
away once its content had been absorbed into the references, the ledger, and
the checklist; a research note that duplicates the runtime references rots.

### Do not turn generic lint into Cloudflare findings

The first proposal added standalone checks for `export *` barrels, missing
`sideEffects`, and dynamic package-root imports. Those patterns appear in every
TypeScript monorepo, including ones whose isolate idles at 30 MB, and the
repository had just spent two releases on precision. The shipped lead counts
schema builders that actually run at module scope, fires only above a
threshold that is lower when Durable Object bindings exist, reports the
barrel/`sideEffects`/dynamic-import patterns as amplifiers inside that one
finding, and tells the reader to measure. Memory findings need a measurement
path, not a pattern match.

### Measurement recipes belong next to checks that cannot produce a number

A regex cannot produce a heap figure, and the incident's own numbers came from
a local probe of the exact `wrangler deploy --dry-run` bundle. The recipe now
lives in `docs/recipes.md` beside `wrangler check startup` and the dry-run
bundle size, with the interpretation rule that turns the account chart into a
diagnosis: high and flat at idle means baseline, trending up at constant
traffic means a leak. The Wrangler snapshot wrapper set the precedent for
read-only tooling that produces evidence; a dry-run build never touches the
account and fits that posture even more easily.

### Updated lesson list addendum

74. Classify an incident by mechanism and by blast radius separately; a generic mechanism with a platform-specific blast radius still belongs in the skill, framed around the platform fact.
75. Before writing checks for a war story, survey the platform's own documentation for the failure class; one anecdote plus documented semantics is a scenario, one anecdote alone is a note.
76. Discard research notes once their content is absorbed into runtime references and the ledger; keep provenance in the ledger, not in a parallel document.
77. Patterns that are common in healthy codebases must not become standalone findings; count the memory-relevant signal, gate on the platform shape, and report the common patterns as amplifiers.
78. When a check cannot produce the number a finding needs, ship the measurement recipe with the check and make the finding say "measure" rather than "defect".
79. State the interpretation rule alongside the account read (flat-at-idle means baseline; upward at constant traffic means leak) so the evidence request can decide the hypothesis.
80. Benchmark-staged fixtures must keep `main` as a root-level basename; nested entrypoints break the staging test even when the detection eval passes.

