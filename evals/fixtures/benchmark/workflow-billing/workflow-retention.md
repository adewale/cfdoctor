Captured 2026-10-18 from the official URL indicated by the document's links. Raw Markdown response follows.

---
description: New Workflows on Workers Paid retain instance state for seven days by default.
title: Default instance retention for new Workflows on Workers Paid is seven days
image: https://developers.cloudflare.com/changelog/post/2026-09-10-paid-retention-default/og.png?v=d9455c8a65eb7d3b
---

[Skip to content](#main-content)

[View RSS feeds](https://developers.cloudflare.com/fundamentals/new-features/available-rss-feeds/) [ Subscribe to RSS](https://developers.cloudflare.com/changelog/rss/index.xml)

[Back to all posts](https://developers.cloudflare.com/changelog)

September 10, 2026

## Default instance retention for new Workflows on Workers Paid is seven days

[Workflows](https://developers.cloudflare.com/workflows/)

Copy as Markdown| [View as Markdown](https://developers.cloudflare.com/changelog/post/2026-09-10-paid-retention-default/index.md)| [Agent setup](https://developers.cloudflare.com/agent-setup/)

[Workflows](https://developers.cloudflare.com/workflows/) created on or after September 10, 2026, on the Workers Paid plan retain completed and errored instance state for seven days by default (previously 30 days). The seven day default helps to reduce storage costs by default. The maximum retention [limit](https://developers.cloudflare.com/workflows/reference/limits/) remains 30 days.

The retention period for existing Workflows is unchanged. The Workers Free plan retains its three-day default and limit.

To set the retention period for a Workflow instance, specify `successRetention`, `errorRetention`, or both:

```js
const instance = await env.MY_WORKFLOW.create({
	retention: {
		successRetention: "2 days",
		errorRetention: "30 days",
	},
});
```

```ts
const instance = await env.MY_WORKFLOW.create({
	retention: {
		successRetention: "2 days",
		errorRetention: "30 days",
	},
});
```

You can also set the retention period per Workflow and per instance in the [Cloudflare dashboard ↗︎](https://dash.cloudflare.com/?to=/:account/workers/workflows).

For retention details, refer to [Workflows pricing](https://developers.cloudflare.com/workflows/reference/pricing/) and the [`WorkflowInstanceCreateOptions` API reference](https://developers.cloudflare.com/workflows/build/workers-api/#workflowinstancecreateoptions).

```json
{"@context":"https://schema.org","@type":"BlogPosting","@id":"https://developers.cloudflare.com/changelog/post/2026-09-10-paid-retention-default/#page","headline":"Default instance retention for new Workflows on Workers Paid is seven days","description":"New Workflows on Workers Paid retain instance state for seven days by default.","url":"https://developers.cloudflare.com/changelog/post/2026-09-10-paid-retention-default/","inLanguage":"en","image":"https://developers.cloudflare.com/changelog/post/2026-09-10-paid-retention-default/og.png?v=d9455c8a65eb7d3b","dateModified":"2026-09-10","datePublished":"2026-09-10","publisher":{"@type":"Organization","name":"Cloudflare","description":"One platform for your apps, agents, and workforce. Build, secure, and scale without managing infrastructure","url":"https://www.cloudflare.com/","sameAs":["https://github.com/cloudflare","https://www.linkedin.com/company/cloudflare","https://x.com/cloudflare"],"logo":{"@type":"ImageObject","url":"https://developers.cloudflare.com/logo.svg"},"address":{"@type":"PostalAddress","streetAddress":"101 Townsend St","addressLocality":"San Francisco","addressRegion":"CA","postalCode":"94107","addressCountry":"US"},"contactPoint":[{"@type":"ContactPoint","contactType":"Customer Support","url":"https://support.cloudflare.com/","availableLanguage":["English"]},{"@type":"ContactPoint","contactType":"Sales","url":"https://www.cloudflare.com/contact/","availableLanguage":["English"]}]},"isPartOf":{"@type":"WebSite","@id":"https://developers.cloudflare.com/#website","name":"Cloudflare Docs","url":"https://developers.cloudflare.com/"}}
```
