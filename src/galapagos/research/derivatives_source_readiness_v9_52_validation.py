from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPORT_JSON_PATH = Path("reports/research_decisions/derivatives_source_readiness_v9_52.json")
ALLOWED_DECISIONS = {
    "derivatives_source_readiness_funding_ready",
    "derivatives_source_readiness_funding_ready_oi_limited",
    "derivatives_source_readiness_not_ready_source_uncertainty",
    "derivatives_source_readiness_not_ready_no_public_source",
    "derivatives_source_readiness_manual_review_required",
}


def validate_derivatives_source_readiness_report_v9_52(report: dict[str, Any], *, mode: str = "full") -> dict[str, Any]:
    errors: list[str] = []
    if report.get("version") != "V9.52":
        errors.append("version mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("invalid decision")
    for key in ["funding_rate", "open_interest"]:
        if key not in report.get("source_assessments", {}):
            errors.append(f"missing source assessment: {key}")
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
    ]
    for key in expected_true:
        if flags.get(key) is not True:
            errors.append(f"safety flag must be true: {key}")
    expected_false = [
        "api_key_used",
        "private_endpoint_used",
        "exchange_auth_used",
        "websocket_live_used",
        "network_used",
    ]
    for key in expected_false:
        if flags.get(key) is not False:
            errors.append(f"safety flag must be false: {key}")
    if report.get("network_used") is not False or report.get("new_data_downloaded") is not False:
        errors.append("V9.52 must not use network or download data")
    if mode not in {"full", "audit-lite"}:
        errors.append("unknown validation mode")
    return {"version": "V9.52", "mode": mode, "passed": not errors, "errors": errors}


def validate_derivatives_source_readiness_file_v9_52(root: Path = Path("."), *, mode: str = "full") -> dict[str, Any]:
    path = root / REPORT_JSON_PATH
    if not path.exists():
        return {"version": "V9.52", "mode": mode, "passed": False, "errors": [f"missing report: {path}"]}
    return validate_derivatives_source_readiness_report_v9_52(json.loads(path.read_text(encoding="utf-8")), mode=mode)
