from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCANNER = ROOT / "skills/cloudflare-doctor/scripts/cfdoctor_static_scan.py"


def scan(files: dict[str, str]) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for name, content in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SCANNER), str(root), "--json"],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(proc.stdout)


class StaticScannerTests(unittest.TestCase):
    def test_valid_jsonc_comments_and_trailing_commas_are_parsed(self) -> None:
        report = scan({
            "wrangler.jsonc": '''{
              // comment with }, and // inside it
              "name": "trailing-comma-test",
              "compatibility_date": "2026-07-01",
              "observability": {"enabled": true,},
              "routes": ["*/*",],
              "vars": {"URL": "https://example.com/a,//b",},
            }''',
            "src/index.js": "export default { fetch() { return new Response('ok') } }",
        })
        ids = {f["check_id"] for f in report["findings"]}
        self.assertIn("CFDOC-COST-BROAD-ROUTE", ids)
        self.assertNotIn("CFDOC-CONFIG-UNPARSEABLE", ids)
        self.assertIn("Workers", report["detected_products"])

    def test_modern_wrangler_products_are_inventoried(self) -> None:
        report = scan({
            "wrangler.jsonc": '''{
              "name": "modern-bindings",
              "main": "src/index.js",
              "compatibility_date": "2026-07-01",
              "assets": {"directory": "public", "binding": "ASSETS"},
              "containers": [{"class_name": "Sandbox"}],
              "dispatch_namespaces": [{"binding": "DISPATCH", "namespace": "tenant-workers"}],
              "pipelines": [{"binding": "PIPELINE", "pipeline": "events"}],
              "ratelimits": [{"name": "RATE_LIMITER", "namespace_id": "1"}],
              "secrets_store_secrets": [{"binding": "API_TOKEN", "store_id": "store", "secret_name": "token"}],
              "send_email": [{"name": "EMAIL"}],
              "vpc_services": [{"binding": "VPC", "service_id": "service"}]
            }''',
            "src/index.js": "export default { fetch() { return new Response('ok') } }",
        })
        self.assertTrue({
            "Containers",
            "Dynamic Workers",
            "Email bindings",
            "Pipelines",
            "Rate Limiting bindings",
            "Secrets Store",
            "Workers Static Assets",
            "Workers VPC",
        }.issubset(report["detected_products"]))

    def test_generated_corpus_cache_is_excluded_from_repository_scan(self) -> None:
        report = scan({
            "wrangler.jsonc": '{"name":"app","main":"src/index.js","compatibility_date":"2026-07-01"}',
            "src/index.js": "export default { fetch() { return new Response('ok') } }",
            "corpus-cache/copied/wrangler.jsonc": '{"name":"copy","compatibility_date":"2099-01-01","routes":["*/*"]}',
        })
        ids = {finding["check_id"] for finding in report["findings"]}
        self.assertNotIn("CFDOC-CONFIG-COMPAT-DATE-FUTURE", ids)
        self.assertNotIn("CFDOC-COST-BROAD-ROUTE", ids)

    def test_malformed_jsonc_always_reports_parse_error(self) -> None:
        report = scan({
            "wrangler.jsonc": '''{
              "name": "broken",
              "compatibility_date": "2026-07-01",
              "routes": ["example.com/*",,]
            }''',
        })
        findings = [f for f in report["findings"] if f["check_id"] == "CFDOC-CONFIG-UNPARSEABLE"]
        self.assertEqual(1, len(findings))
        self.assertIn("line", findings[0]["evidence"].lower())

    def test_unterminated_block_comment_is_rejected(self) -> None:
        report = scan({"wrangler.jsonc": '{"compatibility_date":"2026-07-01"} /* unterminated'})
        finding = next(f for f in report["findings"] if f["check_id"] == "CFDOC-CONFIG-UNPARSEABLE")
        self.assertIn("unterminated block comment", finding["evidence"])

    def test_valid_empty_config_is_not_called_unparseable(self) -> None:
        report = scan({"wrangler.json": "{}"})
        ids = {f["check_id"] for f in report["findings"]}
        self.assertNotIn("CFDOC-CONFIG-UNPARSEABLE", ids)
        self.assertIn("CFDOC-CONFIG-NO-COMPAT-DATE", ids)

    def test_queue_default_is_bounded_and_missing_dlq_means_deletion(self) -> None:
        report = scan({
            "wrangler.jsonc": '''{
              "name": "queue-test",
              "compatibility_date": "2026-07-01",
              "observability": {"enabled": true},
              "queues": {"consumers": [{"queue": "jobs"}]}
            }''',
        })
        finding = next(f for f in report["findings"] if f["check_id"] == "CFDOC-REL-QUEUE-NO-DLQ")
        combined = " ".join([finding["title"], finding["message"], finding["fix"]]).lower()
        self.assertIn("three times", combined)
        self.assertIn("permanently deleted", combined)
        self.assertNotIn("unbounded", combined)

    def test_empty_dlq_value_does_not_suppress_lead(self) -> None:
        report = scan({
            "wrangler.jsonc": '''{
              "name": "queue-empty-dlq",
              "compatibility_date": "2026-07-01",
              "observability": {"enabled": true},
              "queues": {"consumers": [{"queue": "jobs", "dead_letter_queue": ""}]}
            }''',
        })
        self.assertIn("CFDOC-REL-QUEUE-NO-DLQ", {f["check_id"] for f in report["findings"]})

    def test_explicit_dlq_suppresses_missing_dlq_lead(self) -> None:
        report = scan({
            "wrangler.jsonc": '''{
              "name": "queue-safe",
              "compatibility_date": "2026-07-01",
              "observability": {"enabled": true},
              "queues": {"consumers": [{"queue": "jobs", "dead_letter_queue": "jobs-dlq"}]}
            }''',
        })
        self.assertNotIn("CFDOC-REL-QUEUE-NO-DLQ", {f["check_id"] for f in report["findings"]})

    def test_d1_select_star_is_not_reported_as_proven_rows_read_cost(self) -> None:
        report = scan({
            "wrangler.jsonc": '''{
              "name": "d1-test",
              "compatibility_date": "2026-07-01",
              "observability": {"enabled": true},
              "d1_databases": [{"binding": "DB", "database_name": "db", "database_id": "x"}]
            }''',
            "migrations/0001.sql": "CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT);",
            "src/index.js": "env.DB.prepare('SELECT * FROM users WHERE id = ? LIMIT 1').bind(id)",
        })
        finding = next(f for f in report["findings"] if f["check_id"] == "CFDOC-PERF-D1-SELECT-STAR")
        self.assertEqual("low", finding["severity"])
        self.assertIn("does not by itself prove", finding["message"])

    def test_do_batching_lead_distinguishes_batching_from_coalescing(self) -> None:
        puts = "\n".join(f"await this.ctx.storage.put('k{i}', value);" for i in range(4))
        report = scan({
            "wrangler.jsonc": '''{
              "name": "do-test",
              "compatibility_date": "2026-07-01",
              "observability": {"enabled": true}
            }''',
            "src/object.js": f"class Room extends DurableObject {{ async save() {{ {puts} }} }}",
        })
        finding = next(f for f in report["findings"] if f["check_id"] == "DO-STORAGE-BATCHING")
        self.assertEqual("low", finding["severity"])
        self.assertIn("batching alone is not a proven billing reduction", finding["message"])
        self.assertIn("coalesce redundant writes", finding["fix"].lower())

    def secret_assignment_ids(self, report: dict) -> list[str]:
        return [f["check_id"] for f in report["findings"] if f["check_id"] == "CFDOC-SEC-SECRET-ASSIGNMENT"]

    def test_secret_named_reference_in_code_is_not_a_committed_credential(self) -> None:
        report = scan({
            "src/index.js": "\n".join([
                'const token = form.get("cf-turnstile-response");',
                "const apiKey = env.SERVICE_API_KEY;",
                "const password = await getPassword();",
                "const clientSecret = this.config.clientSecret;",
            ]),
            "main.tf": 'provider "cloudflare" {\n  api_token = var.cloudflare_api_token\n}',
        })
        self.assertEqual([], self.secret_assignment_ids(report))

    def test_secret_literal_in_code_is_still_reported(self) -> None:
        report = scan({"src/index.js": 'const apiKey = "live-9f8a7b6c5d4e3f21";'})
        self.assertEqual(["CFDOC-SEC-SECRET-ASSIGNMENT"], self.secret_assignment_ids(report))

    def test_unquoted_secret_literal_outside_code_is_still_reported(self) -> None:
        report = scan({".env": "API_KEY=9f8a7b6c5d4e3f21abcd\n"})
        self.assertEqual(["CFDOC-SEC-SECRET-ASSIGNMENT"], self.secret_assignment_ids(report))

    TWO_DO_CONFIG = """{
      "name": "two-do-app",
      "main": "src/index.js",
      "compatibility_date": "2026-07-01",
      "observability": {"enabled": true, "head_sampling_rate": 0.05},
      "durable_objects": {"bindings": [
        {"name": "COORDINATOR", "class_name": "Coordinator"},
        {"name": "RUNNER", "class_name": "TaskRunner"}
      ]},
      "migrations": [{"tag": "v1", "new_sqlite_classes": ["Coordinator", "TaskRunner"]}]
    }"""

    def test_do_stub_call_cycle_between_two_classes_is_reported(self) -> None:
        report = scan({
            "wrangler.jsonc": self.TWO_DO_CONFIG,
            "src/index.js": "\n".join([
                "export class Coordinator {",
                "  constructor(ctx, env) { this.ctx = ctx; this.env = env; }",
                "  async fetch(request) {",
                "    const auth = request.headers.get('authorization');",
                "    const id = this.env.RUNNER.idFromName(auth);",
                "    this.ctx.waitUntil(this.env.RUNNER.get(id).fetch('https://do/run'));",
                "    return new Response('ok');",
                "  }",
                "}",
                "export class TaskRunner {",
                "  constructor(ctx, env) { this.ctx = ctx; this.env = env; }",
                "  async fetch(request) {",
                "    const auth = request.headers.get('authorization');",
                "    const id = this.env.COORDINATOR.idFromName(auth);",
                "    this.ctx.waitUntil(this.env.COORDINATOR.get(id).fetch('https://do/notify'));",
                "    return new Response('done');",
                "  }",
                "}",
            ]),
        })
        cycle = [f for f in report["findings"] if f["check_id"] == "DO-STUB-CALL-CYCLE"]
        self.assertEqual(1, len(cycle))
        self.assertIn("Coordinator -> TaskRunner -> Coordinator", cycle[0]["evidence"])

    def test_do_stub_chain_without_cycle_is_not_reported(self) -> None:
        report = scan({
            "wrangler.jsonc": self.TWO_DO_CONFIG,
            "src/index.js": "\n".join([
                "export class Coordinator {",
                "  constructor(ctx, env) { this.ctx = ctx; this.env = env; }",
                "  async fetch(request) {",
                "    const auth = request.headers.get('authorization');",
                "    const id = this.env.RUNNER.idFromName(auth);",
                "    await this.env.RUNNER.get(id).fetch('https://do/run');",
                "    return new Response('ok');",
                "  }",
                "}",
                "export class TaskRunner {",
                "  constructor(ctx, env) { this.ctx = ctx; this.env = env; }",
                "  async fetch(request) { return new Response('done'); }",
                "}",
            ]),
        })
        ids = {f["check_id"] for f in report["findings"]}
        self.assertNotIn("DO-STUB-CALL-CYCLE", ids)

    def test_do_stub_cycle_with_unpropagated_depth_guard_is_reported(self) -> None:
        report = scan({
            "wrangler.jsonc": self.TWO_DO_CONFIG,
            "src/index.js": "\n".join([
                "export class Coordinator {",
                "  constructor(ctx, env) { this.ctx = ctx; this.env = env; }",
                "  async fetch(request) {",
                "    const auth = request.headers.get('authorization');",
                "    const depth = Number(request.headers.get('x-hop-depth') || 0);",
                "    if (depth >= 3) return new Response('depth limit', { status: 429 });",
                "    const id = this.env.RUNNER.idFromName(auth);",
                "    await this.env.RUNNER.get(id).fetch('https://do/run');",
                "    return new Response('ok');",
                "  }",
                "}",
                "export class TaskRunner {",
                "  constructor(ctx, env) { this.ctx = ctx; this.env = env; }",
                "  async fetch(request) {",
                "    const auth = request.headers.get('authorization');",
                "    const depth = Number(request.headers.get('x-hop-depth') || 0);",
                "    if (depth >= 3) return new Response('depth limit', { status: 429 });",
                "    const id = this.env.COORDINATOR.idFromName(auth);",
                "    await this.env.COORDINATOR.get(id).fetch('https://do/notify');",
                "    return new Response('done');",
                "  }",
                "}",
            ]),
        })
        ids = {f["check_id"] for f in report["findings"]}
        self.assertIn("DO-STUB-CALL-CYCLE", ids)

    def test_do_stub_cycle_is_not_suppressed_by_guard_in_another_method(self) -> None:
        report = scan({
            "wrangler.jsonc": self.TWO_DO_CONFIG,
            "src/index.js": "\n".join([
                "export class Coordinator {",
                "  constructor(ctx, env) { this.env = env; }",
                "  validate(depth) { if (depth >= 3) return false; return true; }",
                "  fetch(request) {",
                "    const depth = Number(request.headers.get('x-hop-depth') || 0);",
                "    return this.env.RUNNER.getByName('runner').fetch('https://do/run', {",
                "      headers: { 'x-hop-depth': String(depth + 1) },",
                "    });",
                "  }",
                "}",
                "export class TaskRunner {",
                "  constructor(ctx, env) { this.env = env; }",
                "  validate(depth) { if (depth >= 3) return false; return true; }",
                "  fetch(request) {",
                "    const depth = Number(request.headers.get('x-hop-depth') || 0);",
                "    return this.env.COORDINATOR.getByName('coordinator').fetch('https://do/back', {",
                "      headers: { 'x-hop-depth': String(depth + 1) },",
                "    });",
                "  }",
                "}",
            ]),
        })
        ids = {f["check_id"] for f in report["findings"]}
        self.assertIn("DO-STUB-CALL-CYCLE", ids)

    def test_do_stub_cycle_with_terminating_propagated_depth_guard_is_suppressed(self) -> None:
        report = scan({
            "wrangler.jsonc": self.TWO_DO_CONFIG,
            "src/index.js": "\n".join([
                "export class Coordinator {",
                "  constructor(ctx, env) { this.ctx = ctx; this.env = env; }",
                "  async fetch(request) {",
                "    const auth = request.headers.get('authorization');",
                "    const depth = Number(request.headers.get('x-hop-depth') || 0);",
                "    if (depth >= 3) return new Response('depth limit', { status: 429 });",
                "    const id = this.env.RUNNER.idFromName(auth);",
                "    return this.env.RUNNER.get(id).fetch('https://do/run', {",
                "      headers: { 'x-hop-depth': String(depth + 1), authorization: auth },",
                "    });",
                "  }",
                "}",
                "export class TaskRunner {",
                "  constructor(ctx, env) { this.ctx = ctx; this.env = env; }",
                "  async fetch(request) {",
                "    const auth = request.headers.get('authorization');",
                "    const depth = Number(request.headers.get('x-hop-depth') || 0);",
                "    if (depth >= 3) return new Response('depth limit', { status: 429 });",
                "    const id = this.env.COORDINATOR.idFromName(auth);",
                "    return this.env.COORDINATOR.get(id).fetch('https://do/notify', {",
                "      headers: { 'x-hop-depth': String(depth + 1), authorization: auth },",
                "    });",
                "  }",
                "}",
            ]),
        })
        ids = {f["check_id"] for f in report["findings"]}
        self.assertNotIn("DO-STUB-CALL-CYCLE", ids)

    def test_do_binding_id_or_stub_construction_without_invocation_is_not_a_cycle(self) -> None:
        report = scan({
            "wrangler.jsonc": self.TWO_DO_CONFIG,
            "src/index.js": "\n".join([
                "export class Coordinator {",
                "  constructor(ctx, env) { this.env = env; }",
                "  fetch() {",
                "    const runnerId = this.env.RUNNER.idFromName('reference-only');",
                "    const runner = this.env.RUNNER.get(runnerId);",
                "    return Response.json({ runner: runner.id.toString() });",
                "  }",
                "}",
                "export class TaskRunner {",
                "  constructor(ctx, env) { this.env = env; }",
                "  fetch() {",
                "    const coordinatorId = this.env.COORDINATOR.idFromName('reference-only');",
                "    const coordinator = this.env.COORDINATOR.get(coordinatorId);",
                "    return Response.json({ coordinator: coordinator.id.toString() });",
                "  }",
                "}",
            ]),
        })
        ids = {f["check_id"] for f in report["findings"]}
        self.assertNotIn("DO-STUB-CALL-CYCLE", ids)

    def test_do_stub_rpc_cycle_through_local_variables_is_reported(self) -> None:
        report = scan({
            "wrangler.jsonc": self.TWO_DO_CONFIG,
            "src/index.js": """
              export class Coordinator {
                constructor(ctx, env) { this.env = env; }
                run() {
                  const runner = this.env.RUNNER.getByName('runner')
                  return runner.runTask();
                }
              }
              export class TaskRunner {
                constructor(ctx, env) { this.env = env; }
                notify() {
                  const coordinator = this.env.COORDINATOR.getByName('coordinator');
                  return coordinator.notify();
                }
              }
            """,
        })
        cycle = [f for f in report["findings"] if f["check_id"] == "DO-STUB-CALL-CYCLE"]
        self.assertEqual(1, len(cycle))

    def test_worker_entrypoint_after_do_class_is_not_attributed_to_class(self) -> None:
        report = scan({
            "wrangler.jsonc": """{
              "name": "entrypoint-and-do",
              "main": "src/index.js",
              "compatibility_date": "2026-07-01",
              "durable_objects": {"bindings": [{"name": "ROOM", "class_name": "Room"}]},
              "migrations": [{"tag": "v1", "new_sqlite_classes": ["Room"]}]
            }""",
            "src/index.js": "\n".join([
                "export class Room {",
                "  fetch() { return new Response('room'); }",
                "}",
                "export default {",
                "  async fetch(request, env) {",
                "    const id = env.ROOM.idFromName('main');",
                "    return env.ROOM.get(id).fetch(request);",
                "  },",
                "};",
            ]),
        })
        ids = {f["check_id"] for f in report["findings"]}
        self.assertNotIn("DO-STUB-CALL-CYCLE", ids)

    def test_helper_and_dynamic_binding_indirection_are_explicit_cycle_boundaries(self) -> None:
        report = scan({
            "wrangler.jsonc": self.TWO_DO_CONFIG,
            "src/index.js": """
              async function invoke(namespace, name) {
                return namespace.getByName(name).fetch('https://do/next');
              }
              export class Coordinator {
                constructor(ctx, env) { this.env = env; }
                fetch() { return invoke(this.env.RUNNER, 'runner'); }
              }
              export class TaskRunner {
                constructor(ctx, env) { this.env = env; }
                fetch() {
                  const binding = 'COORDINATOR';
                  return this.env[binding].getByName('coordinator').fetch('https://do/back');
                }
              }
            """,
        })
        ids = {f["check_id"] for f in report["findings"]}
        self.assertNotIn("DO-STUB-CALL-CYCLE", ids)

    def test_queue_and_service_binding_hops_are_not_do_stub_edges(self) -> None:
        report = scan({
            "wrangler.jsonc": """{
              "name": "composed-loop-shape",
              "main": "src/index.js",
              "compatibility_date": "2026-07-01",
              "durable_objects": {"bindings": [
                {"name": "COORDINATOR", "class_name": "Coordinator"}
              ]},
              "queues": {"producers": [{"binding": "JOBS", "queue": "jobs"}]},
              "services": [{"binding": "ROUTER", "service": "router-worker"}],
              "migrations": [{"tag": "v1", "new_sqlite_classes": ["Coordinator"]}]
            }""",
            "src/index.js": """
              export class Coordinator {
                constructor(ctx, env) { this.env = env; }
                async fetch(request) {
                  await this.env.JOBS.send({ id: request.url });
                  return this.env.ROUTER.fetch(request);
                }
              }
              export default {
                async queue(batch, env) {
                  return env.COORDINATOR.getByName('main').fetch('https://do/resume');
                }
              };
            """,
        })
        ids = {f["check_id"] for f in report["findings"]}
        self.assertNotIn("DO-STUB-CALL-CYCLE", ids)

    def test_do_self_stub_call_is_reported_as_cycle(self) -> None:
        report = scan({
            "wrangler.jsonc": """{
              "name": "self-do-app",
              "main": "src/index.js",
              "compatibility_date": "2026-07-01",
              "observability": {"enabled": true, "head_sampling_rate": 0.05},
              "durable_objects": {"bindings": [{"name": "SELF_DO", "class_name": "Looper"}]},
              "migrations": [{"tag": "v1", "new_sqlite_classes": ["Looper"]}]
            }""",
            "src/index.js": "\n".join([
                "export class Looper {",
                "  constructor(ctx, env) { this.ctx = ctx; this.env = env; }",
                "  async fetch(request) {",
                "    const auth = request.headers.get('authorization');",
                "    const id = this.env.SELF_DO.idFromName(auth);",
                "    this.ctx.waitUntil(this.env.SELF_DO.get(id).fetch('https://do/again'));",
                "    return new Response('ok');",
                "  }",
                "}",
            ]),
        })
        cycle = [f for f in report["findings"] if f["check_id"] == "DO-STUB-CALL-CYCLE"]
        self.assertEqual(1, len(cycle))
        self.assertIn("Looper -> Looper", cycle[0]["evidence"])

    THREE_DO_CONFIG = """{
      "name": "three-do-ring",
      "main": "src/index.js",
      "compatibility_date": "2026-07-01",
      "observability": {"enabled": true, "head_sampling_rate": 0.05},
      "durable_objects": {"bindings": [
        {"name": "STAGE_A", "class_name": "StageA"},
        {"name": "STAGE_B", "class_name": "StageB"},
        {"name": "STAGE_C", "class_name": "StageC"}
      ]},
      "migrations": [{"tag": "v1", "new_sqlite_classes": ["StageA", "StageB", "StageC"]}]
    }"""

    @staticmethod
    def ring_stage(class_name: str, next_binding: str, guarded: bool) -> str:
        guard = [
            "    const depth = Number(request.headers.get('x-hop-depth') || 0);",
            "    if (depth >= 3) return new Response('hop limit reached', { status: 429 });",
        ] if guarded else []
        call = (
            f"    this.ctx.waitUntil(this.env.{next_binding}.get(id).fetch('https://do/next', "
            "{ headers: { 'x-hop-depth': String(depth + 1) } }));"
            if guarded
            else f"    this.ctx.waitUntil(this.env.{next_binding}.get(id).fetch('https://do/next'));"
        )
        return "\n".join([
            f"export class {class_name} {{",
            "  constructor(ctx, env) { this.ctx = ctx; this.env = env; }",
            "  async fetch(request) {",
            "    const auth = request.headers.get('authorization');",
            *guard,
            f"    const id = this.env.{next_binding}.idFromName(auth);",
            call,
            f"    return new Response('{class_name}');",
            "  }",
            "}",
        ])

    def test_do_stub_cycle_through_three_classes_is_reported_with_full_path(self) -> None:
        report = scan({
            "wrangler.jsonc": self.THREE_DO_CONFIG,
            "src/index.js": "\n".join([
                self.ring_stage("StageA", "STAGE_B", guarded=False),
                self.ring_stage("StageB", "STAGE_C", guarded=False),
                self.ring_stage("StageC", "STAGE_A", guarded=False),
            ]),
        })
        cycle = [f for f in report["findings"] if f["check_id"] == "DO-STUB-CALL-CYCLE"]
        self.assertEqual(1, len(cycle))
        self.assertIn("StageA -> StageB -> StageC -> StageA", cycle[0]["evidence"])

    def test_do_stub_three_class_cycle_with_one_unguarded_class_still_fires(self) -> None:
        report = scan({
            "wrangler.jsonc": self.THREE_DO_CONFIG,
            "src/index.js": "\n".join([
                self.ring_stage("StageA", "STAGE_B", guarded=True),
                self.ring_stage("StageB", "STAGE_C", guarded=True),
                self.ring_stage("StageC", "STAGE_A", guarded=False),
            ]),
        })
        cycle = [f for f in report["findings"] if f["check_id"] == "DO-STUB-CALL-CYCLE"]
        self.assertEqual(1, len(cycle))

    def test_do_stub_cycle_through_ten_classes_is_reported(self) -> None:
        count = 10
        bindings = [
            {"name": f"STAGE_{index}", "class_name": f"Stage{index}"}
            for index in range(count)
        ]
        config = {
            "name": "ten-do-ring",
            "main": "src/index.js",
            "compatibility_date": "2026-07-01",
            "durable_objects": {"bindings": bindings},
            "migrations": [{"tag": "v1", "new_sqlite_classes": [item["class_name"] for item in bindings]}],
        }
        source = "\n".join(
            self.ring_stage(f"Stage{index}", f"STAGE_{(index + 1) % count}", guarded=False)
            for index in range(count)
        )
        report = scan({"wrangler.jsonc": json.dumps(config), "src/index.js": source})
        cycle = [f for f in report["findings"] if f["check_id"] == "DO-STUB-CALL-CYCLE"]
        self.assertEqual(1, len(cycle))
        self.assertIn("Stage0 -> Stage1 -> Stage2", cycle[0]["evidence"])

    def test_do_cycles_are_scoped_per_wrangler_project(self) -> None:
        report = scan({
            "worker-one/wrangler.jsonc": """{
              "name": "worker-one",
              "main": "src/index.js",
              "compatibility_date": "2026-07-01",
              "durable_objects": {"bindings": [
                {"name": "SELF_A", "class_name": "A"},
                {"name": "TO_B", "class_name": "B"}
              ]},
              "migrations": [{"tag": "v1", "new_sqlite_classes": ["A", "B"]}]
            }""",
            "worker-one/src/index.js": """
              export class A { constructor(ctx, env) { this.env = env; } async fetch() {
                const id = this.env.TO_B.idFromName('x');
                return this.env.TO_B.get(id).fetch('https://do/b');
              }}
              export class B { fetch() { return new Response('done'); } }
            """,
            "worker-two/wrangler.jsonc": """{
              "name": "worker-two",
              "main": "src/index.js",
              "compatibility_date": "2026-07-01",
              "durable_objects": {"bindings": [
                {"name": "SELF_B", "class_name": "B"},
                {"name": "TO_A", "class_name": "A"}
              ]},
              "migrations": [{"tag": "v1", "new_sqlite_classes": ["A", "B"]}]
            }""",
            "worker-two/src/index.js": """
              export class B { constructor(ctx, env) { this.env = env; } async fetch() {
                const id = this.env.TO_A.idFromName('x');
                return this.env.TO_A.get(id).fetch('https://do/a');
              }}
              export class A { fetch() { return new Response('done'); } }
            """,
        })
        ids = {f["check_id"] for f in report["findings"]}
        self.assertNotIn("DO-STUB-CALL-CYCLE", ids)

    def test_cross_script_do_binding_is_an_explicit_cycle_detection_boundary(self) -> None:
        report = scan({
            "wrangler.jsonc": """{
              "name": "local-worker",
              "main": "src/index.js",
              "compatibility_date": "2026-07-01",
              "durable_objects": {"bindings": [
                {"name": "LOCAL_A", "class_name": "A"},
                {"name": "REMOTE_B", "class_name": "B", "script_name": "remote-worker"}
              ]},
              "migrations": [{"tag": "v1", "new_sqlite_classes": ["A"]}]
            }""",
            "src/index.js": """
              export class A { constructor(ctx, env) { this.env = env; } async fetch() {
                return this.env.REMOTE_B.getByName('b').fetch('https://do/b');
              }}
              export class B { constructor(ctx, env) { this.env = env; } async fetch() {
                return this.env.LOCAL_A.getByName('a').fetch('https://do/a');
              }}
            """,
        })
        ids = {f["check_id"] for f in report["findings"]}
        self.assertNotIn("DO-STUB-CALL-CYCLE", ids)

    def do_sql_ids(self, report: dict) -> list[str]:
        return [f["check_id"] for f in report["findings"] if f["check_id"] == "DO-SQL-SCAN-HOTPATH"]

    def test_do_sql_unbounded_select_is_reported(self) -> None:
        report = scan({
            "src/index.js": "\n".join([
                "export class EventLog {",
                "  constructor(ctx, env) { this.ctx = ctx; this.env = env; }",
                "  async fetch(request) {",
                "    const auth = request.headers.get('authorization');",
                "    const rows = this.ctx.storage.sql.exec('SELECT * FROM events ORDER BY created_at').toArray();",
                "    return Response.json(rows.length);",
                "  }",
                "}",
            ]),
        })
        self.assertEqual(["DO-SQL-SCAN-HOTPATH"], self.do_sql_ids(report))

    def test_do_sql_bounded_select_is_not_reported(self) -> None:
        report = scan({
            "src/index.js": "\n".join([
                "export class EventLog {",
                "  constructor(ctx, env) { this.ctx = ctx; this.env = env; }",
                "  async fetch(request) {",
                "    const auth = request.headers.get('authorization');",
                "    const rows = this.ctx.storage.sql.exec('SELECT id FROM events WHERE done = 0 LIMIT 10').toArray();",
                "    return Response.json(rows.length);",
                "  }",
                "}",
            ]),
        })
        self.assertEqual([], self.do_sql_ids(report))

    def test_do_sql_limit_in_comment_does_not_hide_unbounded_select(self) -> None:
        report = scan({
            "src/index.js": """
              export class EventLog {
                constructor(ctx, env) { this.ctx = ctx; this.env = env; }
                fetch() {
                  return Response.json(
                    this.ctx.storage.sql.exec('SELECT * FROM events /* TODO: add LIMIT */').toArray()
                  );
                }
              }
            """,
        })
        self.assertEqual(["DO-SQL-SCAN-HOTPATH"], self.do_sql_ids(report))

    def test_do_sql_keyword_in_string_literal_does_not_hide_unbounded_select(self) -> None:
        report = scan({
            "src/index.js": """
              export class EventLog {
                constructor(ctx, env) { this.ctx = ctx; this.env = env; }
                fetch() {
                  return Response.json(
                    this.ctx.storage.sql.exec("SELECT 'LIMIT' AS note, id FROM events").toArray()
                  );
                }
              }
            """,
        })
        self.assertEqual(["DO-SQL-SCAN-HOTPATH"], self.do_sql_ids(report))

    def test_prose_mention_of_sql_exec_in_markdown_is_not_reported(self) -> None:
        report = scan({
            "docs/notes.md": "Audit `storage.sql.exec(\"SELECT * FROM events\")` shapes for rows-read cost.",
        })
        self.assertEqual([], self.do_sql_ids(report))


    # --- Isolate memory leads: module-scope schema weight and body buffering ---

    DO_MEMORY_CONFIG = """{
      "name": "agent-threads",
      "main": "src/index.js",
      "compatibility_date": "2026-08-01",
      "observability": {"enabled": true},
      "durable_objects": {"bindings": [{"name": "THREAD", "class_name": "Thread"}]},
      "migrations": [{"tag": "v1", "new_sqlite_classes": ["Thread"]}]
    }"""
    PLAIN_MEMORY_CONFIG = """{
      "name": "api",
      "main": "src/index.js",
      "compatibility_date": "2026-08-01",
      "observability": {"enabled": true}
    }"""

    def memory_findings(self, report: dict) -> list[dict]:
        return [
            f for f in report["findings"]
            if f["check_id"] in {"CFDOC-PERF-MODULE-SCOPE-SCHEMA-WEIGHT", "CFDOC-PERF-BODY-BUFFERING"}
        ]

    @staticmethod
    def module_scope_tool_files(count: int, prefix: str = "src/tools") -> dict[str, str]:
        files: dict[str, str] = {}
        for index in range(count):
            files[f"{prefix}/tool{index}.ts"] = "\n".join([
                "import { z } from 'zod';",
                f"export const parameters{index} = z.object({{",
                "  owner: z.string().describe('Repository owner'),",
                "  repo: z.string().describe('Repository name'),",
                "});",
            ])
        return files

    def test_module_scope_schema_weight_is_reported_for_durable_object_project(self) -> None:
        files = {"wrangler.jsonc": self.DO_MEMORY_CONFIG, "src/index.js": "export class Thread {}"}
        files.update(self.module_scope_tool_files(25))
        report = scan(files)
        found = self.memory_findings(report)
        self.assertEqual(["CFDOC-PERF-MODULE-SCOPE-SCHEMA-WEIGHT"], [f["check_id"] for f in found])
        self.assertIn("project total 25", found[0]["evidence"])
        self.assertIn("128 MB", found[0]["message"])
        self.assertIn("Durable Objects share one V8 isolate", found[0]["message"])
        self.assertEqual("low", found[0]["confidence"])

    def test_module_scope_schema_weight_threshold_is_higher_without_durable_objects(self) -> None:
        files = {"wrangler.jsonc": self.PLAIN_MEMORY_CONFIG, "src/index.js": "export default { fetch() { return new Response('ok') } }"}
        files.update(self.module_scope_tool_files(30))
        self.assertEqual([], self.memory_findings(scan(files)))
        files.update(self.module_scope_tool_files(50))
        found = self.memory_findings(scan(files))
        self.assertEqual(["CFDOC-PERF-MODULE-SCOPE-SCHEMA-WEIGHT"], [f["check_id"] for f in found])
        self.assertIn("Script startup exceeded", found[0]["message"])

    def test_schemas_built_inside_functions_are_not_module_scope(self) -> None:
        files = {"wrangler.jsonc": self.DO_MEMORY_CONFIG, "src/index.js": "export class Thread {}"}
        for index in range(30):
            files[f"src/tools/tool{index}.ts"] = "\n".join([
                "import { z } from 'zod';",
                f"export function parameters{index}() {{",
                "  return z.object({ owner: z.string(), repo: z.string() });",
                "}",
                f"export const lazy{index} = () => ({{ parameters: z.object({{ owner: z.string() }}) }});",
                f"export class Tool{index} {{ params = z.object({{}}); run() {{ return z.object({{}}); }} }}",
            ])
        self.assertEqual([], self.memory_findings(scan(files)))

    def test_module_scope_object_literals_and_route_registrations_count(self) -> None:
        files = {"wrangler.jsonc": self.DO_MEMORY_CONFIG, "src/index.js": "export class Thread {}"}
        for index in range(13):
            files[f"src/tools/tool{index}.ts"] = "\n".join([
                "import { z } from 'zod';",
                f"export const tool{index} = defineTool({{",
                "  description: 'Read a pull request',",
                "  parameters: z.object({ owner: z.string(), repo: z.string() }),",
                "  execute: async (input) => { return z.object({}).parse(input); },",
                "});",
                f"app.post('/tool{index}', zValidator('json', z.object({{ id: z.string() }})), (c) => c.json({{}}));",
            ])
        found = self.memory_findings(scan(files))
        self.assertEqual(["CFDOC-PERF-MODULE-SCOPE-SCHEMA-WEIGHT"], [f["check_id"] for f in found])
        self.assertIn("project total 26", found[0]["evidence"])

    def test_test_files_and_string_mentions_do_not_count_toward_schema_weight(self) -> None:
        files = {"wrangler.jsonc": self.DO_MEMORY_CONFIG, "src/index.js": "export class Thread {}"}
        files.update(self.module_scope_tool_files(20, prefix="src/__tests__"))
        files.update(self.module_scope_tool_files(10, prefix="test"))
        files["src/notes.ts"] = "\n".join(["const doc = 'z.object( ' + 'z.object(';"] * 30)
        self.assertEqual([], self.memory_findings(scan(files)))

    def test_schema_weight_evidence_names_tree_shaking_amplifiers(self) -> None:
        files = {"wrangler.jsonc": self.DO_MEMORY_CONFIG, "src/index.js": "export class Thread {}"}
        files.update(self.module_scope_tool_files(25, prefix="packages/tools/src"))
        files["packages/tools/package.json"] = '{"name": "@scope/tools", "version": "1.0.0"}'
        files["packages/tools/src/index.ts"] = "export * from './zod';\nexport * from './tool0';\n"
        files["src/agent.ts"] = "export async function load() { const { run } = await import('@scope/tools'); return run; }"
        found = self.memory_findings(scan(files))
        self.assertEqual(1, len(found))
        self.assertIn("1 package.json file(s) without a sideEffects field", found[0]["message"])
        self.assertIn("1 index barrel(s) using export *", found[0]["message"])
        self.assertIn("1 dynamic import(s) of a bare package root", found[0]["message"])

    def test_valibot_and_typebox_builders_count_toward_schema_weight(self) -> None:
        files = {"wrangler.jsonc": self.DO_MEMORY_CONFIG, "src/index.js": "export class Thread {}"}
        for index in range(13):
            files[f"src/v/tool{index}.ts"] = "import { object, string } from 'valibot';\nexport const S = object({ a: string() });\n"
            files[f"src/t/tool{index}.ts"] = "import { Type } from '@sinclair/typebox';\nexport const T = Type.Object({ a: Type.String() });\n"
        found = self.memory_findings(scan(files))
        self.assertEqual(["CFDOC-PERF-MODULE-SCOPE-SCHEMA-WEIGHT"], [f["check_id"] for f in found])
        self.assertIn("project total 26", found[0]["evidence"])

    R2_UPLOAD_CONFIG = """{
      "name": "uploads",
      "main": "src/index.js",
      "compatibility_date": "2026-08-01",
      "observability": {"enabled": true},
      "r2_buckets": [{"binding": "BUCKET", "bucket_name": "uploads"}]
    }"""

    def test_request_array_buffer_without_size_guard_is_reported(self) -> None:
        report = scan({
            "wrangler.jsonc": self.R2_UPLOAD_CONFIG,
            "src/index.js": "\n".join([
                "export default {",
                "  async fetch(request, env) {",
                "    const bytes = await request.arrayBuffer();",
                "    await env.BUCKET.put(crypto.randomUUID(), bytes);",
                "    return new Response('stored');",
                "  },",
                "};",
            ]),
        })
        found = self.memory_findings(report)
        self.assertEqual(["CFDOC-PERF-BODY-BUFFERING"], [f["check_id"] for f in found])
        self.assertIn("request.arrayBuffer()", found[0]["evidence"])
        self.assertIn("Memory limit would be exceeded before EOF", found[0]["message"])

    def test_request_array_buffer_with_content_length_guard_is_not_reported(self) -> None:
        report = scan({
            "wrangler.jsonc": self.R2_UPLOAD_CONFIG,
            "src/index.js": "\n".join([
                "const MAX_BYTES = 5 * 1024 * 1024;",
                "export default {",
                "  async fetch(request, env) {",
                "    const length = Number(request.headers.get('content-length') || 0);",
                "    if (!length || length > MAX_BYTES) return new Response('too large', { status: 413 });",
                "    const bytes = await request.arrayBuffer();",
                "    await env.BUCKET.put(crypto.randomUUID(), bytes);",
                "    return new Response('stored');",
                "  },",
                "};",
            ]),
        })
        self.assertEqual([], self.memory_findings(report))

    def test_webhook_signature_verification_array_buffer_is_not_reported(self) -> None:
        report = scan({
            "wrangler.jsonc": self.PLAIN_MEMORY_CONFIG,
            "src/index.js": "\n".join([
                "export default {",
                "  async fetch(request, env) {",
                "    const body = await request.arrayBuffer();",
                "    const signature = request.headers.get('x-hub-signature-256');",
                "    const ok = await crypto.subtle.verify('HMAC', env.KEY, hexToBytes(signature), body);",
                "    return new Response(ok ? 'ok' : 'bad', { status: ok ? 200 : 401 });",
                "  },",
                "};",
            ]),
        })
        self.assertEqual([], self.memory_findings(report))

    def test_upstream_buffered_passthrough_is_reported_but_streamed_passthrough_is_not(self) -> None:
        buffered = scan({
            "wrangler.jsonc": self.PLAIN_MEMORY_CONFIG,
            "src/index.js": "\n".join([
                "export default {",
                "  async fetch(request) {",
                "    const upstream = await fetch('https://origin.example.com' + new URL(request.url).pathname);",
                "    const bytes = await upstream.arrayBuffer();",
                "    return new Response(bytes, { headers: upstream.headers });",
                "  },",
                "};",
            ]),
        })
        found = self.memory_findings(buffered)
        self.assertEqual(["CFDOC-PERF-BODY-BUFFERING"], [f["check_id"] for f in found])
        self.assertIn("upstream.arrayBuffer()", found[0]["evidence"])
        streamed = scan({
            "wrangler.jsonc": self.PLAIN_MEMORY_CONFIG,
            "src/index.js": "\n".join([
                "export default {",
                "  async fetch(request) {",
                "    const upstream = await fetch('https://origin.example.com' + new URL(request.url).pathname);",
                "    return new Response(upstream.body, { headers: upstream.headers });",
                "  },",
                "};",
            ]),
        })
        self.assertEqual([], self.memory_findings(streamed))

    def test_r2_buffering_file_is_not_double_reported_as_body_buffering(self) -> None:
        report = scan({
            "wrangler.jsonc": self.R2_UPLOAD_CONFIG,
            "src/index.js": "\n".join([
                "export default {",
                "  async fetch(request, env) {",
                "    const object = await env.BUCKET.get('report.pdf');",
                "    const bytes = await object.arrayBuffer();",
                "    await fetch('https://hooks.example.com', { method: 'POST' });",
                "    return new Response(bytes);",
                "  },",
                "};",
            ]),
        })
        ids = sorted(f["check_id"] for f in report["findings"] if f["check_id"] in {"CFDOC-PERF-R2-BUFFERING", "CFDOC-PERF-BODY-BUFFERING"})
        self.assertEqual(["CFDOC-PERF-R2-BUFFERING"], ids)

    def test_node_fs_temp_file_write_is_reported_as_low_severity(self) -> None:
        report = scan({
            "wrangler.jsonc": self.PLAIN_MEMORY_CONFIG.replace('"observability"', '"compatibility_flags": ["nodejs_compat"], "observability"'),
            "src/index.js": "\n".join([
                "import { writeFile } from 'node:fs/promises';",
                "export default {",
                "  async fetch(request) {",
                "    await writeFile('/tmp/upload.bin', new Uint8Array(await request.clone().arrayBuffer()));",
                "    return new Response('ok');",
                "  },",
                "};",
            ]),
        })
        found = [f for f in self.memory_findings(report) if "virtual file system" in f["message"]]
        self.assertEqual(1, len(found))
        self.assertEqual("low", found[0]["severity"])
        self.assertIn("writeFile(", found[0]["evidence"])


if __name__ == "__main__":
    unittest.main()
