import { z } from "zod";

// Every datadog tool declares its input schema at module scope (this is how the
// docs do it). Each z.object tree is built when the module evaluates, before any
// thread has asked for the tool.

export const queryMetrics = {
  name: "datadog.query_metrics",
  description: "datadog query metrics",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("datadog", "query_metrics", input);
  },
};

export const listMonitors = {
  name: "datadog.list_monitors",
  description: "datadog list monitors",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("datadog", "list_monitors", input);
  },
};

export const getMonitor = {
  name: "datadog.get_monitor",
  description: "datadog get monitor",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("datadog", "get_monitor", input);
  },
};

export const searchLogs = {
  name: "datadog.search_logs",
  description: "datadog search logs",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("datadog", "search_logs", input);
  },
};

export const getTrace = {
  name: "datadog.get_trace",
  description: "datadog get trace",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("datadog", "get_trace", input);
  },
};

export const listDashboards = {
  name: "datadog.list_dashboards",
  description: "datadog list dashboards",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("datadog", "list_dashboards", input);
  },
};

export const getDashboard = {
  name: "datadog.get_dashboard",
  description: "datadog get dashboard",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("datadog", "get_dashboard", input);
  },
};

export const listIncidents = {
  name: "datadog.list_incidents",
  description: "datadog list incidents",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("datadog", "list_incidents", input);
  },
};

export const getIncident = {
  name: "datadog.get_incident",
  description: "datadog get incident",
  parameters: z.object({
    account: z.string().describe("Account or organization identifier"),
    target: z.string().min(1).describe("Resource identifier"),
    limit: z.number().int().min(1).max(100).default(20).describe("Maximum results"),
    cursor: z.string().optional().describe("Pagination cursor"),
  }),
  async execute(input, env) {
    return env.PROVIDERS.call("datadog", "get_incident", input);
  },
};
