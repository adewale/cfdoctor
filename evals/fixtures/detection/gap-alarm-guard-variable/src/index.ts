export class Scheduler extends DurableObject {
  async alarm(): Promise<void> {
    const nextRun = Date.now() + 60_000;
    const maxDelay = 60_000;
    console.log({ nextRun, maxDelay });
    await this.ctx.storage.setAlarm(nextRun);
  }
}
