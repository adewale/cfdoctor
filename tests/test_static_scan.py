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

    def test_do_stub_cycle_with_depth_guard_in_every_class_is_suppressed(self) -> None:
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
    def ring_stage(cls: str, next_binding: str, guarded: bool) -> str:
        guard = [
            "    const depth = Number(request.headers.get('x-hop-depth') || 0);",
            "    if (depth >= 3) return new Response('hop limit reached', { status: 429 });",
        ] if guarded else []
        return "\n".join([
            f"export class {cls} {{",
            "  constructor(ctx, env) { this.ctx = ctx; this.env = env; }",
            "  async fetch(request) {",
            "    const auth = request.headers.get('authorization');",
            *guard,
            f"    const id = this.env.{next_binding}.idFromName(auth);",
            f"    this.ctx.waitUntil(this.env.{next_binding}.get(id).fetch('https://do/next'));",
            f"    return new Response('{cls}');",
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

    def test_prose_mention_of_sql_exec_in_markdown_is_not_reported(self) -> None:
        report = scan({
            "docs/notes.md": "Audit `storage.sql.exec(\"SELECT * FROM events\")` shapes for rows-read cost.",
        })
        self.assertEqual([], self.do_sql_ids(report))


if __name__ == "__main__":
    unittest.main()
