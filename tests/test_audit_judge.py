"""Execution evidence and cache correctness for the native project-audit judge."""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

HELPERS = Path(__file__).resolve().parents[1] / "evals/results/repair-final"
sys.path.insert(0, str(HELPERS))
spec = importlib.util.spec_from_file_location("audit_judge", HELPERS / "judge_round.py")
judge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(judge)


class AuditJudgeTests(unittest.TestCase):
    def write_trace(self, root, commands):
        (root / "metadata.json").write_text(
            json.dumps({"trace_observation_complete": True})
        )
        (root / "trace.jsonl").write_text(
            "".join(
                json.dumps({"type": "item.completed", "item": item}) + "\n"
                for item in commands
            )
        )

    def test_prompt_forwards_real_scanner_result_and_auditor_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = {
                "scanner_version": "0.5.1",
                "findings": [{"check_id": "CFDOC-REL-QUEUE-NO-DLQ"}],
            }
            self.write_trace(
                root,
                [
                    {
                        "type": "command_execution",
                        "command": "python3 -B skills/root-0/scripts/cfdoctor_static_scan.py project --json",
                        "exit_code": 0,
                        "aggregated_output": json.dumps(result),
                    }
                ],
            )
            bundle = root / "project.json"
            bundle.write_text(json.dumps({"files": {"worker.js": "export default {}"}}))
            prompt = judge.grading_prompt(
                {
                    "prompt": "You may run the supplied scanner read-only.",
                    "files": [str(bundle)],
                },
                root,
            )
            activity = json.loads(
                prompt.split(
                    "Observed auditor activity (evaluator trace, not project source):\n"
                )[1]
            )
            self.assertEqual(activity["commands"][0]["scanner_output"], result)
            self.assertEqual(activity["commands"][0]["exit_code"], 0)
            self.assertIn("You may run the supplied scanner read-only.", prompt)

    def test_quoted_scanner_mention_and_failure_are_not_successful_scans(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_trace(
                root,
                [
                    {
                        "type": "command_execution",
                        "command": "rg cfdoctor_static_scan.py README.md",
                        "exit_code": 0,
                        "aggregated_output": "Run cfdoctor_static_scan.py",
                    },
                    {
                        "type": "command_execution",
                        "command": "python3 -B missing.py",
                        "exit_code": 2,
                        "aggregated_output": "No such file",
                    },
                    {"type": "agent_message", "text": "I ran a scanner"},
                ],
            )
            activity = judge.observed_activity(root)
            self.assertEqual(len(activity["commands"]), 2)
            self.assertTrue(
                all("scanner_output" not in item for item in activity["commands"])
            )
            self.assertEqual(activity["commands"][1]["exit_code"], 2)

    def test_missing_trace_is_unavailable_not_a_complete_empty_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(judge.observed_activity(Path(tmp)), {"available": False})

    def test_changed_evidence_cannot_reuse_a_cached_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "output.md"
            output.write_text("Scanner ran.")
            task = {
                "prompt": "source and receipt A",
                "expected_behavior": ["verify execution"],
                "assertion": {"type": "judge"},
                "output_path": str(output),
            }
            first = judge.grading_fingerprint(task, "model", "backend")
            cached = root / "cached.json"
            cached.write_text(
                json.dumps(
                    {
                        "grading_input_sha256": first,
                        "dimension_scores": {"precision": 5},
                    }
                )
            )
            self.assertEqual(
                judge.cached_judgment(cached, first)["dimension_scores"]["precision"], 5
            )
            task["prompt"] = "source and receipt B"
            second = judge.grading_fingerprint(task, "model", "backend")
            self.assertNotEqual(first, second)
            with self.assertRaisesRegex(ValueError, "different grading inputs"):
                judge.cached_judgment(cached, second)
            output.write_text("Different audit.")
            self.assertNotEqual(
                second, judge.grading_fingerprint(task, "model", "backend")
            )
