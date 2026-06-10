# Improvement plan: ranked by verifiability and likelihood of success

Date: 2026-06-09. This plan orders the skill-improvement recommendations by how
deterministically each change can be verified and how likely it is to deliver
its intended benefit. Items are implemented in this order. Every item records
its risks and downsides, because each change can also make the skill worse if
the risk is ignored.

## Status (end of 2026-06-09 pass)

1. Scanner check IDs + JSON output — **done** (scanner 0.3.0; 56-check registry; scanner 0.3.1 adds the dead-RPC review-surface lead, bringing the registry to 57 checks).
2. Fixture-based detection evals — **done** (15 fixtures, including five
   `gap-*` fixtures that reproduced and then closed real false negatives).
3. Coverage matrix + consistency checker — **done** (CI-enforced).
4. Link verification + archive fallbacks — **done** (initial run; periodic
   re-runs tracked in `TODO.md`).
5. SKILL.md reference routing — **done deterministically** (trigger eval,
   contract markers); model-graded confirmation still pending (`TODO.md`).
6. Holdout/holdback scaffolding — **rescoped** (see correction below); two
   fixture-backed tune cases added to the shared benchmark.
7. Account-state collector — **deferred** (needs a live Cloudflare account).

Remaining work lives in [`TODO.md`](../TODO.md).

## Ranking criteria

- **Verifiability**: can a command prove the change works (exit code, diff,
  eval pass rate), or does verification require model judgment, live accounts,
  or network state we do not control?
- **Likelihood of success**: does the change have a clear mechanism for
  improving audit quality, and does it depend on anything outside this repo?

## 1. Stable check IDs + JSON output in the static scanner

- **Verifiability: high.** `--list-checks` and `--json` output are asserted by
  running the scanner; the self-scan must stay at 0 findings; `py_compile`
  must pass.
- **Likelihood of success: high.** The war-story checklist already names the
  check IDs; the scanner already emits the findings. This is plumbing, and it
  is the prerequisite for fixture evals (#2) and the coverage matrix (#3).
- **Risks / downsides:**
  - Renaming or re-mapping IDs later breaks consumers and baselines; IDs are
    a public contract from the first release. Mitigation: registry is the
    single source of truth, version the scanner, never reuse a retired ID.
  - JSON output invites people to treat scanner leads as proof. Mitigation:
    the JSON document and docs keep the "leads, not proof" framing.
  - An unregistered-ID guard that raises at scan time turns a metadata bug
    into a runtime failure. Accepted: failing loudly is better than emitting
    findings that downstream tooling cannot attribute.

## 2. Fixture-based detection evals

- **Verifiability: high.** Each known-bad fixture has an expected-findings
  manifest keyed by check ID; a deterministic runner asserts expected IDs are
  found and (on the clean fixture) that nothing is found.
- **Likelihood of success: high.** Converts the war-story research corpus into
  a regression suite. Detection coverage stops being an untested claim.
- **Risks / downsides:**
  - Fixtures overfit: the scanner can be tuned to pass fixtures while missing
    real-world variants. Mitigation: fixtures are derived from documented war
    stories, not from the scanner's regexes; keep them small and idiomatic.
  - Known-bad fixtures inside the repo pollute the self-scan (this bit us
    before — see lessons-learned). Mitigation: the self-scan excludes
    `evals/fixtures` via the scanner's `--exclude` flag; CI asserts both the
    excluded self-scan and the fixture detections.
  - Clean-fixture false-positive checks can rot as new checks are added.
    Mitigation: the runner fails when the clean fixture trips any check, which
    forces a conscious decision per new check.

## 3. Checklist → scanner coverage matrix

- **Verifiability: high, with a consistency checker.** A script cross-checks
  the matrix against `--list-checks`, so the doc cannot silently drift.
- **Likelihood of success: high.** Makes the research-vs-implementation gap
  visible instead of implicit, and gives contributors a worklist.
- **Risks / downsides:**
  - A matrix without enforcement is worse than none (false confidence).
    Mitigation: the consistency checker runs in CI.
  - "Covered by scanner" can be misread as "fully detected". Mitigation: the
    matrix distinguishes `scanner-lead` from `skill-prompt-only` and
    `not-implemented`; scanner coverage means a heuristic lead exists, not
    proof.

## 4. Link verification + archive fallbacks

- **Verifiability: medium-high.** The checker runs now and produces a report,
  but results depend on network state, bot-blocking, and rate limits.
- **Likelihood of success: high for the goal** (knowing which citations are
  alive, having archive fallbacks), **as long as it never hard-gates CI**.
- **Risks / downsides:**
  - Network-dependent CI is flaky CI. Mitigation: the checker exits 0 unless
    `--strict` is passed; CI does not run it on every push.
  - Bot-blocked domains (Reddit, Medium, HN, LinkedIn) cannot be verified
    automatically; calling them "dead" would prompt bad deletions.
    Mitigation: they are classified `unverifiable-automated` and flagged for
    manual review.
  - Archive links can be fabricated by tooling that guesses URLs. Mitigation:
    only archive URLs that were actually resolved during the run are written
    into the docs; absence is recorded explicitly.
  - Annotations add noise to research files. Accepted: provenance integrity
    is the skill's core promise, so the noise pays for itself.

## 5. SKILL.md reference routing (reduce mandatory context load)

- **Verifiability: medium.** The trigger eval and contract-marker checks still
  pass deterministically, but the real question — do audits stay as good with
  less mandatory reading — needs model-graded evals (#6) to answer.
- **Likelihood of success: medium-high.** Reading ~900 lines of references
  before every audit dilutes context; routing by detected product keeps depth
  where it is relevant.
- **Risks / downsides:**
  - The agent may skip a reference that was actually relevant, missing
    findings. This is the main regression risk of this whole plan.
    Mitigation: the playbook and provenance rules stay mandatory; routing
    rules are explicit ("if Durable Objects detected, read X"); the war-story
    checklist remains mandatory for cost-focused audits.
  - Conditional instructions are harder for models to follow than
    unconditional ones. Mitigation: routing is a short table, not prose.

## 6. Holdout/holdback model-graded eval scaffolding

- **Correction (2026-06-09):** this item was planned on a wrong premise. The
  scaffolding already exists: `evals/shared-benchmark.json` defines 24 cases
  across `tune`/`holdout`/`holdback` splits, and `evals/holdout/` +
  `evals/holdback/` are intentionally gitignored so hidden cases stay out of
  the public repo. "Filling" those directories from an ephemeral session
  would produce unpushable files, so the scope changes to: strengthen the
  visible `tune` split with cases backed by the new detection fixtures, so
  model-graded audit cases and deterministic scanner cases share evidence.
- **Verifiability: low-medium.** Case structure and JSON shape are
  verifiable; grading quality still requires running the external
  skill-eval-harness with a model.
- **Risks / downsides:**
  - Unused eval scaffolding rots and misleads contributors about coverage.
    Mitigation: CI validates JSON shape only; the harness docs state what
    requires a model run.
  - Fixture-backed tune cases are public, so models can memorize them; the
    gitignored holdout/holdback splits remain the contamination guard.

## 7. Account-state collector (collect/eval split) — deferred

- **Verifiability: low.** Requires a live Cloudflare account, API token, and
  plan-dependent API surface. Nothing in this environment can prove it works.
- **Likelihood of success: low right now.** High design risk (token scopes,
  redaction, plan differences) and the skill's safety policy requires explicit
  user approval for authenticated reads.
- **Decision: defer.** Shipping an untested collector that handles API tokens
  is the kind of risk this plan exists to avoid: secrets handling, silent
  partial snapshots presented as complete state, and support burden. The
  design from `research/doctor-patterns-research.md` stands; implementation
  should happen in a session with a real test account.

## Cross-cutting risks

- **CI surface grows.** Every new gate is a new way for unrelated PRs to fail.
  Mitigation: only deterministic, offline checks gate CI (scanner self-scan,
  fixture evals, coverage consistency, JSON shape); network checks are opt-in.
- **More moving parts to keep in sync.** The output contract, eval
  assertions, fixtures, and matrix must move together (lessons-learned #1).
  The consistency checker and fixture runner exist to catch exactly this.
- **Scanner authority creep.** As the scanner gains IDs, JSON, and evals, it
  starts to look like the product. It is still a triage layer; the audit
  workflow with current-docs verification remains the Doctor.
