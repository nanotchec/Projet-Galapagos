from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPORT_JSON_PATH = Path("reports/data/derivatives_funding_oi_collection_v9_53.json")
ALLOWED_DECISIONS = {
    "funding_collection_complete",
    "funding_collection_complete_oi_not_ready",
    "funding_collection_partial",
    "funding_collection_failed_source_issue",
    "oi_collection_ready",
    "oi_collection_not_ready_history_limited",
    "derivatives_collection_not_executed",
}
SUCCESS_DECISIONS = {
    "funding_collection_complete",
    "funding_collection_complete_oi_not_ready",
}


def validate_derivatives_funding_oi_collection_report_v9_53(report: dict[str, Any], *, mode: str = "full") -> dict[str, Any]:
    errors: list[str] = []
    if report.get("version") != "V9.53":
        errors.append("version mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("invalid decision")
    if report.get("decision") in SUCCESS_DECISIONS:
        funding = report.get("funding", {})
        if funding.get("quality_status") != "PASS":
            errors.append("funding quality must pass on success")
        if int(funding.get("missing_intervals") or 0) != 0:
            errors.append("funding success cannot have missing intervals")
        if int(funding.get("duplicate_funding_time") or 0) != 0:
            errors.append("funding success cannot have duplicate funding_time")
        if report.get("oi", {}).get("collected") is not False:
            errors.append("V9.53 expected OI to remain uncollected")
        if mode == "full":
            path = Path(funding.get("silver_path", ""))
            if not path.exists():
                errors.append(f"missing silver funding file: {path}")
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
    for key in ["api_key_used", "private_endpoint_used", "exchange_auth_used", "websocket_live_used"]:
        if flags.get(key) is not False:
            errors.append(f"safety flag must be false: {key}")
    if mode not in {"full", "audit-lite"}:
        errors.append("unknown validation mode")
    return {"version": "V9.53", "mode": mode, "passed": not errors, "errors": errors}


def validate_derivatives_funding_oi_collection_file_v9_53(root: Path = Path("."), *, mode: str = "full") -> dict[str, Any]:
    path = root / REPORT_JSON_PATH
    if not path.exists():
        return {"version": "V9.53", "mode": mode, "passed": False, "errors": [f"missing report: {path}"]}
    return validate_derivatives_funding_oi_collection_report_v9_53(json.loads(path.read_text(encoding="utf-8")), mode=mode)
