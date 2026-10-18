Captured 2026-10-18 from the official URL indicated by the document's links. Raw Markdown response follows.

---
description: Cloudflare Workflows adds per-step pricing, with step and storage billing starting no earlier than August 10, 2026.
title: Workflows pricing adds per-step billing. Step and storage billing to start no earlier than August 10, 2026.
image: https://developers.cloudflare.com/changelog/post/2026-07-07-workflows-billing-updates/og.png?v=b18ad5a4324986aa
---

[Skip to content](#main-content)

[View RSS feeds](https://developers.cloudflare.com/fundamentals/new-features/available-rss-feeds/) [ Subscribe to RSS](https://developers.cloudflare.com/changelog/rss/index.xml)

[Back to all posts](https://developers.cloudflare.com/changelog)

July 7, 2026

## Workflows pricing adds per-step billing. Step and storage billing to start no earlier than August 10, 2026.

[Workflows](https://developers.cloudflare.com/workflows/)

Copy as Markdown| [View as Markdown](https://developers.cloudflare.com/changelog/post/2026-07-07-workflows-billing-updates/index.md)| [Agent setup](https://developers.cloudflare.com/agent-setup/)

[Workflows](https://developers.cloudflare.com/workflows/) pricing now includes per-step billing. Requests and CPU time billing have been enabled since the initial public beta and is not changing.

#### Workflows adds step billing

A step is each unit of work executed by a Workflow, including step operations such as [sleeping](https://developers.cloudflare.com/workflows/build/sleeping-and-retrying/) or [waiting for events](https://developers.cloudflare.com/workflows/build/events-and-parameters/).

You can query Workflows analytics, including `stepCount` for a Workflow instance, with the [GraphQL Analytics API](https://developers.cloudflare.com/workflows/observability/metrics-analytics/#query-via-the-graphql-api).

#### Steps and storage billing to take effect August 10th, 2026

Starting no earlier than August 10th, 2026, Cloudflare will begin billing for step and storage usage on Workers Paid plans.

Storage pricing has been published since Workflows became generally available and is not changing. Storage is measured as persisted Workflow state in GB-months.

| Dimension | Workers Free | Workers Paid |
| --- | --- | --- |
| Steps | 3,000 included per day | 500,000 included per month, then $0.80 per additional 100,000 steps |
| Storage | 1 GB-month included | 1 GB-month included, then $0.20 per additional GB-month |

Developers on the Workers Free plan will not be charged for steps or storage beyond the included amounts.

Cloudflare will not bill step and storage usage before August 10, 2026.

You can review Workflows usage in the [Cloudflare dashboard ↗︎](https://dash.cloudflare.com/) before this change takes effect. To reduce costs, consider reducing the number of steps per Workflow or improving the memory efficiency of your stored state.

Refer to the [Workflows pricing](https://developers.cloudflare.com/workflows/reference/pricing/) page for full details.

```json
{"@context":"https://schema.org","@type":"BlogPosting","@id":"https://developers.cloudflare.com/changelog/post/2026-07-07-workflows-billing-updates/#page","headline":"Workflows pricing adds per-step billing. Step and storage billing to start no earlier than August 10, 2026.","description":"Cloudflare Workflows adds per-step pricing, with step and storage billing starting no earlier than August 10, 2026.","url":"https://developers.cloudflare.com/changelog/post/2026-07-07-workflows-billing-updates/","inLanguage":"en","image":"https://developers.cloudflare.com/changelog/post/2026-07-07-workflows-billing-updates/og.png?v=b18ad5a4324986aa","dateModified":"2026-07-07","datePublished":"2026-07-07","publisher":{"@type":"Organization","name":"Cloudflare","description":"One platform for your apps, agents, and workforce. Build, secure, and scale without managing infrastructure","url":"https://www.cloudflare.com/","sameAs":["https://github.com/cloudflare","https://www.linkedin.com/company/cloudflare","https://x.com/cloudflare"],"logo":{"@type":"ImageObject","url":"https://developers.cloudflare.com/logo.svg"},"address":{"@type":"PostalAddress","streetAddress":"101 Townsend St","addressLocality":"San Francisco","addressRegion":"CA","postalCode":"94107","addressCountry":"US"},"contactPoint":[{"@type":"ContactPoint","contactType":"Customer Support","url":"https://support.cloudflare.com/","availableLanguage":["English"]},{"@type":"ContactPoint","contactType":"Sales","url":"https://www.cloudflare.com/contact/","availableLanguage":["English"]}]},"isPartOf":{"@type":"WebSite","@id":"https://developers.cloudflare.com/#website","name":"Cloudflare Docs","url":"https://developers.cloudflare.com/"}}
```
