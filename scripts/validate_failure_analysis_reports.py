"""Validate failure analysis reports for a given version.

Ensures that no report has status=missing_dataset or verdict=SKIPPED,
that the recommendation contains primary_recommendation, and that
safety flags are correct.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPORT_NAMES = [
    "recent_window_failure",
    "regime_failure",
    "cost_failure",
    "feature_drift",
    "label_diagnostics",
    "horizon_diagnostics",
    "data_gap_analysis",
]


def validate(version: str, reports_dir: str = "reports/research") -> dict:
    """Validate all failure-analysis reports for *version*.

    Returns a dict with ``passed`` (bool), ``errors`` (list), and
    ``verdicts`` (dict).
    """
    v_suffix = version.replace(".", "_")
    rd = Path(reports_dir)
    errors: list[str] = []
    verdicts: dict[str, str] = {}

    # ---- Check each analysis report ----
    for name in REPORT_NAMES:
        fname = f"{name}_{v_suffix}.json"
        fpath = rd / fname
        if not fpath.exists():
            errors.append(f"Missing report: {fpath}")
            continue

        data = json.loads(fpath.read_text())
        status = data.get("status", "")
        verdict = data.get("verdict", "")
        verdicts[name] = verdict

        if status == "missing_dataset":
            errors.append(f"{fname}: status=missing_dataset (scientific analysis was NOT executed)")
        if verdict == "SKIPPED":
            errors.append(f"{fname}: verdict=SKIPPED (scientific analysis was NOT executed)")

    # ---- Check recommendation report ----
    rec_name = f"{v_suffix}_recommendation.json"
    rec_path = rd / rec_name
    if not rec_path.exists():
        errors.append(f"Missing recommendation: {rec_path}")
    else:
        rec = json.loads(rec_path.read_text())
        if "primary_recommendation" not in rec:
            errors.append(f"{rec_name}: missing primary_recommendation")
        if rec.get("status") == "missing_dataset":
            errors.append(f"{rec_name}: status=missing_dataset")
        if rec.get("verdict") == "SKIPPED":
            errors.append(f"{rec_name}: verdict=SKIPPED")
        if rec.get("ready_for_reviewer") is True:
            errors.append(f"{rec_name}: ready_for_reviewer should be false")

    passed = len(errors) == 0
    return {"passed": passed, "errors": errors, "verdicts": verdicts}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate failure analysis reports.")
    parser.add_argument("--version", required=True, help="Version string (e.g., v1.17.1)")
    parser.add_argument("--reports-dir", default="reports/research")
    args = parser.parse_args()

    result = validate(args.version, args.reports_dir)

    print(f"Validation for {args.version}:")
    print(f"  Passed: {result['passed']}")
    if result["verdicts"]:
        print("  Verdicts:")
        for k, v in result["verdicts"].items():
            print(f"    {k}: {v}")
    if result["errors"]:
        print("  Errors:")
        for e in result["errors"]:
            print(f"    - {e}")
        sys.exit(1)
    else:
        print("  All checks passed.")


if __name__ == "__main__":
    main()
