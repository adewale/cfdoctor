# Public gallery

The gallery has about 10,000 crawlable `/gallery/:slug` pages. The HTML route
does not read a binding, but every rendered page requests twelve transformed
images and one JSON metadata endpoint. No deployed cache rules, request logs,
Images usage, R2 metrics, D1 metrics, or bot controls are supplied.
