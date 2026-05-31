from __future__ import annotations

import io
import json
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pandas as pd


VERSION = "V9.53"
SOURCE_VERSION = "V9.52"
DIRECTION = "derivatives_funding_oi_collection"
SYMBOL = "BTCUSDT"
VENUE = "binance"
SOURCE = "binance_archive"
MARKET_TYPE = "futures_um"
TARGET_WINDOW_START = "2021-05-05"
TARGET_WINDOW_END = "2026-05-05"
HOST = "data.binance.vision"
BASE_URL = f"https://{HOST}/data/futures/um/monthly/fundingRate/{SYMBOL}"
REST_BASE_URL = "https://fapi.binance.com/fapi/v1/fundingRate"
TIMEOUT_SECONDS = 45

RAW_DIR = Path("data/raw/binance_public/futures_um/fundingRate/BTCUSDT")
SILVER_PATH = Path("data/silver/derivatives/binance_archive/futures_um/BTCUSDT/fundingRate/window=2021-05-05_2026-05-05/funding_rate.parquet")
REPORT_JSON_PATH = Path("reports/data/derivatives_funding_oi_collection_v9_53.json")
REPORT_MD_PATH = Path("reports/data/derivatives_funding_oi_collection_v9_53.md")
MANIFEST_PATH = Path("reports/manifests/derivatives_funding_oi_collection_v9_53_manifest.json")
DOC_PATH = Path("docs/derivatives_funding_oi_collection_v9_53.md")
READINESS_REPORT_PATH = Path("reports/research_decisions/derivatives_source_readiness_v9_52.json")

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
    "no_destructive_cleanup": True,
    "no_sidecars": True,
    "no_zip_fingerprints": True,
}

SUCCESS_DECISIONS = {
    "funding_collection_complete",
    "funding_collection_complete_oi_not_ready",
    "oi_collection_ready",
}


def run_derivatives_funding_oi_collection_v9_53(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    started = time.monotonic()
    readiness = _read_json(root / READINESS_REPORT_PATH)
    if readiness.get("decision") not in {
        "derivatives_source_readiness_funding_ready",
        "derivatives_source_readiness_funding_ready_oi_limited",
    }:
        report = _not_executed_report(readiness, "V9.52 did not authorize collection", time.monotonic() - started)
    else:
        report = collect_funding_window_v9_53(root, readiness, runtime_started=started)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_53(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_53(report))
    return report


def collect_funding_window_v9_53(root: Path, readiness: dict[str, Any], *, runtime_started: float) -> dict[str, Any]:
    raw_dir = root / RAW_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)
    month_reports: list[dict[str, Any]] = []
    frames: list[pd.DataFrame] = []
    for month in funding_months_v9_53(TARGET_WINDOW_START, TARGET_WINDOW_END):
        month_report, frame = collect_one_month_v9_53(raw_dir, month)
        month_reports.append(month_report)
        if frame is not None and not frame.empty:
            frames.append(frame)
    source_errors = [item for item in month_reports if item["status"] != "month_complete"]
    if _can_use_rest_tail_fallback(source_errors):
        tail_report, tail_frame = collect_rest_tail_v9_53(raw_dir)
        month_reports.append(tail_report)
        if tail_frame is not None and not tail_frame.empty:
            frames.append(tail_frame)
            source_errors = [item for item in month_reports if item["status"] not in {"month_complete", "rest_tail_complete"}]
    funding = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    normalized = normalize_funding_frame_v9_53(funding)
    quality = validate_funding_silver_v9_53(normalized)
    if not source_errors and quality["quality_status"] == "PASS":
        silver_path = root / SILVER_PATH
        if silver_path.exists():
            existing_quality = validate_funding_silver_v9_53(pd.read_parquet(silver_path, engine="pyarrow"))
            silver_write_status = "skipped_existing_valid_silver" if existing_quality["quality_status"] == "PASS" else "existing_silver_invalid_not_overwritten"
        else:
            silver_path.parent.mkdir(parents=True, exist_ok=True)
            normalized.to_parquet(silver_path, index=False, engine="pyarrow", compression="zstd")
            silver_write_status = "written"
    else:
        silver_write_status = "not_written_due_to_source_or_quality"
    any_downloaded = any(bool(item.get("downloaded")) for item in month_reports)
    silver_exists = (root / SILVER_PATH).exists()
    silver_bytes = (root / SILVER_PATH).stat().st_size if silver_exists else 0
    decision = decide_v9_53(source_errors, quality)
    rows = int(len(normalized))
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": _utc_now(),
        "status": "PASS" if decision in SUCCESS_DECISIONS else "FAIL",
        "direction": DIRECTION,
        "decision": decision,
        "readiness_decision": readiness.get("decision"),
        "source_host": HOST,
        "source_url_pattern": f"{BASE_URL}/{SYMBOL}-fundingRate-YYYY-MM.zip",
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "funding_collected": decision in {"funding_collection_complete", "funding_collection_complete_oi_not_ready"},
        "funding_usable": quality["quality_status"] == "PASS" and not source_errors,
        "funding": {
            "raw_files_count": sum(1 for item in month_reports if item["status"] == "month_complete"),
            "rest_tail_files_count": sum(1 for item in month_reports if item["status"] == "rest_tail_complete"),
            "raw_files_expected": len(funding_months_v9_53(TARGET_WINDOW_START, TARGET_WINDOW_END)),
            "raw_bytes_total": sum(int(item.get("raw_bytes", 0)) for item in month_reports),
            "rows": rows,
            "coverage_start": quality["coverage_start"],
            "coverage_end": quality["coverage_end"],
            "expected_funding_interval_hours": 8,
            "expected_intervals": quality["expected_intervals"],
            "missing_intervals": quality["missing_intervals"],
            "duplicate_funding_time": quality["duplicate_funding_time"],
            "funding_rate_nulls": quality["funding_rate_nulls"],
            "mark_price_nulls": quality["mark_price_nulls"],
            "quality_status": quality["quality_status"],
            "silver_path": SILVER_PATH.as_posix(),
            "silver_bytes": silver_bytes,
            "silver_write_status": silver_write_status,
            "tail_rest_fallback_used": any(item["status"] == "rest_tail_complete" for item in month_reports),
        },
        "oi": {
            "collected": False,
            "reason": "oi_collection_not_ready_history_limited",
            "coverage_start": None,
            "coverage_end": None,
            "history_limit_notes": "No proven multi-year no-key public archive was available in local evidence; REST openInterestHist is treated as history-limited.",
            "source_issue_notes": "OI is non-blocking for V9.53 funding-only feature readiness.",
        },
        "month_reports": month_reports,
        "source_errors": source_errors,
        "runtime_seconds": round(time.monotonic() - runtime_started, 3),
        "next_recommendation": "V9.54 - Funding / OI Feature Store Candidate" if decision in SUCCESS_DECISIONS else "V9.54 - Funding Source Correction",
        "warnings": ["OI is not included because historical coverage is not ready."],
        "limitations": [
            "V9.53 collecte uniquement fundingRate public historique depuis data.binance.vision.",
            "Aucune API privee, aucune cle, aucun websocket et aucun endpoint de trading.",
            "Aucun dataset supervise, label, ML, backtest, walk-forward, strategie ou signal n'est cree.",
        ],
        "collection_executed": True,
        "network_used": True,
        "network_scope": "public_archive_or_public_market_data_read_only",
        "new_data_downloaded": any_downloaded,
        "new_data_download_scope": "public_historical_funding_rate_only",
        "ingestion_executed": True,
        "ingestion_scope": "public_funding_bronze_silver_only",
        "feature_store_created": False,
        "feature_store_validated": False,
        "dataset_created": False,
        "labels_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "signal_created": False,
        "strategy_created": False,
        "findings": dict(FINDINGS),
        "safety_flags": {
            **SAFETY_FLAGS,
            "network_used": True,
            "new_data_downloaded": any_downloaded,
        },
    }


def collect_one_month_v9_53(raw_dir: Path, month: str) -> tuple[dict[str, Any], pd.DataFrame | None]:
    file_name = f"{SYMBOL}-fundingRate-{month}.zip"
    path = raw_dir / file_name
    url = f"{BASE_URL}/{file_name}"
    downloaded = False
    if not path.exists():
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
                payload = response.read()
            if not payload:
                return _month_report(month, path, url, "month_failed", "empty_download", downloaded), None
            path.write_bytes(payload)
            downloaded = True
        except Exception as exc:  # pragma: no cover - exercised by integration command, not unit tests
            return _month_report(month, path, url, "month_failed", f"{type(exc).__name__}: {exc}", downloaded), None
    try:
        payload = path.read_bytes()
        if not payload:
            return _month_report(month, path, url, "month_failed", "empty_raw_file", downloaded), None
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            names = [name for name in archive.namelist() if not name.endswith("/")]
            if len(names) != 1:
                return _month_report(month, path, url, "month_failed", f"expected_one_csv_found_{len(names)}", downloaded), None
            with archive.open(names[0]) as handle:
                frame = pd.read_csv(handle)
        frame["source_file"] = path.as_posix()
        return _month_report(month, path, url, "month_complete", None, downloaded), frame
    except Exception as exc:
        return _month_report(month, path, url, "month_failed", f"{type(exc).__name__}: {exc}", downloaded), None


def collect_rest_tail_v9_53(raw_dir: Path) -> tuple[dict[str, Any], pd.DataFrame | None]:
    rest_dir = raw_dir / "rest_tail"
    rest_dir.mkdir(parents=True, exist_ok=True)
    path = rest_dir / "BTCUSDT-fundingRate-2026-05-01_2026-05-05.json"
    start = pd.Timestamp("2026-05-01T00:00:00Z")
    end = pd.Timestamp("2026-05-05T16:00:00Z")
    params = {
        "symbol": SYMBOL,
        "startTime": int(start.timestamp() * 1000),
        "endTime": int(end.timestamp() * 1000),
        "limit": 1000,
    }
    url = f"{REST_BASE_URL}?{urllib.parse.urlencode(params)}"
    downloaded = False
    try:
        if not path.exists():
            with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read().decode("utf-8"))
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            downloaded = True
        else:
            payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list) or not payload:
            return _month_report("2026-05-rest-tail", path, url, "rest_tail_failed", "empty_or_invalid_rest_payload", downloaded), None
        frame = pd.DataFrame(payload)
        frame["source_file"] = path.as_posix()
        return _month_report("2026-05-rest-tail", path, url, "rest_tail_complete", None, downloaded), frame
    except Exception as exc:  # pragma: no cover - integration/network path
        return _month_report("2026-05-rest-tail", path, url, "rest_tail_failed", f"{type(exc).__name__}: {exc}", downloaded), None


def normalize_funding_frame_v9_53(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=funding_silver_columns_v9_53())
    source = frame.copy()
    time_column = "calc_time" if "calc_time" in source.columns else "fundingTime"
    rate_column = "last_funding_rate" if "last_funding_rate" in source.columns else "fundingRate"
    if time_column not in source.columns or rate_column not in source.columns:
        raise ValueError("funding source missing required time/rate columns")
    event_ts = pd.to_datetime(pd.to_numeric(source[time_column], errors="coerce"), unit="ms", utc=True)
    funding_rate = pd.to_numeric(source[rate_column], errors="coerce")
    interval = pd.to_numeric(source.get("funding_interval_hours", 8), errors="coerce")
    mark_price = pd.to_numeric(source["mark_price"], errors="coerce") if "mark_price" in source.columns else pd.Series(pd.NA, index=source.index, dtype="Float64")
    normalized = pd.DataFrame(
        {
            "source": SOURCE,
            "venue": VENUE,
            "market_type": MARKET_TYPE,
            "symbol": SYMBOL,
            "metric_name": "funding_rate",
            "funding_time": event_ts,
            "event_ts": event_ts,
            "available_ts": event_ts,
            "funding_interval_hours": interval.fillna(8).astype("int64"),
            "funding_rate": funding_rate,
            "mark_price": mark_price,
            "source_file": source.get("source_file", ""),
        }
    )
    start = pd.Timestamp(TARGET_WINDOW_START, tz="UTC")
    end = pd.Timestamp(TARGET_WINDOW_END, tz="UTC") + pd.Timedelta(days=1) - pd.Timedelta(milliseconds=1)
    normalized = normalized.loc[(normalized["funding_time"] >= start) & (normalized["funding_time"] <= end)].copy()
    normalized = normalized.sort_values("funding_time", kind="mergesort").drop_duplicates("funding_time", keep="last").reset_index(drop=True)
    normalized["row_valid"] = normalized["funding_time"].notna() & normalized["funding_rate"].notna() & (normalized["funding_interval_hours"] > 0)
    normalized["invalid_reason"] = ""
    normalized.loc[normalized["funding_time"].isna(), "invalid_reason"] = "missing_funding_time"
    normalized.loc[normalized["funding_rate"].isna(), "invalid_reason"] = "missing_funding_rate"
    return normalized[funding_silver_columns_v9_53()]


def validate_funding_silver_v9_53(frame: pd.DataFrame) -> dict[str, Any]:
    errors: list[str] = []
    if list(frame.columns) != funding_silver_columns_v9_53():
        errors.append("schema mismatch")
    if frame.empty:
        errors.append("empty funding frame")
    times = pd.to_datetime(frame.get("funding_time", pd.Series(dtype="datetime64[ns, UTC]")), utc=True)
    duplicate_count = int(times.duplicated().sum()) if not times.empty else 0
    if duplicate_count:
        errors.append("duplicate funding_time")
    null_rates = int(frame.get("funding_rate", pd.Series(dtype=float)).isna().sum()) if not frame.empty else 0
    if null_rates:
        errors.append("funding_rate nulls")
    available_violation = int((pd.to_datetime(frame.get("available_ts", []), utc=True) < times).sum()) if not frame.empty else 0
    if available_violation:
        errors.append("available_ts before funding_time")
    expected = pd.date_range(
        pd.Timestamp(TARGET_WINDOW_START, tz="UTC"),
        pd.Timestamp(TARGET_WINDOW_END, tz="UTC") + pd.Timedelta(hours=16),
        freq="8h",
    )
    rounded_times = times.dt.round("s") if not times.empty else pd.Series(dtype="datetime64[ns, UTC]")
    missing = sorted(set(expected) - set(rounded_times))
    missing_intervals = len(missing)
    if missing_intervals:
        errors.append("missing funding intervals")
    return {
        "quality_status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "coverage_start": times.min().isoformat() if not times.empty else None,
        "coverage_end": times.max().isoformat() if not times.empty else None,
        "expected_intervals": int(len(expected)),
        "missing_intervals": int(missing_intervals),
        "missing_interval_sample": [item.isoformat() for item in missing[:10]],
        "duplicate_funding_time": duplicate_count,
        "funding_rate_nulls": null_rates,
        "mark_price_nulls": int(frame.get("mark_price", pd.Series(dtype=float)).isna().sum()) if not frame.empty else 0,
        "available_ts_before_event_count": available_violation,
        "rows": int(len(frame)),
    }


def funding_months_v9_53(start_date: str, end_date: str) -> list[str]:
    start = date.fromisoformat(start_date).replace(day=1)
    end = date.fromisoformat(end_date).replace(day=1)
    months: list[str] = []
    cursor = start
    while cursor <= end:
        months.append(f"{cursor.year:04d}-{cursor.month:02d}")
        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year + 1, month=1)
        else:
            cursor = cursor.replace(month=cursor.month + 1)
    return months


def _can_use_rest_tail_fallback(source_errors: list[dict[str, Any]]) -> bool:
    if len(source_errors) != 1:
        return False
    item = source_errors[0]
    return item.get("month") == "2026-05" and "404" in str(item.get("error", ""))


def funding_silver_columns_v9_53() -> list[str]:
    return [
        "source",
        "venue",
        "market_type",
        "symbol",
        "metric_name",
        "funding_time",
        "event_ts",
        "available_ts",
        "funding_interval_hours",
        "funding_rate",
        "mark_price",
        "source_file",
        "row_valid",
        "invalid_reason",
    ]


def decide_v9_53(source_errors: list[dict[str, Any]], quality: dict[str, Any]) -> str:
    if source_errors:
        return "funding_collection_failed_source_issue"
    if quality.get("quality_status") != "PASS":
        return "funding_collection_partial"
    return "funding_collection_complete_oi_not_ready"


def build_manifest_v9_53(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": report["created_at_utc"],
        "decision": report["decision"],
        "reports": [REPORT_JSON_PATH.as_posix(), REPORT_MD_PATH.as_posix(), DOC_PATH.as_posix()],
        "manifest_path": MANIFEST_PATH.as_posix(),
        "funding_silver_path": SILVER_PATH.as_posix(),
        "raw_dir": RAW_DIR.as_posix(),
        "funding": report["funding"],
        "oi": report["oi"],
        "network_used": report["network_used"],
        "new_data_downloaded": report["new_data_downloaded"],
        "no_sidecars": True,
        "no_zip_fingerprints": True,
    }


def build_markdown_v9_53(report: dict[str, Any]) -> str:
    funding = report.get("funding", {})
    oi = report.get("oi", {})
    return (
        "# V9.53 - Funding / OI Collection\n\n"
        f"- Decision : `{report['decision']}`.\n"
        f"- Funding lignes : `{funding.get('rows')}`.\n"
        f"- Couverture funding : `{funding.get('coverage_start')}` -> `{funding.get('coverage_end')}`.\n"
        f"- Intervalles manquants : `{funding.get('missing_intervals')}`.\n"
        f"- OI collecte : `{oi.get('collected')}` (`{oi.get('reason')}`).\n"
        f"- Silver : `{funding.get('silver_path')}`.\n\n"
        "Collecte publique read-only uniquement depuis data.binance.vision. Aucun trading, ML, label, dataset supervise, backtest, walk-forward, strategie ou signal.\n"
    )


def _not_executed_report(readiness: dict[str, Any], reason: str, runtime_seconds: float) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": _utc_now(),
        "status": "FAIL",
        "direction": DIRECTION,
        "decision": "derivatives_collection_not_executed",
        "readiness_decision": readiness.get("decision"),
        "reason": reason,
        "funding_collected": False,
        "funding_usable": False,
        "funding": {},
        "oi": {"collected": False, "reason": "not_executed"},
        "runtime_seconds": round(runtime_seconds, 3),
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": False,
        "findings": dict(FINDINGS),
        "safety_flags": {**SAFETY_FLAGS, "network_used": False, "no_new_data_download": True},
    }


def _month_report(month: str, path: Path, url: str, status: str, error: str | None, downloaded: bool) -> dict[str, Any]:
    return {
        "month": month,
        "status": status,
        "path": path.as_posix(),
        "url": url,
        "downloaded": downloaded,
        "raw_bytes": path.stat().st_size if path.exists() else 0,
        "error": error,
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
