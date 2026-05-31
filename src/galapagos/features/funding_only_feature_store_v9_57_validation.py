from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.features.funding_only_feature_store_v9_57_schemas import EXPECTED_TIMEFRAMES


REPORT_JSON_PATH = Path("reports/features/funding_only_feature_store_v9_57.json")
ALLOWED_DECISIONS = {
    "funding_only_feature_store_created",
    "funding_only_feature_store_created_with_warnings",
    "funding_only_feature_store_partial",
    "funding_only_feature_store_blocked_by_alignment",
    "funding_only_feature_store_blocked_by_quality",
    "funding_only_feature_store_blocked_by_leakage",
    "funding_only_feature_store_blocked_by_storage",
}
SUCCESS_DECISIONS = {"funding_only_feature_store_created", "funding_only_feature_store_created_with_warnings"}


def validate_funding_only_feature_store_report_v9_57(report: dict[str, Any], *, mode: str = "full") -> dict[str, Any]:
    errors: list[str] = []
    if report.get("version") != "V9.57":
        errors.append("version mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("invalid decision")
    if report.get("decision") in SUCCESS_DECISIONS:
        if report.get("feature_store_created") is not True:
            errors.append("success decision must create feature store")
        if report.get("quality_status") != "PASS":
            errors.append("success decision requires quality PASS")
        if report.get("leakage_guard", {}).get("status") != "PASS":
            errors.append("success decision requires leakage guard PASS")
        paths = report.get("feature_store_paths", {})
        for timeframe in EXPECTED_TIMEFRAMES:
            if timeframe not in paths:
                errors.append(f"missing feature path for {timeframe}")
    if report.get("dataset_created") is not False or report.get("labels_created") is not False:
        errors.append("V9.57 must not create dataset or labels")
    if report.get("network_used") is not False or report.get("new_data_downloaded") is not False:
        errors.append("V9.57 must not use network or download new data")
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
        "no_new_data_download",
    ]
    for key in expected_true:
        if flags.get(key) is not True:
            errors.append(f"safety flag must be true: {key}")
    expected_false = ["api_key_used", "private_endpoint_used", "exchange_auth_used", "websocket_live_used", "network_used"]
    for key in expected_false:
        if flags.get(key) is not False:
            errors.append(f"safety flag must be false: {key}")
    if mode not in {"full", "audit-lite"}:
        errors.append("unknown validation mode")
    return {"version": "V9.57", "mode": mode, "passed": not errors, "errors": errors}


def validate_funding_only_feature_store_file_v9_57(root: Path = Path("."), *, mode: str = "full") -> dict[str, Any]:
    path = root / REPORT_JSON_PATH
    if not path.exists():
        return {"version": "V9.57", "mode": mode, "passed": False, "errors": [f"missing report: {path}"]}
    return validate_funding_only_feature_store_report_v9_57(json.loads(path.read_text(encoding="utf-8")), mode=mode)
