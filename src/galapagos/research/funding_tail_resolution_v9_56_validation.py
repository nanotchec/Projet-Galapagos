from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPORT_JSON_PATH = Path("reports/research_decisions/funding_tail_resolution_v9_56.json")
ALLOWED_DECISIONS = {
    "funding_tail_resolved_full_target_window",
    "funding_tail_unavailable_use_closed_common_window",
    "funding_tail_unavailable_wait_for_public_archive",
    "funding_tail_unavailable_source_issue",
    "funding_common_window_not_sufficient",
    "stop_derivatives_funding_branch",
}
SUCCESS_DECISIONS = {
    "funding_tail_resolved_full_target_window",
    "funding_tail_unavailable_use_closed_common_window",
}


def validate_funding_tail_resolution_report_v9_56(report: dict[str, Any], *, mode: str = "full") -> dict[str, Any]:
    errors: list[str] = []
    if report.get("version") != "V9.56":
        errors.append("version mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("invalid decision")
    if report.get("decision") in SUCCESS_DECISIONS and not report.get("common_window_sufficient_for_feature_store"):
        errors.append("success decision must authorize common window feature store")
    if report.get("decision") == "funding_tail_unavailable_use_closed_common_window":
        window = report.get("actual_feature_window", {})
        if window.get("end") != "2026-04-30T16:00:00Z":
            errors.append("closed common window must end at last known funding timestamp")
        full_quality = report.get("full_target_window_quality", {})
        if int(full_quality.get("missing_intervals", 0)) <= 0:
            errors.append("closed common window requires documented missing full-target intervals")
    if report.get("decision") == "funding_tail_resolved_full_target_window":
        full_quality = report.get("full_target_window_quality", {})
        if full_quality.get("quality_status") != "PASS":
            errors.append("full target decision requires full target quality PASS")
    if report.get("network_used") is not True:
        errors.append("V9.56 must record the authorized public source probe")
    flags = report.get("safety_flags", {})
    expected_true = [
        "no_trading",
        "no_paper_live",
        "no_orders",
        "no_backtest",
        "no_walk_forward",
        "no_ml",
        "no_dataset_supervised",
        "no_labels",
        "no_strategy",
        "no_actionable_signal",
        "no_persistent_model",
        "no_destructive_cleanup",
        "no_sidecars",
        "no_zip_fingerprints",
        "network_used",
    ]
    for key in expected_true:
        if flags.get(key) is not True:
            errors.append(f"safety flag must be true: {key}")
    expected_false = ["api_key_used", "private_endpoint_used", "exchange_auth_used", "websocket_live_used"]
    for key in expected_false:
        if flags.get(key) is not False:
            errors.append(f"safety flag must be false: {key}")
    if mode not in {"full", "audit-lite"}:
        errors.append("unknown validation mode")
    return {"version": "V9.56", "mode": mode, "passed": not errors, "errors": errors}


def validate_funding_tail_resolution_file_v9_56(root: Path = Path("."), *, mode: str = "full") -> dict[str, Any]:
    path = root / REPORT_JSON_PATH
    if not path.exists():
        return {"version": "V9.56", "mode": mode, "passed": False, "errors": [f"missing report: {path}"]}
    return validate_funding_tail_resolution_report_v9_56(json.loads(path.read_text(encoding="utf-8")), mode=mode)
