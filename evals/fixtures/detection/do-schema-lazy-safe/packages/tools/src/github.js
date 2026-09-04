import { z } from "zod";

// github tools describe their input as plain JSON Schema (what the model
// receives anyway) and build a zod validator only when a call arrives.

export const getPullRequest = {
  name: "github.get_pull_request",
  description: "github get pull request",
  inputSchema: {
    type: "object",
    properties: { account: { type: "string" }, target: { type: "string" }, limit: { type: "integer", minimum: 1, maximum: 100 } },
    required: ["account", "target"],
  },
  validate(input) {
    return z.object({ account: z.string(), target: z.string().min(1), limit: z.number().int().min(1).max(100).default(20) }).parse(input);
  },
  async execute(input, env) {
    return env.PROVIDERS.call("github", "get_pull_request", this.validate(input));
  },
};

export const listPullRequests = {
  name: "github.list_pull_requests",
  description: "github list pull requests",
  inputSchema: {
    type: "object",
    properties: { account: { type: "string" }, target: { type: "string" }, limit: { type: "integer", minimum: 1, maximum: 100 } },
    required: ["account", "target"],
  },
  validate(input) {
    return z.object({ account: z.string(), target: z.string().min(1), limit: z.number().int().min(1).max(100).default(20) }).parse(input);
  },
  async execute(input, env) {
    return env.PROVIDERS.call("github", "list_pull_requests", this.validate(input));
  },
};

export const getIssue = {
  name: "github.get_issue",
  description: "github get issue",
  inputSchema: {
    type: "object",
    properties: { account: { type: "string" }, target: { type: "string" }, limit: { type: "integer", minimum: 1, maximum: 100 } },
    required: ["account", "target"],
  },
  validate(input) {
    return z.object({ account: z.string(), target: z.string().min(1), limit: z.number().int().min(1).max(100).default(20) }).parse(input);
  },
  async execute(input, env) {
    return env.PROVIDERS.call("github", "get_issue", this.validate(input));
  },
};
