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

    D1_WRANGLER = '''{
      "name": "d1-cache-test",
      "compatibility_date": "2026-07-01",
      "observability": {"enabled": true},
      "d1_databases": [{"binding": "DB", "database_name": "blog", "database_id": "x"}]
    }'''
    D1_MIGRATION = "CREATE TABLE post_reads(id INTEGER PRIMARY KEY, slug TEXT, client_id TEXT);"

    def test_memory_only_cachified_adapter_on_d1_aggregate_is_flagged(self) -> None:
        report = scan({
            "wrangler.jsonc": self.D1_WRANGLER,
            "migrations/0001.sql": self.D1_MIGRATION,
            "src/reads.ts": "\n".join([
                "import { LRUCache } from 'lru-cache';",
                "const lruCache = new LRUCache({ max: 500 });",
                "export function getBlogPostReadCounts(env) {",
                "  return cachified({",
                "    key: 'blog:post-read-counts',",
                "    cache: lruCache,",
                "    ttl: 1000 * 60 * 30,",
                "    async getFreshValue() {",
                "      return env.DB.prepare('SELECT slug, COUNT(id) AS reads FROM post_reads GROUP BY slug').all();",
                "    },",
                "  });",
                "}",
            ]),
        })
        finding = next(f for f in report["findings"] if f["check_id"] == "CFDOC-COST-D1-ISOLATE-CACHE")
        self.assertIn("lruCache", finding["evidence"])
        self.assertIn("regardless of TTL", finding["message"])

    def test_module_scope_map_memo_on_d1_aggregate_is_flagged(self) -> None:
        report = scan({
            "wrangler.jsonc": self.D1_WRANGLER,
            "migrations/0001.sql": self.D1_MIGRATION,
            "src/stats.js": "\n".join([
                "const statsMemo = new Map();",
                "export async function totalReaders(env) {",
                "  const hit = statsMemo.get('total');",
                "  if (hit && hit.expires > Date.now()) return hit.value;",
                "  const row = await env.DB.prepare('SELECT COUNT(DISTINCT client_id) AS total FROM post_reads').first();",
                "  statsMemo.set('total', { value: row.total, expires: Date.now() + 300000 });",
                "  return row.total;",
                "}",
            ]),
        })
        self.assertIn("CFDOC-COST-D1-ISOLATE-CACHE", {f["check_id"] for f in report["findings"]})

    def test_shared_kv_layer_suppresses_isolate_cache_lead(self) -> None:
        report = scan({
            "wrangler.jsonc": self.D1_WRANGLER,
            "migrations/0001.sql": self.D1_MIGRATION,
            "src/layered.js": "\n".join([
                "const l1 = new Map();",
                "export async function readTotals(env) {",
                "  const cached = l1.get('totals');",
                "  if (cached) return cached;",
                "  const stored = await env.CACHE_KV.get('totals', 'json');",
                "  if (stored) { l1.set('totals', stored); return stored; }",
                "  const rows = await env.DB.prepare('SELECT slug, SUM(read_ms) AS total_ms FROM post_reads GROUP BY slug').all();",
                "  await env.CACHE_KV.put('totals', JSON.stringify(rows), { expirationTtl: 1800 });",
                "  l1.set('totals', rows);",
                "  return rows;",
                "}",
            ]),
            "src/shared-adapter.ts": "\n".join([
                "export function getReadCounts(env) {",
                "  return cachified({",
                "    key: 'blog:post-read-counts',",
                "    cache: sharedKvCache(env),",
                "    ttl: 1000 * 60 * 30,",
                "    async getFreshValue() {",
                "      return env.DB.prepare('SELECT slug, COUNT(id) AS reads FROM post_reads GROUP BY slug').all();",
                "    },",
                "  });",
                "}",
            ]),
        })
        self.assertNotIn("CFDOC-COST-D1-ISOLATE-CACHE", {f["check_id"] for f in report["findings"]})

    def test_memory_cache_of_cheap_point_query_is_not_flagged(self) -> None:
        report = scan({
            "wrangler.jsonc": self.D1_WRANGLER,
            "migrations/0001.sql": self.D1_MIGRATION,
            "src/title.ts": "\n".join([
                "import { LRUCache } from 'lru-cache';",
                "const lruCache = new LRUCache({ max: 500 });",
                "export function getPostTitle(env, slug) {",
                "  return cachified({",
                "    key: `title:${slug}`,",
                "    cache: lruCache,",
                "    async getFreshValue() {",
                "      return env.DB.prepare('SELECT title FROM posts WHERE slug = ?1').bind(slug).first();",
                "    },",
                "  });",
                "}",
            ]),
        })
        self.assertNotIn("CFDOC-COST-D1-ISOLATE-CACHE", {f["check_id"] for f in report["findings"]})

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


if __name__ == "__main__":
    unittest.main()
