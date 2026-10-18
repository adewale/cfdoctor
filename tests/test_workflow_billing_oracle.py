from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ORACLE = Path(__file__).resolve().parents[1] / "evals/oracles/workflow_billing_oracle.py"
spec = importlib.util.spec_from_file_location("workflow_billing_oracle", ORACLE)
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


def output(values):
    return "```json\n" + json.dumps(values) + "\n```"


class WorkflowBillingOracleTests(unittest.TestCase):
    def test_correct_worksheets_pass(self):
        for case_id, expected in module.EXPECTED.items():
            with self.subTest(case=case_id):
                self.assertEqual([], module.check(output(expected), case_id))

    def test_each_wrong_value_fails_even_when_other_values_are_correct(self):
        for case_id, expected in module.EXPECTED.items():
            for key, value in expected.items():
                values = dict(expected)
                values[key] = not value if isinstance(value, bool) else value + 1
                with self.subTest(case=case_id, key=key):
                    self.assertTrue(module.check(output(values), case_id))

    def test_strings_and_booleans_do_not_pass_for_numbers(self):
        case_id = "workflow-builtin-retry-billing"
        for wrong in ("5000000", True, None):
            values = dict(module.EXPECTED[case_id], billed_steps=wrong)
            self.assertTrue(module.check(output(values), case_id))

    def test_answer_echo_or_contradictory_duplicate_is_not_a_worksheet(self):
        case_id = "workflow-builtin-retry-billing"
        expected = module.EXPECTED[case_id]
        self.assertTrue(module.check(str(expected), case_id))
        self.assertTrue(module.check(output(expected) + output(dict(expected, billed_steps=15000000)), case_id))


if __name__ == "__main__":
    unittest.main()
