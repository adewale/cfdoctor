# Public product catalogue

This SvelteKit application is deployed at `catalog.example.com`. The sitemap
contains only `/` and `/categories`, while the categories page renders product
links. The product route represents about 60,000 public pages. The included
source project uses exact SvelteKit and Cloudflare-adapter versions;
`npm install && npm run build` produces the Wrangler entrypoint at
`.svelte-kit/cloudflare/_worker.js`. Generated output is deliberately not stored
in the benchmark. No deployed traffic, cache rules, Query Insights, WAF, bot
controls, or billing data are included.
