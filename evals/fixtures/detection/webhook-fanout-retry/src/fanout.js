import { deliverOnce } from "./deliver.js";

// Deliver the event to every subscriber at the same time.
export async function broadcastEvent(subscribers, event) {
  const body = JSON.stringify(event);
  await Promise.all(subscribers.map((subscriber) => deliverOnce(subscriber.url, body)));
}
