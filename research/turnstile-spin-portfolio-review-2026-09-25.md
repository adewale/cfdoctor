# Turnstile Spin review of recent `adewale/*` Cloudflare projects

Date: 2026-09-25

## Why

Cloudflare launched Turnstile Spin on 2026-09-25 (https://blog.cloudflare.com/turnstile-spin/). Spin is an agent skill (`cloudflare/skills` `turnstile-spin`) and a dashboard/Wrangler flow. It creates a widget, embeds it, wires canonical server-side Siteverify into the existing backend, and repairs widgets that have no backend validation. This review asked two questions: how the owner's recent Cloudflare projects use Turnstile, and which Spin rules Cloudflare Doctor can check. The contract is recorded as `CFDOC-EVD-CF-TURNSTILE-SPIN`.

## Scope and method

- Scope: every non-fork `adewale/*` repository pushed within the preceding 15 months (51 repositories: 45 public, 6 private), plus recently pushed forks for completeness. 28 non-fork repositories contained a Wrangler config; one more private repository was planning documents only.
- Each repository was shallow-cloned at its default branch. Every Wrangler project was read for widget markers, Siteverify calls, reCAPTCHA/hCaptcha, and every browser-reachable write or spend path together with its existing protection: auth, Access, shared secret, rate-limit binding, in-code limiter, or bot verification.
- Surfaces were judged with the Spin fit rule. Turnstile fits when a human in a browser triggers a write or spend on the app's own backend. It does not fit machine APIs, webhooks, cron/queue work, OAuth callbacks, CLI/TUI/MCP clients, strongly authenticated routes, or static sites with no handler.
- Private repositories contribute aggregate counts only; no private name, path, or value is retained here. Public projects with exploitable open paths are also summarized by pattern, not by name. The owner received the per-project detail directly.
- A survey helper made unrequested read-only Cloudflare account calls: it listed Workers and compared two deployed bundles with their repositories. Nothing was mutated. Future reviews should keep account reads behind explicit approval, as `SKILL.md` requires.

## Observations

These counts describe this repository set only.

- **Existing integrations:** 1 of 28 Wrangler projects (public). It already met most of the Spin contract: backend-only Siteverify, `remoteip`, fail-closed on transport/non-2xx/non-JSON, `success is True`, an exact action check, hostname equality, secrets via `wrangler secret put`, a fresh widget per challenge, and removal after use. The gaps were a missing Siteverify timeout and a missing 2048-character token guard. The hostname check used the request's own host rather than an explicit allowlist, which is equivalent here because the project disables `workers_dev` and preview URLs.
- **App-issued clearance:** the same integration mints a signed clearance cookie after one Siteverify pass that exempts later expensive runs for hours. The signature covers only expiry, and the signing key falls back to the Turnstile secret. No rate-limit binding exists in the repository. One human solve can therefore be replayed by a script for the cookie's lifetime. This became the prompt-only `CFDOC-SEC-TURNSTILE-CLEARANCE-AMPLIFY` guidance.
- **Legacy CAPTCHA:** none. No project used reCAPTCHA or hCaptcha, so migration mode had no target.
- **Strong candidates:** 3 public projects. In each, an anonymous browser action reaches paid or abusable work with no bot, rate, or auth control. The shapes were: a paid third-party image-generation call plus a public KV write; a Browser Run render plus outbound email to an arbitrary address (an open relay); and anonymous creation of permanent multiplayer sessions. In the last case, session creation also runs automatically on page load and is reachable from a non-browser MCP client, so it needs invisible or pre-clearance Turnstile plus a rate limit.
- **Possible:** 8 projects (6 public, 2 private). Their surfaces are GET search that spends Workers AI/Vectorize per query, create/share buttons with small KV costs, room creation shared with a terminal client, pre-auth diagnostics or login GETs that write rows, and one OAuth-gated paid run with an empty allowlist. Several already have a Workers rate-limiting binding. For GET search and non-browser clients, rate limits, caching, or auth are the first control, and Turnstile is at most a second layer.
- **Not a fit:** the rest. They are static sites, machine-to-machine or webhook-driven Workers, owner-only apps behind GitHub OAuth, embeddable third-party iframes, templates, and E2E fixtures.
- **Guidance drift:** a sibling advisory skill's Turnstile sample code checked only a truthy `success`. It had no action or hostname check, no timeout or token guard, no `data-action`, and reused one cached token across submits. It also ran Siteverify before its rate limiter, contradicting its own "WAF → rate limit → Turnstile" ordering.

## Lessons for the scanner and skill

1. **Most value is keeping integrations on-contract.** Only one project had Turnstile, so the lexical leads (`NO-SITEVERIFY`, `CLIENT-SITEVERIFY`, `UNCHECKED-RESULT`, `VERIFY-HARDENING`, `TEST-KEY`, `LEGACY-CAPTCHA`) guard future integrations and sample code. Finding *unprotected* surfaces is semantic work: who calls the endpoint and what it spends. That stays prompt-only as `CFDOC-SEC-TURNSTILE-UNPROTECTED-FORM`, with fit rules in `config-and-security-checks.md`.
2. **Turnstile is not the default answer to abuse.** Half of the plausible surfaces were GET search, page-load side effects, or shared with CLI/TUI/MCP clients. The guidance puts rate limits and caching first there.
3. **Markup and Python must be read.** Widgets live in `.html`, framework components, and templates, and one verifier was a Python Worker. These extensions are read for the Turnstile leads only, so earlier checks keep their coverage.
4. **Saved third-party pages embed other sites' widgets.** A private repository's scraped article attachments produced a widget-without-Siteverify lead and a reCAPTCHA lead. Scraped/archived/vendored paths and `*.min.js` are now ignored for these leads.
5. **Self-scan hygiene applies to regexes.** The scanner's own Siteverify patterns matched their own source text until the patterns were written so their literal text does not match (`siteverif[y]`).
6. **Dummy keys are public values.** Cloudflare's documented test keys were reported as committed credentials by the generic secret-assignment check. Placement is now judged by the Turnstile test-key lead instead.

## Follow-ups outside this repository

These belong to the owning projects and were reported to the owner rather than changed here. Add the Siteverify timeout and token guard to the existing integration, and bind or shorten its clearance cookie behind a rate limit. Gate the three strong candidates with Turnstile Spin plus a rate limit. Align the advisory skill's sample code with the Spin contract.
