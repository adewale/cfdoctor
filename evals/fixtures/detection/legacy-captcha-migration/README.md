# Fixture: legacy-captcha-migration

A contact form protected by reCAPTCHA v2: the Google widget script, a `g-recaptcha` div,
and a Worker that redeems `g-recaptcha-response` at Google's siteverify. These are the
detection signals Turnstile Spin uses to switch into migration mode (evidence
`CFDOC-EVD-CF-TURNSTILE-SPIN`).

Expected: exactly one low-severity `CFDOC-FIT-LEGACY-CAPTCHA` lead. The integration works;
the lead is a product-fit suggestion, not a vulnerability.
