# Fixture: turnstile-client-siteverify

`public/contact.js` is served as a Workers static asset and calls Siteverify from the
browser; `src/config.ts` reads the secret through a Vite-public `VITE_` variable that is
inlined into the client bundle. Cloudflare's server-side validation docs require the
backend to be the sole Siteverify caller (evidence `CFDOC-EVD-CF-TURNSTILE-SPIN`).

Expected: `CFDOC-SEC-TURNSTILE-CLIENT-SITEVERIFY` for both files. The missing-Siteverify
and unchecked-result leads must stay quiet because the only Siteverify call is the
browser-side one already reported.

This is intentionally bad code, committed only as a detection eval fixture. Do not copy it.
