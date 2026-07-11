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


if __name__ == "__main__":
    unittest.main()
