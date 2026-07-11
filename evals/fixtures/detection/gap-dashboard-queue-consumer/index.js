export default {
  async queue(batch, env) {
    for (const message of batch.messages) {
      const job = message.body;
      const upstream = await fetch(`https://imports.internal.invalid/jobs/${job.id}`);
      if (!upstream.ok) {
        message.retry();
        continue;
      }
      message.ack();
    }
  },
};
