import { z } from "zod";

// Every sentry tool declares its input schema at module scope (this is how the
// docs do it). Each z.object tree is built when the module evaluates, before any
// thread has asked for the tool.

export const listIssues = {
  name: "sentry.list_issues",
  description: "sentry list issues",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("sentry", "list_issues", input);
  },
};

export const getIssue = {
  name: "sentry.get_issue",
  description: "sentry get issue",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("sentry", "get_issue", input);
  },
};

export const listEvents = {
  name: "sentry.list_events",
  description: "sentry list events",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("sentry", "list_events", input);
  },
};

export const getEvent = {
  name: "sentry.get_event",
  description: "sentry get event",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("sentry", "get_event", input);
  },
};

export const resolveIssue = {
  name: "sentry.resolve_issue",
  description: "sentry resolve issue",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("sentry", "resolve_issue", input);
  },
};

export const listReleases = {
  name: "sentry.list_releases",
  description: "sentry list releases",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("sentry", "list_releases", input);
  },
};

export const getRelease = {
  name: "sentry.get_release",
  description: "sentry get release",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("sentry", "get_release", input);
  },
};

export const listProjects = {
  name: "sentry.list_projects",
  description: "sentry list projects",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("sentry", "list_projects", input);
  },
};
