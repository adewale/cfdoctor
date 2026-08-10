from __future__ import annotations

import copy
import datetime as dt
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_claim_ledger.py"
spec = importlib.util.spec_from_file_location("check_claim_ledger", SCRIPT)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
assert spec.loader
spec.loader.exec_module(module)


class ClaimLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ledger = json.loads((ROOT / "research/incident-claim-ledger.json").read_text())

    def test_current_ledger_is_valid_and_superseded_source_is_resolved(self) -> None:
        errors, warnings = module.validate(copy.deepcopy(self.ledger), dt.date(2026, 8, 10))
        self.assertEqual([], errors)
        self.assertEqual([], warnings)
        record = next(item for item in self.ledger["records"] if item["id"] == "CFDOC-EVD-AWS-S3-HOTLINK")
        self.assertEqual("superseded", record["status"])
        self.assertIn("No recoverable primary", record["disposition"])

    def test_duplicate_evidence_id_is_rejected(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        ledger["records"].append(copy.deepcopy(ledger["records"][0]))
        errors, _ = module.validate(ledger, dt.date(2026, 7, 11))
        self.assertTrue(any("duplicate evidence id" in error for error in errors))

    def test_accepted_incident_requires_first_hand_primary_source(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        ledger["records"][0]["sources"][0]["first_hand"] = False
        errors, _ = module.validate(ledger, dt.date(2026, 7, 11))
        self.assertTrue(any("first-hand primary source" in error for error in errors))

    def test_overdue_accepted_record_fails_closed(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        ledger["records"][0]["review_due"] = "2026-07-10"
        errors, _ = module.validate(ledger, dt.date(2026, 7, 11))
        self.assertTrue(any("review due" in error for error in errors))

    def test_review_due_cannot_exceed_declared_cadence(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        ledger["records"][0]["review_due"] = "2099-01-01"
        errors, _ = module.validate(ledger, dt.date(2026, 7, 11))
        self.assertTrue(any("exceeds 92-day ledger cadence" in error for error in errors))

    def test_top_level_freshness_metadata_is_validated(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        ledger["as_of"] = "not-a-date"
        ledger["review_cadence_days"] = 0
        errors, _ = module.validate(ledger, dt.date(2026, 7, 11))
        self.assertTrue(any("ledger.as_of" in error for error in errors))
        self.assertTrue(any("review_cadence_days" in error for error in errors))

    def test_duplicate_primary_source_across_clusters_is_rejected(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        ledger["records"][1]["sources"][0]["url"] = ledger["records"][0]["sources"][0]["url"]
        errors, _ = module.validate(ledger, dt.date(2026, 7, 11))
        self.assertTrue(any("primary source URL duplicates" in error for error in errors))

    def test_extra_ledger_to_fixture_link_is_rejected(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        ledger["records"][1]["fixture_ids"].append("clean-baseline")
        errors, _ = module.validate(ledger, dt.date(2026, 7, 11))
        self.assertTrue(any("lacks reciprocal evidence_id" in error for error in errors))

    def test_unavailable_source_requires_unverified_status(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        ledger["records"][0]["sources"][0]["availability"] = "unavailable"
        errors, _ = module.validate(ledger, dt.date(2026, 7, 11))
        self.assertTrue(any("unavailable source requires unverified" in error for error in errors))

    def test_malformed_source_entry_is_reported_without_crashing(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        ledger["records"][0]["sources"] = ["not-an-object"]
        errors, _ = module.validate(ledger, dt.date(2026, 7, 11))
        self.assertTrue(any("sources[0] must be an object" in error for error in errors))

    def test_unknown_check_id_is_rejected(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        ledger["records"][0]["check_ids"].append("CFDOC-NOT-REAL")
        errors, _ = module.validate(ledger, dt.date(2026, 7, 11))
        self.assertTrue(any("unknown check_id" in error for error in errors))

    def test_fixture_evidence_must_match_a_fixture_check(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        ledger["records"][0]["check_ids"] = []
        errors, _ = module.validate(ledger, dt.date(2026, 7, 11))
        self.assertTrue(any("has no check_id matching required/forbidden fixture behavior" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
