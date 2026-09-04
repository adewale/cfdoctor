import { z } from "zod";

// datadog tools describe their input as plain JSON Schema (what the model
// receives anyway) and build a zod validator only when a call arrives.

export const queryMetrics = {
  name: "datadog.query_metrics",
  description: "datadog query metrics",
  inputSchema: {
    type: "object",
    properties: { account: { type: "string" }, target: { type: "string" }, limit: { type: "integer", minimum: 1, maximum: 100 } },
    required: ["account", "target"],
  },
  validate(input) {
    return z.object({ account: z.string(), target: z.string().min(1), limit: z.number().int().min(1).max(100).default(20) }).parse(input);
  },
  async execute(input, env) {
    return env.PROVIDERS.call("datadog", "query_metrics", this.validate(input));
  },
};

export const listMonitors = {
  name: "datadog.list_monitors",
  description: "datadog list monitors",
  inputSchema: {
    type: "object",
    properties: { account: { type: "string" }, target: { type: "string" }, limit: { type: "integer", minimum: 1, maximum: 100 } },
    required: ["account", "target"],
  },
  validate(input) {
    return z.object({ account: z.string(), target: z.string().min(1), limit: z.number().int().min(1).max(100).default(20) }).parse(input);
  },
  async execute(input, env) {
    return env.PROVIDERS.call("datadog", "list_monitors", this.validate(input));
  },
};
