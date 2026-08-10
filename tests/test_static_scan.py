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

    D1_APP_CONFIG = '''{
      "name": "d1-index-test",
      "compatibility_date": "2026-07-01",
      "observability": {"enabled": true},
      "d1_databases": [{"binding": "DB", "database_name": "app", "database_id": "x"}]
    }'''

    def test_unindexed_d1_filtered_query_is_flagged_and_sql_index_suppresses(self) -> None:
        base = {
            "wrangler.jsonc": self.D1_APP_CONFIG,
            "migrations/0001_init.sql": "CREATE TABLE reimbursement (id INTEGER PRIMARY KEY, year INTEGER NOT NULL, state_id INTEGER NOT NULL);",
            "src/index.js": 'const latest = await env.DB.prepare("SELECT MAX(year) AS year FROM reimbursement").first();',
        }
        report = scan(base)
        finding = next(f for f in report["findings"] if f["check_id"] == "CFDOC-COST-D1-NO-INDEXES")
        self.assertIn("migrations/0001_init.sql", finding["evidence"])
        self.assertIn("rows read (scanned), not rows returned", finding["message"])
        self.assertIn("ANALYZE", finding["fix"])

        indexed = dict(base)
        indexed["migrations/0002_indexes.sql"] = "CREATE INDEX reimbursement_year_idx ON reimbursement(year);"
        ids = {f["check_id"] for f in scan(indexed)["findings"]}
        self.assertNotIn("CFDOC-COST-D1-NO-INDEXES", ids)

    def test_orm_index_definition_suppresses_d1_no_indexes(self) -> None:
        report = scan({
            "wrangler.jsonc": self.D1_APP_CONFIG,
            "migrations/0001_init.sql": "CREATE TABLE reimbursement (id INTEGER PRIMARY KEY, year INTEGER NOT NULL);",
            "src/schema.ts": 'export const reimbursement = sqliteTable("reimbursement", { year: integer("year") }, (t) => [index("reimbursement_year_idx").on(t.year)]);',
            "src/index.js": 'await env.DB.prepare("SELECT year FROM reimbursement WHERE year = ?1").bind(2026).all();',
        })
        self.assertNotIn("CFDOC-COST-D1-NO-INDEXES", {f["check_id"] for f in report["findings"]})

    def test_unfiltered_d1_queries_alone_do_not_claim_missing_indexes(self) -> None:
        report = scan({
            "wrangler.jsonc": self.D1_APP_CONFIG,
            "migrations/0001_init.sql": "CREATE TABLE settings (id INTEGER PRIMARY KEY, value TEXT);",
            "src/index.js": 'await env.DB.prepare("SELECT value FROM settings LIMIT 1").first();',
        })
        self.assertNotIn("CFDOC-COST-D1-NO-INDEXES", {f["check_id"] for f in report["findings"]})

    def test_layout_level_d1_query_without_cache_is_flagged(self) -> None:
        report = scan({
            "wrangler.jsonc": self.D1_APP_CONFIG,
            "src/routes/+layout.server.ts": 'export async function load({ platform }) { return await platform.env.DB.prepare("SELECT MAX(year) AS year FROM reimbursement").first(); }',
        })
        finding = next(f for f in report["findings"] if f["check_id"] == "CFDOC-COST-D1-LAYOUT-HOTPATH")
        self.assertIn("+layout.server.ts", finding["evidence"])
        self.assertIn("every page view", finding["message"])

    def test_nextjs_app_layout_d1_query_is_flagged_but_page_routes_are_not(self) -> None:
        query = 'await env.DB.prepare("SELECT slug FROM sections ORDER BY position").all();'
        report = scan({
            "wrangler.jsonc": self.D1_APP_CONFIG,
            "app/dashboard/layout.tsx": query,
            "src/routes/prices/+page.server.ts": query,
        })
        layout_hits = [f["evidence"] for f in report["findings"] if f["check_id"] == "CFDOC-COST-D1-LAYOUT-HOTPATH"]
        self.assertEqual(1, len(layout_hits))
        self.assertIn("app/dashboard/layout.tsx", layout_hits[0])

    def test_cached_layout_d1_query_is_not_flagged(self) -> None:
        config = '''{
          "name": "d1-index-test",
          "compatibility_date": "2026-07-01",
          "observability": {"enabled": true},
          "d1_databases": [{"binding": "DB", "database_name": "app", "database_id": "x"}],
          "kv_namespaces": [{"binding": "NAV_CACHE", "id": "y"}]
        }'''
        report = scan({
            "wrangler.jsonc": config,
            "src/routes/+layout.server.ts": "\n".join([
                "export async function load({ platform }) {",
                '  const hit = await platform.env.NAV_CACHE.get("nav-data:v1", "json");',
                "  if (hit) return hit;",
                '  const fresh = await platform.env.DB.prepare("SELECT MAX(year) AS year FROM reimbursement").first();',
                '  await platform.env.NAV_CACHE.put("nav-data:v1", JSON.stringify(fresh));',
                "  return fresh;",
                "}",
            ]),
        })
        self.assertNotIn("CFDOC-COST-D1-LAYOUT-HOTPATH", {f["check_id"] for f in report["findings"]})


if __name__ == "__main__":
    unittest.main()
