# Catalogue host controls

The production custom domain `catalog.example.com` has supplied cache and WAF
coverage for `/product/*`. The same Worker also has its `workers.dev` hostname
enabled. The attached control export says that hostname is outside those zone
rules. Product routes represent about 60,000 public pages. No request counts,
D1 metrics, or billing export are supplied.
