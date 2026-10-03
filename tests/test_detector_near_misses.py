"""Near-miss controls for scanner detectors.

Each case is a minimal pair: a positive project that must emit the check and a
near-miss that differs only in the guard the detector relies on, and must not.
The positive half keeps the negative honest: if a detector stopped firing at
all, the near-miss would pass for the wrong reason, so the pair fails instead.
"""

from __future__ import annotations

import json
import unittest

from test_static_scan import scan


def wrangler(**extra: object) -> str:
    config = {
        "name": "near-miss",
        "main": "src/index.js",
        "compatibility_date": "2026-07-01",
        "observability": {"enabled": True},
    }
    config.update(extra)
    return json.dumps(config, indent=2)


def worker(body: str, **config: object) -> dict[str, str]:
    return {"wrangler.jsonc": wrangler(**config), "src/index.js": body}


def durable_object(body: str) -> dict[str, str]:
    return worker(
        'import { DurableObject } from "cloudflare:workers";\n'
        "export class Room extends DurableObject {\n" + body + "\n}\n"
        "export default { async fetch() { return new Response('ok'); } };\n",
        durable_objects={"bindings": [{"name": "ROOM", "class_name": "Room"}]},
        migrations=[{"tag": "v1", "new_sqlite_classes": ["Room"]}],
    )


def check_ids(files: dict[str, str]) -> set[str]:
    return {f["check_id"] for f in scan(files)["findings"]}


# (check id, near-miss description, positive project, near-miss project)
CASES = [
    (
        "CFDOC-COST-CRON-EVERY-MINUTE",
        "a five-minute cron is not every minute",
        worker("export default { scheduled() {} };", triggers={"crons": ["* * * * *"]}),
        worker("export default { scheduled() {} };", triggers={"crons": ["*/5 * * * *"]}),
    ),
    (
        "CFDOC-COST-LOG-VOLUME",
        "10% head sampling is not full sampling",
        worker("export default {};", observability={"enabled": True, "head_sampling_rate": 1}),
        worker("export default {};", observability={"enabled": True, "head_sampling_rate": 0.1}),
    ),
    (
        "CFDOC-COST-WORKERS-CACHE-BILLING",
        "an entrypoint with cache explicitly disabled",
        worker("export default {};", exports={"Api": {"cache": {"enabled": True}}}),
        worker("export default {};", exports={"Api": {"cache": {"enabled": False}}}),
    ),
    (
        "CFDOC-COST-UNBOUNDED-FANOUT",
        "Promise.all fanout through a p-limit concurrency cap",
        worker(
            "export default { async fetch(request) {\n"
            "  const urls = await request.json();\n"
            "  const res = await Promise.all(urls.map((u) => fetch(u)));\n"
            "  return Response.json(res.length);\n"
            "} };\n"
        ),
        worker(
            'import pLimit from "p-limit";\n'
            "const cap = pLimit(4);\n"
            "export default { async fetch(request) {\n"
            "  const urls = await request.json();\n"
            "  const res = await Promise.all(urls.map((u) => cap(() => fetch(u))));\n"
            "  return Response.json(res.length);\n"
            "} };\n"
        ),
    ),
    (
        "CFDOC-COST-RETRY-AMPLIFY",
        "a retry loop with exponential backoff",
        worker(
            "export default { async fetch() {\n"
            "  for (let attempt = 0; attempt < 5; attempt++) {\n"
            '    const res = await fetch("https://upstream.example/api");\n'
            "    if (res.ok) return res;\n"
            "  }\n"
            '  return new Response("upstream failed", { status: 502 });\n'
            "} };\n"
        ),
        worker(
            "export default { async fetch() {\n"
            "  for (let attempt = 0; attempt < 5; attempt++) {\n"
            '    const res = await fetch("https://upstream.example/api");\n'
            "    if (res.ok) return res;\n"
            "    const backoffMs = 2 ** attempt * 100;\n"
            "    await scheduler.wait(backoffMs);\n"
            "  }\n"
            '  return new Response("upstream failed", { status: 502 });\n'
            "} };\n"
        ),
    ),
    (
        "CFDOC-COST-WEBHOOK-NO-IDEMPOTENCY",
        "a webhook that dedupes on the provider delivery id",
        worker(
            "export default { async fetch(request, env) {\n"
            "  const payload = await request.json(); // GitHub webhook\n"
            "  await env.ORDERS.send(payload);\n"
            '  return new Response("ok");\n'
            "} };\n"
        ),
        worker(
            "export default { async fetch(request, env) {\n"
            "  const payload = await request.json(); // GitHub webhook\n"
            '  const deliveryId = request.headers.get("x-github-delivery");\n'
            '  if (await env.SEEN.get(deliveryId)) return new Response("duplicate");\n'
            '  await env.SEEN.put(deliveryId, "1");\n'
            "  await env.ORDERS.send(payload);\n"
            '  return new Response("ok");\n'
            "} };\n"
        ),
    ),
    (
        "CFDOC-COST-KV-LIST-HOTPATH",
        "listing an R2 bucket is not a KV list",
        worker(
            "export default { async fetch(request, env) {\n"
            '  const keys = await env.CACHE.list({ prefix: "user:" });\n'
            "  return Response.json(keys);\n"
            "} };\n",
            kv_namespaces=[{"binding": "CACHE", "id": "abc"}],
            r2_buckets=[{"binding": "FILES", "bucket_name": "files"}],
        ),
        worker(
            "export default { async fetch(request, env) {\n"
            '  const keys = await env.FILES.list({ prefix: "user:" });\n'
            "  return Response.json(keys);\n"
            "} };\n",
            kv_namespaces=[{"binding": "CACHE", "id": "abc"}],
            r2_buckets=[{"binding": "FILES", "bucket_name": "files"}],
        ),
    ),
    (
        "CFDOC-PERF-D1-SELECT-STAR",
        "SELECT COUNT(*) projects one column",
        worker(
            "export default { async fetch(request, env) {\n"
            '  return Response.json(await env.DB.prepare("SELECT * FROM posts WHERE id = ?").bind(1).first());\n'
            "} };\n",
            d1_databases=[{"binding": "DB", "database_name": "app", "database_id": "x"}],
        ),
        worker(
            "export default { async fetch(request, env) {\n"
            '  return Response.json(await env.DB.prepare("SELECT COUNT(*) AS n FROM posts").first());\n'
            "} };\n",
            d1_databases=[{"binding": "DB", "database_name": "app", "database_id": "x"}],
        ),
    ),
    (
        "CFDOC-PERF-D1-N-PLUS-ONE",
        "a handler with one read and one write",
        worker(
            "export default { async fetch(request, env) {\n"
            + "".join(f'  await env.DB.prepare("SELECT id FROM t{i} WHERE id = ?").bind(1).first();\n' for i in range(6))
            + '  return new Response("ok");\n} };\n',
            d1_databases=[{"binding": "DB", "database_name": "app", "database_id": "x"}],
        ),
        worker(
            "export default { async fetch(request, env) {\n"
            '  const row = await env.DB.prepare("SELECT id FROM posts WHERE id = ?").bind(1).first();\n'
            '  await env.DB.prepare("UPDATE posts SET views = views + 1 WHERE id = ?").bind(row.id).run();\n'
            '  return new Response("ok");\n} };\n',
            d1_databases=[{"binding": "DB", "database_name": "app", "database_id": "x"}],
        ),
    ),
    (
        "CFDOC-REL-CROSS-BOUNDARY-RPC-DEAD",
        "a Durable Object exposing only runtime hooks",
        durable_object(
            "  async fetch(request) { return new Response('ok'); }\n"
            "  async resetEverything() { await this.ctx.storage.deleteAll(); }\n"
        ),
        durable_object(
            "  async fetch(request) { return new Response('ok'); }\n"
            "  async webSocketMessage(ws, message) { ws.send(message); }\n"
        ),
    ),
    (
        "DO-SHARDING-HOTSPOT",
        "a per-room key built from a literal prefix",
        worker(
            "export default { async fetch(request, env) {\n"
            '  const stub = env.ROOM.get(env.ROOM.idFromName("global"));\n'
            "  return stub.fetch(request);\n"
            "} };\n"
        ),
        worker(
            "export default { async fetch(request, env) {\n"
            '  const roomId = new URL(request.url).searchParams.get("room");\n'
            '  const stub = env.ROOM.get(env.ROOM.idFromName("room-" + roomId));\n'
            "  return stub.fetch(request);\n"
            "} };\n"
        ),
    ),
    (
        "DO-STORAGE-LIST-HOTPATH",
        "an R2 list inside a Durable Object is not a storage.list",
        durable_object('  async fetch() { return Response.json(await this.ctx.storage.list({ prefix: "msg:" })); }\n'),
        durable_object('  async fetch() { return Response.json(await this.env.FILES.list({ prefix: "msg:" })); }\n'),
    ),
    (
        "DO-ALARM-RECURSION",
        "an alarm that reschedules only while work is pending",
        durable_object(
            "  async alarm() {\n"
            '    await this.ctx.storage.delete("batch");\n'
            "    await this.ctx.storage.setAlarm(Date.now() + 1000);\n"
            "  }\n"
        ),
        durable_object(
            "  async alarm() {\n"
            '    const pending = (await this.ctx.storage.get("pending")) ?? [];\n'
            "    if (pending.length > 0) {\n"
            "      await this.ctx.storage.setAlarm(Date.now() + 1000);\n"
            "    }\n"
            "  }\n"
        ),
    ),
    (
        "DO-STORAGE-BATCHING",
        "one multi-key storage.put call",
        durable_object(
            "  async save(entries) {\n"
            "    for (const [key, value] of entries) {\n"
            "      await this.ctx.storage.put(key, value);\n"
            "    }\n"
            "  }\n"
        ),
        durable_object(
            "  async save(entries) {\n"
            "    await this.ctx.storage.put(Object.fromEntries(entries));\n"
            "  }\n"
        ),
    ),
    (
        "DO-WEBSOCKET-DURATION",
        "a Durable Object that uses the hibernation API",
        durable_object(
            "  async fetch() {\n"
            "    const [client, server] = Object.values(new WebSocketPair());\n"
            "    server.accept();\n"
            "    return new Response(null, { status: 101, webSocket: client });\n"
            "  }\n"
        ),
        durable_object(
            "  async fetch() {\n"
            "    const [client, server] = Object.values(new WebSocketPair());\n"
            "    if (this.legacy) server.accept();\n"
            "    else this.ctx.acceptWebSocket(server);\n"
            "    return new Response(null, { status: 101, webSocket: client });\n"
            "  }\n"
        ),
    ),
    (
        "CFDOC-COST-ASYNC-LOOP",
        "fetching a path on a configured origin, not the incoming URL",
        worker('export default { async fetch(request) { return fetch(new URL("/api", request.url)); } };\n'),
        worker('export default { async fetch(request, env) { return fetch(new URL("/api", env.ORIGIN_URL)); } };\n'),
    ),
]


class DetectorNearMissTests(unittest.TestCase):
    def test_each_detector_fires_on_positive_and_not_on_near_miss(self) -> None:
        for check_id, near_miss, positive, negative in CASES:
            with self.subTest(check_id=check_id, near_miss=near_miss):
                self.assertIn(check_id, check_ids(positive), "positive half no longer fires")
                self.assertNotIn(check_id, check_ids(negative), f"over-fires on {near_miss}")


if __name__ == "__main__":
    unittest.main()
