# Fixture: turnstile-widget-no-siteverify

Models the incomplete Turnstile setup that the Turnstile Spin skill's widget-recovery mode
repairs (evidence `CFDOC-EVD-CF-TURNSTILE-SPIN`). `public/index.html` renders a Turnstile
widget, but `src/index.js` only checks that a `cf-turnstile-response` field is present
before writing to KV. It never calls Siteverify, so a bot can post any string as the
token. Cloudflare's server-side validation docs state that the widget alone does not
protect a form.

Expected: `CFDOC-SEC-TURNSTILE-NO-SITEVERIFY` and nothing else.

This is intentionally bad code, committed only as a detection eval fixture for
`skills/cloudflare-doctor/scripts/cfdoctor_static_scan.py`. Do not copy it into a real project.
