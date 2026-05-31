from __future__ import annotations

import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.features.ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59_schemas import (
    BASE_AUDIT_COLUMNS,
    BASE_FEATURE_ROOT,
    BASE_FEATURE_STORE_VERSION,
    BASE_FEATURE_VALIDATION_VERSION,
    COMMON_WINDOW_END,
    COMMON_WINDOW_LABEL,
    COMMON_WINDOW_POLICY,
    COMMON_WINDOW_START,
    DIRECTION,
    DOC_PATH,
    FEATURE_COLUMNS,
    FEATURE_RUN_ID_PREFIX,
    FEATURE_SCHEMA_VERSION,
    FINDINGS,
    FORBIDDEN_FEATURE_TOKENS,
    FUNDING_AUDIT_COLUMNS,
    FUNDING_FEATURE_ROOT,
    FUNDING_FEATURE_STORE_VERSION,
    FUNDING_FEATURE_VALIDATION_VERSION,
    INPUT_PATHS,
    MANIFEST_PATH,
    MARKET_TYPE,
    METADATA_COLUMNS,
    OUTPUT_ROOT,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SAFETY_FLAGS,
    SOURCE,
    SOURCE_VERSION,
    STRICT_COLUMNS,
    SYMBOL,
    TIMEFRAMES,
    VENUE,
    VERSION,
)


SUCCESS_DECISIONS = {
    "funding_common_window_feature_store_created",
    "funding_common_window_feature_store_created_with_warnings",
}


def run_ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    preflight = build_preflight_v9_59(root, inputs)
    run_id = f"{FEATURE_RUN_ID_PREFIX}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    output_paths = {timeframe: feature_output_path_v9_59(root, timeframe) for timeframe in TIMEFRAMES}
    timeframe_reports: dict[str, dict[str, Any]] = {}
    if preflight["safe_to_run"]:
        workers = min(int(os.environ.get("GALAPAGOS_V9_59_WORKERS", "4")), len(TIMEFRAMES))
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(build_timeframe_v9_59, root, timeframe, run_id): timeframe for timeframe in TIMEFRAMES}
            for future in as_completed(futures):
                timeframe = futures[future]
                timeframe_reports[timeframe] = future.result()
                print(f"[V9.59] timeframe_done={timeframe} status={timeframe_reports[timeframe]['quality_status']}", flush=True)
    else:
        for timeframe in TIMEFRAMES:
            timeframe_reports[timeframe] = _blocked_timeframe_report(timeframe, output_paths[timeframe], preflight["errors"])
    timeframe_reports = {timeframe: timeframe_reports[timeframe] for timeframe in TIMEFRAMES}
    report = build_report_v9_59(
        inputs=inputs,
        preflight=preflight,
        output_paths=output_paths,
        timeframe_reports=timeframe_reports,
        runtime_seconds=round(time.monotonic() - started, 3),
    )
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_59(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_59(report))
    return report


def build_timeframe_v9_59(root: Path, timeframe: str, run_id: str) -> dict[str, Any]:
    base_path = base_feature_path_v9_59(root, timeframe)
    funding_path = funding_feature_path_v9_59(root, timeframe)
    output_path = feature_output_path_v9_59(root, timeframe)
    base = pd.read_parquet(base_path, engine="pyarrow")
    funding = pd.read_parquet(funding_path, engine="pyarrow")
    merged = merge_feature_frames_v9_59(base, funding, timeframe=timeframe, run_id=run_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(output_path, index=False, engine="pyarrow", compression="zstd")
    return validate_feature_frame_v9_59(merged, timeframe=timeframe, output_path=output_path)


def merge_feature_frames_v9_59(base: pd.DataFrame, funding: pd.DataFrame, *, timeframe: str, run_id: str) -> pd.DataFrame:
    start = pd.Timestamp(COMMON_WINDOW_START)
    end = pd.Timestamp(COMMON_WINDOW_END)
    for frame in (base, funding):
        for column in ["event_ts", "open_ts", "close_ts", "decision_ts", "available_ts", "feature_available_ts"]:
            frame[column] = pd.to_datetime(frame[column], utc=True)
    base = base.loc[(base["decision_ts"] > start) & (base["decision_ts"] <= end)].sort_values("decision_ts", kind="mergesort").reset_index(drop=True)
    funding = funding.sort_values("decision_ts", kind="mergesort").reset_index(drop=True)
    if len(base) != len(funding):
        raise ValueError(f"{timeframe}: base/funding row count mismatch {len(base)} != {len(funding)}")
    for column in ["event_ts", "open_ts", "close_ts", "decision_ts"]:
        if not base[column].equals(funding[column]):
            raise ValueError(f"{timeframe}: base/funding alignment mismatch on {column}")
    collisions = sorted(set(FEATURE_COLUMNS) & set(METADATA_COLUMNS))
    if collisions:
        raise ValueError(f"{timeframe}: feature/metadata collisions: {collisions}")
    feature_available = pd.concat([base["feature_available_ts"], funding["feature_available_ts"]], axis=1).max(axis=1)
    available_ts = pd.concat([base["available_ts"], funding["available_ts"]], axis=1).max(axis=1)
    out = pd.DataFrame(
        {
            "source": SOURCE,
            "venue": VENUE,
            "market_type": MARKET_TYPE,
            "symbol": SYMBOL,
            "timeframe": timeframe,
            "event_ts": base["event_ts"],
            "open_ts": base["open_ts"],
            "close_ts": base["close_ts"],
            "decision_ts": base["decision_ts"],
            "available_ts": available_ts,
            "feature_available_ts": feature_available,
            "funding_common_feature_run_id": run_id,
            "funding_common_feature_schema_version": FEATURE_SCHEMA_VERSION,
            "source_base_feature_store_version": BASE_FEATURE_STORE_VERSION,
            "source_base_feature_validation_version": BASE_FEATURE_VALIDATION_VERSION,
            "source_funding_feature_store_version": FUNDING_FEATURE_STORE_VERSION,
            "source_funding_feature_validation_version": FUNDING_FEATURE_VALIDATION_VERSION,
            "source_window_start": COMMON_WINDOW_START,
            "source_window_end": COMMON_WINDOW_END,
            "actual_window_start": COMMON_WINDOW_START,
            "actual_window_end": COMMON_WINDOW_END,
            "common_window_policy": COMMON_WINDOW_POLICY,
        }
    )
    for column in FEATURE_COLUMNS:
        out[column] = funding[column] if column in funding.columns else base[column]
    for column in BASE_AUDIT_COLUMNS:
        out[column] = base[column]
    for column in FUNDING_AUDIT_COLUMNS:
        out[column] = funding[column]
    base_valid = base["row_valid_for_combined_features"].fillna(False).astype(bool)
    funding_valid = funding["row_valid_for_funding_features"].fillna(False).astype(bool)
    leakage = pd.to_datetime(out["feature_available_ts"], utc=True) > pd.to_datetime(out["decision_ts"], utc=True)
    out["funding_common_feature_null_count"] = (
        pd.to_numeric(base["combined_feature_null_count"], errors="coerce").fillna(0).astype("int64")
        + pd.to_numeric(funding["funding_feature_null_count"], errors="coerce").fillna(0).astype("int64")
    )
    out["funding_common_feature_error_count"] = (
        pd.to_numeric(base["combined_feature_error_count"], errors="coerce").fillna(0).astype("int64")
        + pd.to_numeric(funding["funding_feature_error_count"], errors="coerce").fillna(0).astype("int64")
        + leakage.astype("int64")
    )
    out["row_valid_for_funding_common_features"] = base_valid & funding_valid & ~leakage
    out["funding_common_feature_invalid_reason"] = ""
    out.loc[~base_valid, "funding_common_feature_invalid_reason"] = "base_feature_row_invalid"
    out.loc[base_valid & ~funding_valid, "funding_common_feature_invalid_reason"] = "funding_feature_row_invalid"
    out.loc[leakage, "funding_common_feature_invalid_reason"] = "feature_available_ts_after_decision_ts"
    return out[STRICT_COLUMNS]


def build_preflight_v9_59(root: Path, inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    funding_chain = inputs["funding_chain"].get("payload", {})
    funding_validation = inputs["funding_validation"].get("payload", {})
    base_validation = inputs["base_validation"].get("payload", {})
    if funding_chain.get("decision") != "funding_only_feature_store_validated_on_closed_common_window":
        errors.append("funding chain is not validated on closed common window")
    if funding_validation.get("decision") != "funding_only_feature_store_validated_with_warnings":
        errors.append("funding feature store validation is not PASS with expected warning decision")
    if base_validation.get("quality_status") != "PASS":
        errors.append("base V9.48 feature validation quality is not PASS")
    missing = []
    for timeframe in TIMEFRAMES:
        if not base_feature_path_v9_59(root, timeframe).is_file():
            missing.append(base_feature_path_v9_59(root, timeframe).as_posix())
        if not funding_feature_path_v9_59(root, timeframe).is_file():
            missing.append(funding_feature_path_v9_59(root, timeframe).as_posix())
    if missing:
        errors.append(f"missing feature inputs: {missing[:8]}")
    return {"safe_to_run": not errors, "errors": errors, "inputs_available": {name: item["available"] for name, item in inputs.items()}}


def validate_feature_frame_v9_59(frame: pd.DataFrame, *, timeframe: str, output_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if list(frame.columns) != STRICT_COLUMNS:
        errors.append("strict schema mismatch")
    duplicate_decision_ts = int(frame["decision_ts"].duplicated().sum())
    if duplicate_decision_ts:
        errors.append("duplicate decision_ts")
    leakage_count = int((pd.to_datetime(frame["feature_available_ts"], utc=True) > pd.to_datetime(frame["decision_ts"], utc=True)).sum())
    if leakage_count:
        errors.append("feature availability leakage")
    forbidden = forbidden_columns_v9_59(frame.columns)
    if forbidden:
        errors.append("forbidden columns present")
    invalid_rows = int((~frame["row_valid_for_funding_common_features"].astype(bool)).sum())
    if invalid_rows:
        warnings.append(f"{timeframe}: invalid/warmup rows retained for dataset-level filtering")
    return {
        "version": VERSION,
        "timeframe": timeframe,
        "output_path": output_path.as_posix(),
        "output_bytes": output_path.stat().st_size if output_path.exists() else 0,
        "row_count": int(len(frame)),
        "valid_row_count": int(frame["row_valid_for_funding_common_features"].sum()),
        "invalid_row_count": invalid_rows,
        "coverage_start": str(frame["open_ts"].iloc[0]) if len(frame) else None,
        "coverage_end": str(frame["close_ts"].iloc[-1]) if len(frame) else None,
        "decision_start": str(frame["decision_ts"].iloc[0]) if len(frame) else None,
        "decision_end": str(frame["decision_ts"].iloc[-1]) if len(frame) else None,
        "duplicate_decision_ts": duplicate_decision_ts,
        "leakage_count": leakage_count,
        "feature_available_ts_lte_decision_ts": leakage_count == 0,
        "forbidden_columns": forbidden,
        "schema_status": "PASS" if list(frame.columns) == STRICT_COLUMNS and not forbidden else "FAIL",
        "quality_status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
    }


def build_report_v9_59(
    *,
    inputs: dict[str, dict[str, Any]],
    preflight: dict[str, Any],
    output_paths: dict[str, Path],
    timeframe_reports: dict[str, dict[str, Any]],
    runtime_seconds: float,
) -> dict[str, Any]:
    coverage_pass = all(item.get("row_count", 0) > 0 for item in timeframe_reports.values())
    schema_pass = all(item.get("schema_status") == "PASS" for item in timeframe_reports.values())
    quality_pass = all(item.get("quality_status") == "PASS" for item in timeframe_reports.values())
    leakage_pass = all(item.get("feature_available_ts_lte_decision_ts") for item in timeframe_reports.values())
    warnings = sorted({warning for item in timeframe_reports.values() for warning in item.get("warnings", [])})
    decision = decide_v9_59(preflight, coverage_pass, schema_pass, quality_pass, leakage_pass, warnings)
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": _utc_now(),
        "status": "PASS" if decision in SUCCESS_DECISIONS else "FAIL",
        "direction": DIRECTION,
        "decision": decision,
        "actual_common_window": {"start": COMMON_WINDOW_START, "end": COMMON_WINDOW_END, "label": COMMON_WINDOW_LABEL},
        "timeframes": list(TIMEFRAMES),
        "source_inputs": {name: {"available": item["available"], "path": item["path"]} for name, item in inputs.items()},
        "preflight": preflight,
        "feature_store_created": decision in SUCCESS_DECISIONS,
        "feature_store_paths": {timeframe: path.as_posix() for timeframe, path in output_paths.items()},
        "row_counts": {timeframe: item.get("row_count", 0) for timeframe, item in timeframe_reports.items()},
        "valid_row_counts": {timeframe: item.get("valid_row_count", 0) for timeframe, item in timeframe_reports.items()},
        "invalid_row_counts": {timeframe: item.get("invalid_row_count", 0) for timeframe, item in timeframe_reports.items()},
        "feature_columns_count": len(FEATURE_COLUMNS),
        "base_feature_columns_count": len(FEATURE_COLUMNS) - 14,
        "funding_feature_columns_count": 14,
        "collision_policy": {"status": "PASS", "silent_overwrite": False, "collisions": []},
        "timeframe_reports": timeframe_reports,
        "coverage_status": "funding_common_window_feature_store_complete" if coverage_pass else "funding_common_window_feature_store_incomplete",
        "schema_status": "PASS" if schema_pass else "FAIL",
        "quality_status": "PASS" if quality_pass else "FAIL",
        "leakage_guard": {"status": "PASS" if leakage_pass else "FAIL", "feature_available_ts_lte_decision_ts": leakage_pass, "no_future_funding": leakage_pass},
        "forbidden_column_scan": {"status": "PASS" if all(not item.get("forbidden_columns") for item in timeframe_reports.values()) else "FAIL"},
        "warnings": warnings,
        "errors": build_errors_v9_59(preflight, timeframe_reports, coverage_pass, schema_pass, quality_pass, leakage_pass),
        "limitations": [
            "Feature store commun research-only sur fenetre funding fermee.",
            "Aucun label, dataset, ML, walk-forward, backtest, strategie ou signal n'est cree dans V9.59.",
        ],
        "next_recommendation": "V9.60 - Funding common window dataset" if decision in SUCCESS_DECISIONS else "V9.60 - Feature merge correction",
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


def decide_v9_59(preflight: dict[str, Any], coverage_pass: bool, schema_pass: bool, quality_pass: bool, leakage_pass: bool, warnings: list[str]) -> str:
    if not preflight["safe_to_run"] or not coverage_pass:
        return "funding_common_window_feature_store_blocked_by_alignment"
    if not leakage_pass:
        return "funding_common_window_feature_store_blocked_by_leakage"
    if not schema_pass:
        return "funding_common_window_feature_store_blocked_by_schema"
    if not quality_pass:
        return "funding_common_window_feature_store_blocked_by_quality"
    if warnings:
        return "funding_common_window_feature_store_created_with_warnings"
    return "funding_common_window_feature_store_created"


def build_errors_v9_59(preflight: dict[str, Any], timeframe_reports: dict[str, dict[str, Any]], coverage_pass: bool, schema_pass: bool, quality_pass: bool, leakage_pass: bool) -> list[str]:
    errors = list(preflight.get("errors", []))
    for timeframe, item in timeframe_reports.items():
        errors.extend(f"{timeframe}: {error}" for error in item.get("errors", []))
    if not coverage_pass:
        errors.append("coverage failed")
    if not schema_pass:
        errors.append("schema failed")
    if not quality_pass:
        errors.append("quality failed")
    if not leakage_pass:
        errors.append("leakage failed")
    return errors


def build_manifest_v9_59(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": report["created_at_utc"],
        "decision": report["decision"],
        "report_path": REPORT_JSON_PATH.as_posix(),
        "manifest_path": MANIFEST_PATH.as_posix(),
        "feature_store_paths": report["feature_store_paths"],
        "actual_common_window": report["actual_common_window"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "leakage_guard": report["leakage_guard"],
        "network_used": False,
        "new_data_downloaded": False,
        "safety_flags": report["safety_flags"],
        "no_sidecars": True,
        "no_zip_fingerprints": True,
    }


def build_markdown_v9_59(report: dict[str, Any]) -> str:
    return (
        "# V9.59 - Feature store commun OHLCV + aggTrades exact + funding\n\n"
        f"- Decision : `{report['decision']}`.\n"
        f"- Fenetre commune : `{report['actual_common_window']['start']}` -> `{report['actual_common_window']['end']}`.\n"
        f"- Feature store cree : `{report['feature_store_created']}`.\n"
        f"- Colonnes features : `{report['feature_columns_count']}`.\n"
        f"- Quality : `{report['quality_status']}`.\n"
        f"- Leakage : `{report['leakage_guard']['status']}`.\n\n"
        "Aucun trading, ordre, backtest, walk-forward, ML, strategie ou signal.\n"
    )


def base_feature_path_v9_59(root: Path, timeframe: str) -> Path:
    return root / BASE_FEATURE_ROOT / f"timeframe={timeframe}" / "window=2021-05-05_2026-05-05" / "features.parquet"


def funding_feature_path_v9_59(root: Path, timeframe: str) -> Path:
    return root / FUNDING_FEATURE_ROOT / f"timeframe={timeframe}" / f"window={COMMON_WINDOW_LABEL}" / "features.parquet"


def feature_output_path_v9_59(root: Path, timeframe: str) -> Path:
    return root / OUTPUT_ROOT / f"timeframe={timeframe}" / f"window={COMMON_WINDOW_LABEL}" / "features.parquet"


def forbidden_columns_v9_59(columns: Any) -> list[str]:
    return sorted([column for column in columns if any(token in str(column).casefold() for token in FORBIDDEN_FEATURE_TOKENS)])


def _blocked_timeframe_report(timeframe: str, output_path: Path, errors: list[str]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "timeframe": timeframe,
        "output_path": output_path.as_posix(),
        "row_count": 0,
        "valid_row_count": 0,
        "invalid_row_count": 0,
        "schema_status": "FAIL",
        "quality_status": "FAIL",
        "feature_available_ts_lte_decision_ts": False,
        "errors": errors,
        "warnings": [],
    }


def _load_input(root: Path, path: Path) -> dict[str, Any]:
    full = root / path
    return {"path": path.as_posix(), "available": full.is_file(), "payload": _read_json(full) if full.is_file() else {}}


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
