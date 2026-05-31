from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPORT_JSON_PATH = Path("reports/features/derivatives_funding_oi_feature_store_v9_54.json")
SUCCESS_DECISIONS = {
    "derivatives_funding_feature_store_created",
    "derivatives_funding_oi_feature_store_created",
    "derivatives_feature_store_created_with_warnings",
}
ALLOWED_DECISIONS = SUCCESS_DECISIONS | {
    "derivatives_feature_store_blocked_by_alignment",
    "derivatives_feature_store_blocked_by_quality",
    "derivatives_feature_store_blocked_by_leakage",
    "derivatives_feature_store_not_created_insufficient_coverage",
}


def validate_derivatives_funding_oi_feature_store_report_v9_54(report: dict[str, Any], *, mode: str = "full") -> dict[str, Any]:
    errors: list[str] = []
    if report.get("version") != "V9.54":
        errors.append("version mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("invalid decision")
    if report.get("decision") in SUCCESS_DECISIONS:
        if report.get("quality_status") != "PASS":
            errors.append("quality must pass on success")
        if report.get("schema_status") != "PASS":
            errors.append("schema must pass on success")
        if report.get("leakage_guard", {}).get("status") != "PASS":
            errors.append("leakage guard must pass on success")
        if report.get("open_interest_included") is not False:
            errors.append("V9.54 expected OI to be excluded")
        for timeframe, path in report.get("feature_store_paths", {}).items():
            if mode == "full" and not Path(path).exists():
                errors.append(f"missing feature store for {timeframe}: {path}")
    flags = report.get("safety_flags", {})
    for key in [
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
    ]:
        if flags.get(key) is not True:
            errors.append(f"safety flag must be true: {key}")
    for key in ["api_key_used", "private_endpoint_used", "exchange_auth_used", "websocket_live_used", "network_used"]:
        if flags.get(key) is not False:
            errors.append(f"safety flag must be false: {key}")
    if mode not in {"full", "audit-lite"}:
        errors.append("unknown validation mode")
    return {"version": "V9.54", "mode": mode, "passed": not errors, "errors": errors}


def validate_derivatives_funding_oi_feature_store_file_v9_54(root: Path = Path("."), *, mode: str = "full") -> dict[str, Any]:
    path = root / REPORT_JSON_PATH
    if not path.exists():
        return {"version": "V9.54", "mode": mode, "passed": False, "errors": [f"missing report: {path}"]}
    return validate_derivatives_funding_oi_feature_store_report_v9_54(json.loads(path.read_text(encoding="utf-8")), mode=mode)
