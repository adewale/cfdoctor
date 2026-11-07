async function processMessage(message) {
  console.log("processed", message.id);
}

export default {
  async queue(batch) {
    for (const message of batch.messages) {
      try {
        await processMessage(message);
        message.ack();
      } catch {
        message.retry({ delaySeconds: 30 });
      }
    }
  },
};
