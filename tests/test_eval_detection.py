"""The detection eval is the gate for every fixture; show each failure rule can go red."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("eval_detection", ROOT / "scripts/eval_detection.py")
eval_detection = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = eval_detection
_spec.loader.exec_module(eval_detection)

CRON_PROJECT = json.dumps({
    "name": "cron-worker",
    "main": "src/index.js",
    "compatibility_date": "2026-07-01",
    "observability": {"enabled": True},
    "triggers": {"crons": ["* * * * *"]},
})


def make_fixture(parent: Path, name: str, expected: dict) -> Path:
    fixture = parent / name
    (fixture / "src").mkdir(parents=True)
    (fixture / "wrangler.jsonc").write_text(CRON_PROJECT)
    (fixture / "src/index.js").write_text("export default { scheduled() {} };\n")
    (fixture / "expected.json").write_text(json.dumps(expected))
    return fixture


class EvaluateFixtureTests(unittest.TestCase):
    def evaluate(self, expected: dict):
        with tempfile.TemporaryDirectory() as tmp:
            return eval_detection.evaluate_fixture(make_fixture(Path(tmp), "case", expected))

    def test_passes_when_required_present_and_forbidden_absent(self) -> None:
        result = self.evaluate({
            "required_check_ids": ["CFDOC-COST-CRON-EVERY-MINUTE"],
            "forbidden_check_ids": ["CFDOC-COST-BROAD-ROUTE"],
            "expected_evidence_terms": ["* * * * *"],
        })
        self.assertTrue(result.passed, result.notes)

    def test_missing_required_check_fails(self) -> None:
        result = self.evaluate({"required_check_ids": ["CFDOC-COST-BROAD-ROUTE"]})
        self.assertFalse(result.passed)
        self.assertEqual(["CFDOC-COST-BROAD-ROUTE"], result.missing)

    def test_forbidden_check_fails(self) -> None:
        result = self.evaluate({"required_check_ids": [], "forbidden_check_ids": ["CFDOC-COST-CRON-EVERY-MINUTE"]})
        self.assertFalse(result.passed)
        self.assertEqual(["CFDOC-COST-CRON-EVERY-MINUTE"], result.forbidden_hit)

    def test_max_findings_budget_fails_when_exceeded(self) -> None:
        result = self.evaluate({"required_check_ids": [], "max_findings": 0})
        self.assertFalse(result.passed)
        self.assertTrue(result.over_budget)

    def test_evidence_term_absent_from_required_finding_fails(self) -> None:
        result = self.evaluate({
            "required_check_ids": ["CFDOC-COST-CRON-EVERY-MINUTE"],
            "expected_evidence_terms": ["*/5"],
        })
        self.assertFalse(result.passed)
        self.assertEqual(["*/5"], result.missing_evidence_terms)


    def test_evidence_terms_must_come_from_required_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = make_fixture(Path(tmp), "case", {
                "required_check_ids": ["CFDOC-COST-CRON-EVERY-MINUTE"],
                "expected_evidence_terms": ["*/*"],
            })
            config = json.loads((fixture / "wrangler.jsonc").read_text())
            config["routes"] = ["*/*"]
            (fixture / "wrangler.jsonc").write_text(json.dumps(config))
            result = eval_detection.evaluate_fixture(fixture)
        self.assertIn("CFDOC-COST-BROAD-ROUTE", result.found_ids)
        self.assertFalse(result.passed)
        self.assertEqual(["*/*"], result.missing_evidence_terms)


class MainExitCodeTests(unittest.TestCase):
    def run_main(self, fixtures: list[tuple[str, dict]]) -> int:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fixtures"
            root.mkdir()
            for name, expected in fixtures:
                make_fixture(root, name, expected)
            with mock.patch.object(eval_detection, "FIXTURES_DIR", root), contextlib.redirect_stdout(io.StringIO()):
                return eval_detection.main(["--out-dir", str(Path(tmp) / "out")])

    def test_exit_zero_only_when_every_fixture_passes(self) -> None:
        good = ("good", {"required_check_ids": ["CFDOC-COST-CRON-EVERY-MINUTE"]})
        bad = ("bad", {"required_check_ids": [], "forbidden_check_ids": ["CFDOC-COST-CRON-EVERY-MINUTE"]})
        self.assertEqual(0, self.run_main([good]))
        self.assertEqual(1, self.run_main([good, bad]))

    def test_no_fixtures_is_a_harness_error_not_a_pass(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(2, self.run_main([]))


if __name__ == "__main__":
    unittest.main()
