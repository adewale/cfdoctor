import { z } from "zod";

// Every github tool declares its input schema at module scope (this is how the
// docs do it). Each z.object tree is built when the module evaluates, before any
// thread has asked for the tool.

export const getPullRequest = {
  name: "github.get_pull_request",
  description: "github get pull request",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("github", "get_pull_request", input);
  },
};

export const listPullRequests = {
  name: "github.list_pull_requests",
  description: "github list pull requests",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("github", "list_pull_requests", input);
  },
};

export const getIssue = {
  name: "github.get_issue",
  description: "github get issue",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("github", "get_issue", input);
  },
};

export const createIssueComment = {
  name: "github.create_issue_comment",
  description: "github create issue comment",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("github", "create_issue_comment", input);
  },
};

export const getCommit = {
  name: "github.get_commit",
  description: "github get commit",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("github", "get_commit", input);
  },
};

export const listWorkflowRuns = {
  name: "github.list_workflow_runs",
  description: "github list workflow runs",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("github", "list_workflow_runs", input);
  },
};

export const getWorkflowRunLogs = {
  name: "github.get_workflow_run_logs",
  description: "github get workflow run logs",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("github", "get_workflow_run_logs", input);
  },
};

export const searchCode = {
  name: "github.search_code",
  description: "github search code",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("github", "search_code", input);
  },
};

export const getFileContents = {
  name: "github.get_file_contents",
  description: "github get file contents",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("github", "get_file_contents", input);
  },
};
