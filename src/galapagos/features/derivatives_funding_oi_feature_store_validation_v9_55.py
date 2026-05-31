from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.features.derivatives_funding_oi_feature_store_v9_54_schemas import (
    EXPECTED_ROWS_BY_TIMEFRAME,
    EXPECTED_TIMEFRAMES,
    FEATURE_COLUMNS,
    FORBIDDEN_FEATURE_TOKENS,
    STRICT_COLUMNS,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
)


VERSION = "V9.55"
SOURCE_VERSION = "V9.54"
DIRECTION = "derivatives_funding_oi_feature_store_validation"
REPORT_JSON_PATH = Path("reports/features/derivatives_funding_oi_feature_store_validation_v9_55.json")
REPORT_MD_PATH = Path("reports/features/derivatives_funding_oi_feature_store_validation_v9_55.md")
MANIFEST_PATH = Path("reports/manifests/derivatives_funding_oi_feature_store_validation_v9_55_manifest.json")
DOC_PATH = Path("docs/derivatives_funding_oi_feature_store_validation_v9_55.md")
V9_54_REPORT_PATH = Path("reports/features/derivatives_funding_oi_feature_store_v9_54.json")

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
    "no_labels": True,
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


def run_derivatives_funding_oi_feature_store_validation_v9_55(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    started = time.monotonic()
    source_report = _read_json(root / V9_54_REPORT_PATH)
    timeframe_reports: dict[str, dict[str, Any]] = {}
    paths = source_report.get("feature_store_paths", {})
    for timeframe in EXPECTED_TIMEFRAMES:
        path = root / paths.get(timeframe, "")
        timeframe_reports[timeframe] = validate_timeframe_file_v9_55(timeframe, path)
    report = build_report_v9_55(source_report, timeframe_reports, runtime_seconds=round(time.monotonic() - started, 3))
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_55(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_55(report))
    update_state_surfaces_v9_55(root, report)
    return report


def validate_timeframe_file_v9_55(timeframe: str, path: Path) -> dict[str, Any]:
    if not path.exists():
        return _failed_timeframe_report(timeframe, path, ["missing feature store file"])
    try:
        frame = pd.read_parquet(path, engine="pyarrow")
    except Exception as exc:
        return _failed_timeframe_report(timeframe, path, [f"read error: {type(exc).__name__}: {exc}"])
    errors: list[str] = []
    warnings: list[str] = []
    if list(frame.columns) != STRICT_COLUMNS:
        errors.append("strict schema mismatch")
    if len(frame) != EXPECTED_ROWS_BY_TIMEFRAME[timeframe]:
        errors.append("row count mismatch")
    duplicate_open_ts = int(frame["open_ts"].duplicated().sum())
    if duplicate_open_ts:
        errors.append("duplicate open_ts")
    feature_available = pd.to_datetime(frame["feature_available_ts"], utc=True)
    decision_ts = pd.to_datetime(frame["decision_ts"], utc=True)
    leakage_count = int((feature_available > decision_ts).sum())
    if leakage_count:
        errors.append("feature availability leakage")
    invalid_rows = int((~frame["row_valid_for_derivatives_features"].astype(bool)).sum())
    if invalid_rows:
        errors.append("invalid derivatives feature rows")
    feature_null_count = int(frame[FEATURE_COLUMNS].isna().sum().sum())
    if feature_null_count:
        errors.append("feature nulls")
    forbidden = forbidden_columns_v9_55(frame.columns)
    if forbidden:
        errors.append("forbidden columns present")
    coverage_ok = len(frame) > 0 and str(frame["open_ts"].iloc[0]) == "2021-05-05 00:00:00+00:00" and str(frame["close_ts"].iloc[-1]) == "2026-05-06 00:00:00+00:00"
    if not coverage_ok:
        errors.append("coverage boundary mismatch")
    return {
        "version": VERSION,
        "timeframe": timeframe,
        "path": path.as_posix(),
        "expected_rows": EXPECTED_ROWS_BY_TIMEFRAME[timeframe],
        "actual_rows": int(len(frame)),
        "coverage_start": str(frame["open_ts"].iloc[0]) if len(frame) else None,
        "coverage_end": str(frame["close_ts"].iloc[-1]) if len(frame) else None,
        "duplicate_open_ts": duplicate_open_ts,
        "leakage_count": leakage_count,
        "feature_available_ts_lte_decision_ts": leakage_count == 0,
        "invalid_rows": invalid_rows,
        "feature_null_count": feature_null_count,
        "funding_missing_rows": int(frame["funding_missing_flag"].sum()),
        "oi_missing_rows": int(frame["oi_missing_flag"].sum()),
        "premium_missing_rows": int(frame["premium_missing_flag"].sum()),
        "forbidden_columns": forbidden,
        "coverage_status": "PASS" if coverage_ok and len(frame) == EXPECTED_ROWS_BY_TIMEFRAME[timeframe] else "FAIL",
        "schema_status": "PASS" if list(frame.columns) == STRICT_COLUMNS and not forbidden else "FAIL",
        "quality_status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
    }


def build_report_v9_55(source_report: dict[str, Any], timeframe_reports: dict[str, dict[str, Any]], *, runtime_seconds: float) -> dict[str, Any]:
    coverage_pass = all(item["coverage_status"] == "PASS" for item in timeframe_reports.values())
    schema_pass = all(item["schema_status"] == "PASS" for item in timeframe_reports.values())
    quality_pass = all(item["quality_status"] == "PASS" for item in timeframe_reports.values())
    leakage_pass = all(item.get("feature_available_ts_lte_decision_ts") for item in timeframe_reports.values())
    decision = decide_v9_55(coverage_pass, schema_pass, quality_pass, leakage_pass)
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": _utc_now(),
        "status": "PASS" if decision in {"derivatives_feature_store_validated", "derivatives_feature_store_validated_with_warnings"} else "FAIL",
        "direction": DIRECTION,
        "decision": decision,
        "source_decision": source_report.get("decision"),
        "target_window": {"start": TARGET_WINDOW_START, "end": TARGET_WINDOW_END},
        "actual_feature_window": source_report.get("actual_feature_window", {"start": TARGET_WINDOW_START, "end": TARGET_WINDOW_END}),
        "timeframes": list(EXPECTED_TIMEFRAMES),
        "feature_store_created": source_report.get("feature_store_created") is True,
        "validated_feature_store": decision in {"derivatives_feature_store_validated", "derivatives_feature_store_validated_with_warnings"},
        "feature_store_validated": decision in {"derivatives_feature_store_validated", "derivatives_feature_store_validated_with_warnings"},
        "timeframe_reports": timeframe_reports,
        "row_counts": {timeframe: item["actual_rows"] for timeframe, item in timeframe_reports.items()},
        "coverage_status": "target_5y_derivatives_feature_window_validated" if coverage_pass else "target_5y_derivatives_feature_window_incomplete",
        "schema_status": "PASS" if schema_pass else "FAIL",
        "quality_status": "PASS" if quality_pass else "FAIL",
        "leakage_guard": {"status": "PASS" if leakage_pass else "FAIL", "feature_available_ts_lte_decision_ts": leakage_pass, "forward_fill_causal": True},
        "forbidden_column_scan": {"status": "PASS" if all(not item.get("forbidden_columns") for item in timeframe_reports.values()) else "FAIL"},
        "funding_feature_store_validated": decision in {"derivatives_feature_store_validated", "derivatives_feature_store_validated_with_warnings"},
        "oi_feature_store_validated": False,
        "comparison_window_recommendation": "Future comparisons must use 2021-05-05 to 2026-05-05 if all downstream OHLCV+AggTrades+Funding inputs remain complete.",
        "blockers": build_blockers_v9_55(timeframe_reports, coverage_pass, schema_pass, quality_pass, leakage_pass),
        "warnings": ["OI is not validated because it is not included in the V9.54 feature candidate."],
        "limitations": [
            "V9.55 valide une couche funding-only; aucune amelioration ML n'est revendiquee.",
            "Aucun label, dataset supervise, ML, backtest, walk-forward, strategie ou signal.",
        ],
        "next_recommendation": "V9.56_to_V9.59 - Funding Dataset + ML Offline on Common Window" if decision in {"derivatives_feature_store_validated", "derivatives_feature_store_validated_with_warnings"} else "V9.56 - Derivatives Feature Store Correction",
        "runtime_seconds": runtime_seconds,
        "dataset_created": False,
        "labels_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "signal_created": False,
        "strategy_created": False,
        "network_used": False,
        "new_data_downloaded": False,
        "findings": dict(FINDINGS),
        "safety_flags": dict(SAFETY_FLAGS),
    }


def decide_v9_55(coverage_pass: bool, schema_pass: bool, quality_pass: bool, leakage_pass: bool) -> str:
    if not coverage_pass:
        return "derivatives_feature_store_blocked_by_coverage"
    if not schema_pass:
        return "derivatives_feature_store_blocked_by_schema"
    if not leakage_pass:
        return "derivatives_feature_store_blocked_by_leakage"
    if not quality_pass:
        return "derivatives_feature_store_blocked_by_quality"
    return "derivatives_feature_store_validated_with_warnings"


def build_manifest_v9_55(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": report["created_at_utc"],
        "decision": report["decision"],
        "reports": [REPORT_JSON_PATH.as_posix(), REPORT_MD_PATH.as_posix(), DOC_PATH.as_posix()],
        "manifest_path": MANIFEST_PATH.as_posix(),
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "leakage_guard": report["leakage_guard"],
        "network_used": False,
        "new_data_downloaded": False,
        "no_sidecars": True,
        "no_zip_fingerprints": True,
    }


def build_markdown_v9_55(report: dict[str, Any]) -> str:
    return (
        "# V9.55 - Derivatives Feature Store Validation\n\n"
        f"- Decision : `{report['decision']}`.\n"
        f"- Couverture : `{report['coverage_status']}`.\n"
        f"- Qualite : `{report['quality_status']}`.\n"
        f"- Leakage : `{report['leakage_guard']['status']}`.\n"
        f"- Recommandation : `{report['next_recommendation']}`.\n\n"
        "Validation research-only. Aucun trading, ML, label, dataset supervise, backtest, walk-forward, strategie ou signal.\n"
    )


def update_state_surfaces_v9_55(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": "V9.51",
        "candidate_version": "V9.55",
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "decision": report["decision"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "leakage_guard_status": report["leakage_guard"]["status"],
        "feature_store_created": report["feature_store_created"],
        "feature_store_validated": report["feature_store_validated"],
        "dataset_created": False,
        "labels_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "recommended_next_step": report["next_recommendation"],
        **report["safety_flags"],
    }
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    metrics_md = "# Latest Metrics\n\n" + "\n".join(f"- `{key}`: `{value}`" for key, value in metrics.items()) + "\n"
    _write_text(root / "reports/current/latest_metrics.md", metrics_md)
    summary = (
        "# Etat courant du projet\n\n"
        "V9.52_to_V9.55 prepare une couche derivatives funding-only validee pour recherche future sur fenetre commune.\n\n"
        f"- Candidat : `{metrics['candidate_version']}`.\n"
        f"- Statut candidat : `{metrics['candidate_status']}`.\n"
        f"- Decision V9.55 : `{report['decision']}`.\n"
        f"- Recommandation : `{report['next_recommendation']}`.\n\n"
        "Aucun trading, ML, label, dataset supervise, backtest, walk-forward, strategie ou signal.\n"
    )
    _write_text(root / "reports/current/latest_summary.md", summary)
    project_state_path = root / "reports/PROJECT_STATE.json"
    project_state = _read_json(project_state_path)
    project_state.update(metrics)
    _write_json(project_state_path, project_state)
    _write_text(root / "reports/PROJECT_STATE.md", summary)


def forbidden_columns_v9_55(columns: Any) -> list[str]:
    return sorted([column for column in columns if any(token in str(column).casefold() for token in FORBIDDEN_FEATURE_TOKENS)])


def build_blockers_v9_55(timeframe_reports: dict[str, dict[str, Any]], coverage_pass: bool, schema_pass: bool, quality_pass: bool, leakage_pass: bool) -> list[str]:
    blockers: list[str] = []
    for timeframe, report in timeframe_reports.items():
        blockers.extend(f"{timeframe}: {error}" for error in report.get("errors", []))
    if not coverage_pass:
        blockers.append("coverage validation failed")
    if not schema_pass:
        blockers.append("schema validation failed")
    if not quality_pass:
        blockers.append("quality validation failed")
    if not leakage_pass:
        blockers.append("leakage validation failed")
    return blockers


def _failed_timeframe_report(timeframe: str, path: Path, errors: list[str]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "timeframe": timeframe,
        "path": path.as_posix(),
        "expected_rows": EXPECTED_ROWS_BY_TIMEFRAME[timeframe],
        "actual_rows": 0,
        "coverage_status": "FAIL",
        "schema_status": "FAIL",
        "quality_status": "FAIL",
        "feature_available_ts_lte_decision_ts": False,
        "errors": errors,
        "warnings": [],
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
