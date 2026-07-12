export default {
  async queue(batch: MessageBatch, env: Env): Promise<void> {
    if (batch.queue === "configured-jobs") await processConfigured(batch, env);
    if (batch.queue === "dashboard-only-jobs") await processDashboardOnly(batch, env);
  },
};
