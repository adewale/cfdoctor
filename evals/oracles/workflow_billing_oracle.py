#!/usr/bin/env python3
"""Grade explicit billing worksheets; explanation/source correctness is judged separately."""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

EXPECTED = {
    "workflow-builtin-retry-billing": {
        "workflow_starts": 1000000,
        "billed_steps": 5000000,
        "step_overage_usd": 36,
        "retry_extra_step_fee_usd": 0,
        "retry_cpu_and_downstream_cost_guaranteed_zero": False
    },
    "workflow-application-retry-billing": {
        "workflow_starts": 1000000,
        "billed_steps": 15000000,
        "step_overage_usd": 116
    },
    "workflow-rollback-billing": {
        "billed_steps": 4000000,
        "step_overage_usd": 28,
        "rollback_extra_step_fee_usd": 0,
        "rollback_cpu_and_downstream_cost_guaranteed_zero": False
    },
    "workflow-wait-invocation-billing": {
        "workflow_starts": 1000000,
        "billed_steps": 4000000,
        "step_overage_usd": 28,
        "cpu_overage_usd": 0.4,
        "subtotal_usd": 28.4
    },
    "workflow-retention-cohort": {
        "legacy_success_days": 30,
        "new_success_days": 7,
        "override_success_days": 1,
        "override_error_days": 4,
        "free_success_days": 3
    },
    "workflow-storage-daily-peak": {
        "gb_month": 10,
        "storage_overage_usd": 1.8,
        "cleanup_erases_daily_peak": False
    }
}


def check(output: str, case_id: str) -> list[str]:
    expected = EXPECTED[case_id]
    candidates = []
    for block in re.findall(r"```(?:json)?\s*\n(.*?)```", output, re.IGNORECASE | re.DOTALL):
        try:
            obj = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and set(expected) <= obj.keys():
            candidates.append(obj)
    if len(candidates) != 1:
        return [f"Expected one JSON worksheet with keys {sorted(expected)}, found {len(candidates)}"]
    actual = candidates[0]
    errors = []
    for key, value in expected.items():
        observed = actual[key]
        if isinstance(value, bool):
            valid = isinstance(observed, bool) and observed is value
        else:
            valid = type(observed) in (int, float) and math.isfinite(observed) and math.isclose(observed, value, rel_tol=1e-8, abs_tol=1e-8)
        if not valid:
            errors.append(f"{key}: expected {value!r}, got {observed!r}")
    return errors


def main() -> int:
    run_dir, case_id = Path(sys.argv[1]), sys.argv[2]
    errors = check((run_dir / "output.md").read_text(encoding="utf-8"), case_id)
    print("\n".join(errors) if errors else "Billing worksheet values and arithmetic are correct.")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
