from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_v9_47 import combined_feature_output_path_v9_47
from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_v9_47_schemas import (
    EXPECTED_ROWS_BY_TIMEFRAME,
    EXPECTED_TIMEFRAMES,
    FEATURE_COLUMNS,
    FEATURE_FAMILIES,
    FORBIDDEN_FEATURE_COLUMNS,
    STRICT_COLUMNS,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
)


VERSION = "V9.48"
SOURCE_VERSION = "V9.47"
LAST_VALIDATED_VERSION = "V9.47"
DIRECTION = "ohlcv_aggtrades_exact_5y_feature_store_validation"
REPORT_JSON_PATH = Path("reports/features/ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.json")
REPORT_MD_PATH = Path("reports/features/ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.md")
MANIFEST_PATH = Path("reports/manifests/ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48_manifest.json")
DOC_PATH = Path("docs/ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.md")
INPUT_PATHS = {
    "v9_47": Path("reports/features/ohlcv_aggtrades_exact_5y_feature_store_v9_47.json"),
    "v9_47_manifest": Path("reports/manifests/ohlcv_aggtrades_exact_5y_feature_store_v9_47_manifest.json"),
    "v9_46": Path("reports/features/aggtrades_exact_5y_feature_enrichment_validation_v9_46.json"),
    "v9_45": Path("reports/features/aggtrades_exact_5y_feature_enrichment_v9_45.json"),
    "v9_38": Path("reports/features/ohlcv_aggtrades_5y_feature_store_validation_v9_38.json"),
    "v9_37": Path("reports/features/ohlcv_aggtrades_5y_feature_store_v9_37.json"),
}
ALLOWED_DECISIONS = {
    "combined_feature_store_validated",
    "combined_feature_store_validated_with_warnings",
    "combined_feature_store_blocked_by_alignment",
    "combined_feature_store_blocked_by_schema",
    "combined_feature_store_blocked_by_quality",
    "combined_feature_store_blocked_by_leakage",
}
FINDINGS = {
    "robust_edge_claimed": False,
    "strategy_validated": False,
    "backtest_performed": False,
    "actionable_signal_produced": False,
    "walk_forward_validated_for_trading": False,
    "trading_allowed": False,
    "paper_live_allowed": False,
    "real_trading_allowed": False,
}
SAFETY_FLAGS = {
    "no_trading": True,
    "no_paper_live": True,
    "no_orders": True,
    "no_backtest": True,
    "no_walk_forward": True,
    "no_ml": True,
    "no_dataset_supervised": True,
    "no_strategy": True,
    "no_actionable_signal": True,
    "no_persistent_model": True,
    "api_key_used": False,
    "private_endpoint_used": False,
    "exchange_auth_used": False,
    "websocket_live_used": False,
    "network_used": False,
    "no_new_data_download": True,
    "no_destructive_cleanup": True,
    "no_sidecars": True,
    "no_zip_fingerprints": True,
}


def run_ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48(root: Path = Path("."), *, mode: str = "full-local") -> dict[str, Any]:
    root = root.resolve()
    started = time.monotonic()
    inputs = {name: _read_optional_json(root / path) for name, path in INPUT_PATHS.items()}
    readiness = _readiness(inputs)
    timeframe_results: dict[str, Any] = {}
    errors: list[str] = []
    warnings: list[str] = []
    if not readiness["ready"]:
        errors.extend(readiness["errors"])
    elif mode == "full-local":
        for timeframe in EXPECTED_TIMEFRAMES:
            result = validate_timeframe_v9_48(root, timeframe)
            timeframe_results[timeframe] = result
            errors.extend(f"{timeframe}: {error}" for error in result["errors"])
            warnings.extend(f"{timeframe}: {warning}" for warning in result["warnings"])
    else:
        warnings.append("audit-lite mode: full feature parquet files are not required")
    coverage_pass = mode == "audit-lite" or all(item.get("coverage_status") == "PASS" for item in timeframe_results.values())
    schema_pass = mode == "audit-lite" or all(item.get("schema_status") == "PASS" for item in timeframe_results.values())
    quality_pass = mode == "audit-lite" or all(item.get("quality_status") == "PASS" for item in timeframe_results.values())
    leakage_pass = mode == "audit-lite" or all(item.get("leakage_guard_status") == "PASS" for item in timeframe_results.values())
    forbidden_pass = mode == "audit-lite" or all(not item.get("forbidden_columns") for item in timeframe_results.values())
    decision = _decide(readiness, coverage_pass, schema_pass, quality_pass, leakage_pass, forbidden_pass, warnings, errors)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if decision in {"combined_feature_store_validated", "combined_feature_store_validated_with_warnings"} else "FAIL",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "validation_mode": mode,
        "target_window": {"start": TARGET_WINDOW_START, "end": TARGET_WINDOW_END},
        "timeframes": list(EXPECTED_TIMEFRAMES),
        "readiness": readiness,
        "full_local_validation": timeframe_results,
        "row_counts": {tf: item.get("row_count", 0) for tf, item in timeframe_results.items()},
        "base_feature_columns_count": len(FEATURE_FAMILIES["base_v9_37"]),
        "exact_feature_columns_count": len(FEATURE_FAMILIES["exact_aggtrades_v9_45"]),
        "combined_feature_columns_count": len(FEATURE_COLUMNS),
        "collision_policy": inputs.get("v9_47", {}).get("collision_policy"),
        "coverage_status": "target_5y_combined_feature_window_complete" if coverage_pass else "target_5y_combined_feature_window_incomplete",
        "schema_status": "PASS" if schema_pass else "FAIL",
        "quality_status": "PASS" if quality_pass and not errors else "FAIL",
        "leakage_guard_status": "PASS" if leakage_pass else "FAIL",
        "forbidden_column_scan": {"status": "PASS" if forbidden_pass else "FAIL"},
        "warnings": sorted(set(warnings)),
        "errors": errors,
        "decision": decision,
        "next_recommendation": "V9.49 - Combined Features 5Y Dataset" if decision in {"combined_feature_store_validated", "combined_feature_store_validated_with_warnings"} else "V9.49 - Combined Feature Store Correction",
        "runtime_seconds": round(time.monotonic() - started, 3),
        "dataset_created": False,
        "labels_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "signal_created": False,
        "strategy_created": False,
        "network_used": False,
        "new_data_downloaded": False,
        "findings": FINDINGS,
        "safety_flags": SAFETY_FLAGS,
    }
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_48(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_48(report))
    update_state_surfaces_v9_48(root, report)
    return report


def validate_timeframe_v9_48(root: Path, timeframe: str) -> dict[str, Any]:
    path = combined_feature_output_path_v9_47(root, timeframe)
    errors: list[str] = []
    warnings: list[str] = []
    if not path.is_file():
        return {"timeframe": timeframe, "path": path.as_posix(), "row_count": 0, "errors": ["missing feature parquet"], "warnings": [], "coverage_status": "FAIL", "schema_status": "FAIL", "quality_status": "FAIL", "leakage_guard_status": "FAIL", "forbidden_columns": []}
    frame = pd.read_parquet(path, engine="pyarrow")
    row_count = int(len(frame))
    missing_columns = [column for column in STRICT_COLUMNS if column not in frame.columns]
    extra_columns = [column for column in frame.columns if column not in STRICT_COLUMNS]
    if missing_columns or extra_columns or list(frame.columns) != STRICT_COLUMNS:
        errors.append("strict schema mismatch")
    if row_count != EXPECTED_ROWS_BY_TIMEFRAME[timeframe]:
        errors.append("row count mismatch")
    duplicate_counts = {column: int(frame[column].duplicated().sum()) for column in ["event_ts", "open_ts", "close_ts"]}
    if any(duplicate_counts.values()):
        errors.append("duplicate timestamps")
    if not bool(frame["open_ts"].is_monotonic_increasing):
        errors.append("open_ts not monotone")
    leakage_feature = int((pd.to_datetime(frame["feature_available_ts"], utc=True) > pd.to_datetime(frame["decision_ts"], utc=True)).sum())
    leakage_available = int((pd.to_datetime(frame["available_ts"], utc=True) > pd.to_datetime(frame["decision_ts"], utc=True)).sum())
    if leakage_feature or leakage_available:
        errors.append("availability leakage")
    forbidden = sorted([column for column in frame.columns if any(token in column.casefold() for token in FORBIDDEN_FEATURE_COLUMNS)])
    if forbidden:
        errors.append("forbidden columns present")
    warmup_mask = frame["warmup_row"].astype(bool)
    non_warmup_nulls = int(frame.loc[~warmup_mask, FEATURE_COLUMNS].isna().sum().sum())
    invalid_non_warmup = int((~frame.loc[~warmup_mask, "row_valid_for_combined_features"].astype(bool)).sum())
    warmup_nulls = int(frame.loc[warmup_mask, FEATURE_COLUMNS].isna().sum().sum())
    if warmup_nulls:
        warnings.append("warmup rows contain documented rolling-window nulls")
    if non_warmup_nulls or invalid_non_warmup:
        errors.append("non-warmup feature quality failure")
    return {
        "timeframe": timeframe,
        "path": path.as_posix(),
        "bytes": path.stat().st_size,
        "row_count": row_count,
        "expected_rows": EXPECTED_ROWS_BY_TIMEFRAME[timeframe],
        "base_feature_columns_count": len(FEATURE_FAMILIES["base_v9_37"]),
        "exact_feature_columns_count": len(FEATURE_FAMILIES["exact_aggtrades_v9_45"]),
        "combined_feature_columns_count": len(FEATURE_COLUMNS),
        "duplicate_counts": duplicate_counts,
        "feature_available_ts_gt_decision_ts": leakage_feature,
        "available_ts_gt_decision_ts": leakage_available,
        "forbidden_columns": forbidden,
        "warmup_rows": int(frame["warmup_row"].sum()),
        "warmup_feature_null_count": warmup_nulls,
        "non_warmup_feature_null_count": non_warmup_nulls,
        "invalid_non_warmup_rows": invalid_non_warmup,
        "coverage_status": "PASS" if row_count == EXPECTED_ROWS_BY_TIMEFRAME[timeframe] else "FAIL",
        "schema_status": "PASS" if not missing_columns and not extra_columns and list(frame.columns) == STRICT_COLUMNS else "FAIL",
        "quality_status": "PASS" if not errors else "FAIL",
        "leakage_guard_status": "PASS" if leakage_feature == 0 and leakage_available == 0 else "FAIL",
        "errors": errors,
        "warnings": warnings,
    }


def _readiness(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    v47 = inputs.get("v9_47", {})
    if v47.get("decision") not in {"ohlcv_aggtrades_exact_5y_feature_store_created", "ohlcv_aggtrades_exact_5y_feature_store_created_with_warnings"}:
        errors.append("V9.47 combined feature store decision is not successful")
    if v47.get("quality_status") != "PASS":
        errors.append("V9.47 quality is not PASS")
    if v47.get("combined_feature_columns_count") != len(FEATURE_COLUMNS):
        errors.append("V9.47 combined feature count mismatch")
    return {"ready": not errors, "errors": errors, "source_decision": v47.get("decision"), "source_quality_status": v47.get("quality_status")}


def _decide(readiness: dict[str, Any], coverage_pass: bool, schema_pass: bool, quality_pass: bool, leakage_pass: bool, forbidden_pass: bool, warnings: list[str], errors: list[str]) -> str:
    if not readiness["ready"]:
        return "combined_feature_store_blocked_by_alignment"
    if not schema_pass:
        return "combined_feature_store_blocked_by_schema"
    if not leakage_pass or not forbidden_pass:
        return "combined_feature_store_blocked_by_leakage"
    if not quality_pass or errors:
        return "combined_feature_store_blocked_by_quality"
    if not coverage_pass:
        return "combined_feature_store_blocked_by_alignment"
    if warnings:
        return "combined_feature_store_validated_with_warnings"
    return "combined_feature_store_validated"


def build_manifest_v9_48(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": report["created_at_utc"],
        "decision": report["decision"],
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "leakage_guard_status": report["leakage_guard_status"],
        "row_counts": report["row_counts"],
        "combined_feature_columns_count": report["combined_feature_columns_count"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_48(report: dict[str, Any]) -> str:
    lines = [
        "# V9.48 - Validation feature store combine 5Y",
        "",
        f"- Decision : `{report['decision']}`.",
        f"- Recommandation : `{report['next_recommendation']}`.",
        f"- Qualite : `{report['quality_status']}`.",
        f"- Coverage : `{report['coverage_status']}`.",
        f"- Leakage guard : `{report['leakage_guard_status']}`.",
        f"- Colonnes combinees : `{report['combined_feature_columns_count']}`.",
        f"- Row counts : `{report['row_counts']}`.",
        "",
        "Aucun label, dataset supervise, ML, backtest, walk-forward, strategie ou signal n'est cree.",
    ]
    if report["warnings"]:
        lines.extend(["", "## Warnings", *[f"- {warning}" for warning in report["warnings"]]])
    if report["errors"]:
        lines.extend(["", "## Erreurs", *[f"- {error}" for error in report["errors"]]])
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_48(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "direction": DIRECTION,
        "decision_v9_48": report["decision"],
        "recommended_next_step": report["next_recommendation"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "leakage_guard_status": report["leakage_guard_status"],
        "dataset_created": False,
        "ml_executed": False,
        **SAFETY_FLAGS,
    }
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    text = "# Synthese courante\n\n" f"V9.48 valide le feature store combine V9.47. Decision : `{report['decision']}`.\n"
    _write_text(root / "reports/current/latest_metrics.md", text)
    _write_text(root / "reports/current/latest_summary.md", text)
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_optional_json(state_path)
    state.update(metrics)
    _write_json(state_path, state)
    _write_text(root / "reports/PROJECT_STATE.md", text)


def _read_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
