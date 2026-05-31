from __future__ import annotations

import io
import json
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd


VERSION = "V9.56"
SOURCE_VERSION = "V9.52_to_V9.55"
DIRECTION = "funding_tail_resolution_common_window_decision"
SYMBOL = "BTCUSDT"
VENUE = "binance"
SOURCE = "binance_archive"
MARKET_TYPE = "futures_um"
HOST = "data.binance.vision"
MONTHLY_BASE_URL = f"https://{HOST}/data/futures/um/monthly/fundingRate/{SYMBOL}"
DAILY_BASE_URL = f"https://{HOST}/data/futures/um/daily/fundingRate/{SYMBOL}"
REST_BASE_URL = "https://fapi.binance.com/fapi/v1/fundingRate"
TIMEOUT_SECONDS = 30

TARGET_WINDOW_START = "2021-05-05"
TARGET_WINDOW_END = "2026-05-05"
CLOSED_WINDOW_START_TS = "2021-05-05T00:00:00Z"
CLOSED_WINDOW_END_TS = "2026-04-30T16:00:00Z"
FULL_WINDOW_END_TS = "2026-05-05T16:00:00Z"

RAW_DIR = Path("data/raw/binance_public/futures_um/fundingRate/BTCUSDT")
REPORT_JSON_PATH = Path("reports/research_decisions/funding_tail_resolution_v9_56.json")
REPORT_MD_PATH = Path("reports/research_decisions/funding_tail_resolution_v9_56.md")
MANIFEST_PATH = Path("reports/manifests/funding_tail_resolution_v9_56_manifest.json")
DOC_PATH = Path("docs/funding_tail_resolution_v9_56.md")
CHAIN_REPORT_PATH = Path("reports/research_decisions/derivatives_readiness_feature_chain_v9_52_to_v9_55.json")
COLLECTION_REPORT_PATH = Path("reports/data/derivatives_funding_oi_collection_v9_53.json")
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
    "funding_tail_resolved_full_target_window",
    "funding_tail_unavailable_use_closed_common_window",
}


def run_funding_tail_resolution_v9_56(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    started = time.monotonic()
    chain_report = _read_json(root / CHAIN_REPORT_PATH)
    collection_report = _read_json(root / COLLECTION_REPORT_PATH)
    readiness_report = _read_json(root / READINESS_REPORT_PATH)

    local_before = load_local_funding_frame_v9_56(root)
    tail_checks = probe_tail_sources_v9_56(root)
    local_after = load_local_funding_frame_v9_56(root)

    full_quality = validate_funding_window_v9_56(
        local_after,
        start_ts=CLOSED_WINDOW_START_TS,
        end_ts=FULL_WINDOW_END_TS,
        expected_end_label=TARGET_WINDOW_END,
    )
    closed_quality = validate_funding_window_v9_56(
        local_after,
        start_ts=CLOSED_WINDOW_START_TS,
        end_ts=CLOSED_WINDOW_END_TS,
        expected_end_label="2026-04-30T16:00:00Z",
    )

    decision = decide_v9_56(full_quality, closed_quality, tail_checks)
    actual_window = actual_window_for_decision_v9_56(decision)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": _utc_now(),
        "status": "PASS" if decision in SUCCESS_DECISIONS else "FAIL",
        "direction": DIRECTION,
        "decision": decision,
        "source_chain_decision": chain_report.get("decision"),
        "source_collection_decision": collection_report.get("decision"),
        "source_readiness_decision": readiness_report.get("decision"),
        "funding_tail_status": funding_tail_status_v9_56(decision),
        "source_name": "Binance public archive fundingRate daily/monthly plus public market-data REST tail probe",
        "host": HOST,
        "monthly_tail_url": f"{MONTHLY_BASE_URL}/{SYMBOL}-fundingRate-2026-05.zip",
        "daily_tail_url_pattern": f"{DAILY_BASE_URL}/{SYMBOL}-fundingRate-YYYY-MM-DD.zip",
        "rest_tail_url": tail_checks["rest_tail"].get("url"),
        "local_funding_before_probe": summarize_frame_v9_56(local_before),
        "local_funding_after_probe": summarize_frame_v9_56(local_after),
        "full_target_window_quality": full_quality,
        "closed_common_window_quality": closed_quality,
        "tail_source_checks": tail_checks,
        "actual_feature_window": actual_window,
        "common_window_policy": common_window_policy_v9_56(decision),
        "common_window_sufficient_for_feature_store": decision in SUCCESS_DECISIONS,
        "funding_feature_store_authorized": decision in SUCCESS_DECISIONS,
        "oi_status": "oi_not_ready_history_limited_non_blocking",
        "blockers": build_blockers_v9_56(decision, full_quality, closed_quality, tail_checks),
        "warnings": build_warnings_v9_56(decision, tail_checks),
        "limitations": [
            "V9.56 ne cree aucun label, dataset supervise, ML, walk-forward, backtest, strategie ou signal.",
            "Les intervalles funding mai 2026 ne sont pas imputes et ne sont pas forward-fill pour pretendre une couverture complete.",
            "OI reste non exploitable sur historique long et non bloquant pour la couche funding-only.",
        ],
        "next_recommendation": "V9.57 - Funding-only feature store candidate" if decision in SUCCESS_DECISIONS else "V9.57 - Funding source follow-up",
        "runtime_seconds": round(time.monotonic() - started, 3),
        "network_used": True,
        "network_scope": "public_archive_or_public_market_data_read_only",
        "new_data_downloaded": tail_checks["new_data_downloaded"],
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
        },
    }
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_56(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_56(report))
    return report


def load_local_funding_frame_v9_56(root: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    raw_dir = root / RAW_DIR
    for path in sorted(raw_dir.glob("*.zip")) + sorted((raw_dir / "daily_tail").glob("*.zip")):
        frame = read_funding_zip_v9_56(path)
        if frame is not None and not frame.empty:
            frames.append(frame)
    rest_path = raw_dir / "rest_tail" / "BTCUSDT-fundingRate-2026-05-01_2026-05-05.json"
    if rest_path.exists():
        try:
            payload = json.loads(rest_path.read_text(encoding="utf-8"))
            if isinstance(payload, list) and payload:
                frame = pd.DataFrame(payload)
                frame["source_file"] = rest_path.as_posix()
                frames.append(frame)
        except Exception:
            pass
    if not frames:
        return pd.DataFrame(columns=funding_columns_v9_56())
    return normalize_funding_rows_v9_56(pd.concat(frames, ignore_index=True))


def read_funding_zip_v9_56(path: Path) -> pd.DataFrame | None:
    try:
        with zipfile.ZipFile(path) as archive:
            names = [name for name in archive.namelist() if not name.endswith("/")]
            if len(names) != 1:
                return None
            with archive.open(names[0]) as handle:
                frame = pd.read_csv(handle)
        frame["source_file"] = path.as_posix()
        return frame
    except Exception:
        return None


def normalize_funding_rows_v9_56(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=funding_columns_v9_56())
    source = frame.copy()
    time_column = "calc_time" if "calc_time" in source.columns else "fundingTime"
    rate_column = "last_funding_rate" if "last_funding_rate" in source.columns else "fundingRate"
    if time_column not in source.columns or rate_column not in source.columns:
        return pd.DataFrame(columns=funding_columns_v9_56())
    event_ts = pd.to_datetime(pd.to_numeric(source[time_column], errors="coerce"), unit="ms", utc=True)
    funding_rate = pd.to_numeric(source[rate_column], errors="coerce")
    interval = pd.to_numeric(source.get("funding_interval_hours", 8), errors="coerce").fillna(8)
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
            "funding_interval_hours": interval.astype("int64"),
            "funding_rate": funding_rate,
            "mark_price": mark_price,
            "source_file": source.get("source_file", ""),
        }
    )
    normalized["row_valid"] = normalized["funding_time"].notna() & normalized["funding_rate"].notna() & (normalized["funding_interval_hours"] > 0)
    normalized["invalid_reason"] = ""
    normalized.loc[normalized["funding_time"].isna(), "invalid_reason"] = "missing_funding_time"
    normalized.loc[normalized["funding_rate"].isna(), "invalid_reason"] = "missing_funding_rate"
    return normalized[funding_columns_v9_56()].sort_values("funding_time", kind="mergesort").reset_index(drop=True)


def validate_funding_window_v9_56(frame: pd.DataFrame, *, start_ts: str, end_ts: str, expected_end_label: str) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if list(frame.columns) != funding_columns_v9_56():
        errors.append("schema mismatch")
    start = pd.Timestamp(start_ts)
    end = pd.Timestamp(end_ts)
    window = frame.loc[(pd.to_datetime(frame["funding_time"], utc=True) >= start) & (pd.to_datetime(frame["funding_time"], utc=True) <= end)].copy() if not frame.empty else frame.copy()
    times = pd.to_datetime(window.get("funding_time", pd.Series(dtype="datetime64[ns, UTC]")), utc=True)
    rounded = times.dt.round("s") if not times.empty else pd.Series(dtype="datetime64[ns, UTC]")
    duplicate_count = int(rounded.duplicated().sum()) if not rounded.empty else 0
    invalid_rows = int((~window.get("row_valid", pd.Series(dtype=bool)).astype(bool)).sum()) if not window.empty else 0
    null_rates = int(window.get("funding_rate", pd.Series(dtype=float)).isna().sum()) if not window.empty else 0
    available_violation = int((pd.to_datetime(window.get("available_ts", []), utc=True) < times).sum()) if not window.empty else 0
    expected = pd.date_range(start, end, freq="8h")
    missing = sorted(set(expected) - set(rounded))
    unexpected = sorted(set(rounded) - set(expected)) if not rounded.empty else []
    if window.empty:
        errors.append("empty funding window")
    if duplicate_count:
        errors.append("duplicate funding_time")
    if invalid_rows:
        errors.append("invalid funding rows")
    if null_rates:
        errors.append("funding_rate nulls")
    if available_violation:
        errors.append("available_ts before funding_time")
    if missing:
        errors.append("missing funding intervals")
    if unexpected:
        warnings.append("funding timestamps outside expected 8h grid after rounding")
    return {
        "window_start": start_ts,
        "window_end": end_ts,
        "expected_end_label": expected_end_label,
        "quality_status": "PASS" if not errors else "FAIL",
        "coverage_start": times.min().isoformat() if not times.empty else None,
        "coverage_end": times.max().isoformat() if not times.empty else None,
        "rows": int(len(window)),
        "expected_intervals": int(len(expected)),
        "missing_intervals": int(len(missing)),
        "missing_interval_sample": [item.isoformat() for item in missing[:20]],
        "duplicate_funding_time": duplicate_count,
        "invalid_rows": invalid_rows,
        "funding_rate_nulls": null_rates,
        "available_ts_before_event_count": available_violation,
        "unexpected_interval_count": int(len(unexpected)),
        "unexpected_interval_sample": [item.isoformat() for item in unexpected[:10]],
        "errors": errors,
        "warnings": warnings,
    }


def probe_tail_sources_v9_56(root: Path) -> dict[str, Any]:
    raw_dir = root / RAW_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)
    monthly = fetch_zip_source_v9_56(
        f"{MONTHLY_BASE_URL}/{SYMBOL}-fundingRate-2026-05.zip",
        raw_dir / f"{SYMBOL}-fundingRate-2026-05.zip",
        "monthly_2026_05",
    )
    daily_reports: list[dict[str, Any]] = []
    for day in pd.date_range("2026-05-01", "2026-05-05", freq="D"):
        date_token = day.strftime("%Y-%m-%d")
        daily_reports.append(
            fetch_zip_source_v9_56(
                f"{DAILY_BASE_URL}/{SYMBOL}-fundingRate-{date_token}.zip",
                raw_dir / "daily_tail" / f"{SYMBOL}-fundingRate-{date_token}.zip",
                f"daily_{date_token}",
            )
        )
    rest = fetch_rest_tail_v9_56(raw_dir)
    return {
        "monthly_tail": monthly,
        "daily_tail": daily_reports,
        "daily_tail_complete": all(item["status"] == "available" for item in daily_reports),
        "rest_tail": rest,
        "new_data_downloaded": bool(monthly.get("downloaded") or rest.get("downloaded") or any(item.get("downloaded") for item in daily_reports)),
    }


def fetch_zip_source_v9_56(url: str, path: Path, source_id: str) -> dict[str, Any]:
    downloaded = False
    if path.exists() and path.stat().st_size > 0:
        return validate_zip_path_report_v9_56(source_id, path, url, downloaded)
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            payload = response.read()
        if not payload:
            return {"source_id": source_id, "url": url, "path": path.as_posix(), "status": "unavailable", "downloaded": downloaded, "error": "empty_download", "raw_bytes": 0}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        downloaded = True
        return validate_zip_path_report_v9_56(source_id, path, url, downloaded)
    except Exception as exc:  # pragma: no cover - integration/network path
        return {"source_id": source_id, "url": url, "path": path.as_posix(), "status": "unavailable", "downloaded": downloaded, "error": f"{type(exc).__name__}: {exc}", "raw_bytes": path.stat().st_size if path.exists() else 0}


def validate_zip_path_report_v9_56(source_id: str, path: Path, url: str, downloaded: bool) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(path) as archive:
            names = [name for name in archive.namelist() if not name.endswith("/")]
        if len(names) != 1:
            return {"source_id": source_id, "url": url, "path": path.as_posix(), "status": "invalid", "downloaded": downloaded, "error": f"expected_one_csv_found_{len(names)}", "raw_bytes": path.stat().st_size}
        return {"source_id": source_id, "url": url, "path": path.as_posix(), "status": "available", "downloaded": downloaded, "error": None, "raw_bytes": path.stat().st_size}
    except Exception as exc:
        return {"source_id": source_id, "url": url, "path": path.as_posix(), "status": "invalid", "downloaded": downloaded, "error": f"{type(exc).__name__}: {exc}", "raw_bytes": path.stat().st_size if path.exists() else 0}


def fetch_rest_tail_v9_56(raw_dir: Path) -> dict[str, Any]:
    rest_dir = raw_dir / "rest_tail"
    path = rest_dir / "BTCUSDT-fundingRate-2026-05-01_2026-05-05.json"
    params = {
        "symbol": SYMBOL,
        "startTime": int(pd.Timestamp("2026-05-01T00:00:00Z").timestamp() * 1000),
        "endTime": int(pd.Timestamp("2026-05-05T16:00:00Z").timestamp() * 1000),
        "limit": 1000,
    }
    url = f"{REST_BASE_URL}?{urllib.parse.urlencode(params)}"
    downloaded = False
    if path.exists() and path.stat().st_size > 0:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return {"source_id": "rest_tail_2026_05_01_2026_05_05", "url": url, "path": path.as_posix(), "status": "available" if isinstance(payload, list) and payload else "unavailable", "downloaded": downloaded, "error": None if isinstance(payload, list) and payload else "empty_or_invalid_rest_payload", "raw_bytes": path.stat().st_size, "rows": len(payload) if isinstance(payload, list) else 0}
        except Exception as exc:
            return {"source_id": "rest_tail_2026_05_01_2026_05_05", "url": url, "path": path.as_posix(), "status": "invalid", "downloaded": downloaded, "error": f"{type(exc).__name__}: {exc}", "raw_bytes": path.stat().st_size, "rows": 0}
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
        rest_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        downloaded = True
        return {"source_id": "rest_tail_2026_05_01_2026_05_05", "url": url, "path": path.as_posix(), "status": "available" if isinstance(payload, list) and payload else "unavailable", "downloaded": downloaded, "error": None if isinstance(payload, list) and payload else "empty_or_invalid_rest_payload", "raw_bytes": path.stat().st_size, "rows": len(payload) if isinstance(payload, list) else 0}
    except Exception as exc:  # pragma: no cover - integration/network path
        return {"source_id": "rest_tail_2026_05_01_2026_05_05", "url": url, "path": path.as_posix(), "status": "unavailable", "downloaded": downloaded, "error": f"{type(exc).__name__}: {exc}", "raw_bytes": path.stat().st_size if path.exists() else 0, "rows": 0}


def decide_v9_56(full_quality: dict[str, Any], closed_quality: dict[str, Any], tail_checks: dict[str, Any]) -> str:
    if full_quality.get("quality_status") == "PASS":
        return "funding_tail_resolved_full_target_window"
    if closed_quality.get("quality_status") == "PASS":
        return "funding_tail_unavailable_use_closed_common_window"
    if tail_checks.get("monthly_tail", {}).get("status") == "unavailable" or tail_checks.get("rest_tail", {}).get("status") == "unavailable":
        return "funding_tail_unavailable_source_issue"
    return "funding_common_window_not_sufficient"


def actual_window_for_decision_v9_56(decision: str) -> dict[str, str | None]:
    if decision == "funding_tail_resolved_full_target_window":
        return {"start": CLOSED_WINDOW_START_TS, "end": FULL_WINDOW_END_TS, "label": "2021-05-05_to_2026-05-05"}
    if decision == "funding_tail_unavailable_use_closed_common_window":
        return {"start": CLOSED_WINDOW_START_TS, "end": CLOSED_WINDOW_END_TS, "label": "2021-05-05_to_2026-04-30T16-00-00Z"}
    return {"start": None, "end": None, "label": None}


def funding_tail_status_v9_56(decision: str) -> str:
    if decision == "funding_tail_resolved_full_target_window":
        return "resolved_full_target_window"
    if decision == "funding_tail_unavailable_use_closed_common_window":
        return "tail_unavailable_closed_common_window_selected"
    return "tail_unavailable_no_usable_common_window"


def common_window_policy_v9_56(decision: str) -> str:
    if decision == "funding_tail_resolved_full_target_window":
        return "full_target_window_public_tail_available_no_imputation"
    if decision == "funding_tail_unavailable_use_closed_common_window":
        return "closed_exact_at_last_known_funding_timestamp_no_imputation_no_tail_forward_fill"
    return "no_common_window_authorized"


def summarize_frame_v9_56(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {"rows": 0, "coverage_start": None, "coverage_end": None, "duplicate_funding_time": 0, "raw_files_count": 0}
    times = pd.to_datetime(frame["funding_time"], utc=True)
    return {
        "rows": int(len(frame)),
        "coverage_start": times.min().isoformat(),
        "coverage_end": times.max().isoformat(),
        "duplicate_funding_time": int(times.dt.round("s").duplicated().sum()),
        "raw_files_count": int(frame["source_file"].nunique()),
    }


def build_blockers_v9_56(decision: str, full_quality: dict[str, Any], closed_quality: dict[str, Any], tail_checks: dict[str, Any]) -> list[Any]:
    if decision in SUCCESS_DECISIONS:
        return []
    return [
        {"full_target_errors": full_quality.get("errors", [])},
        {"closed_window_errors": closed_quality.get("errors", [])},
        {"tail_source_checks": tail_checks},
    ]


def build_warnings_v9_56(decision: str, tail_checks: dict[str, Any]) -> list[str]:
    warnings: list[str] = ["OI reste non inclus : historique public long non pret."]
    if decision == "funding_tail_unavailable_use_closed_common_window":
        warnings.append("La queue funding 2026-05 reste indisponible; la fenetre commune est fermee au dernier funding connu.")
    for item in [tail_checks.get("monthly_tail", {}), tail_checks.get("rest_tail", {})]:
        if item.get("error"):
            warnings.append(f"{item.get('source_id')}: {item.get('error')}")
    unavailable_daily = [item["source_id"] for item in tail_checks.get("daily_tail", []) if item.get("status") != "available"]
    if unavailable_daily:
        warnings.append(f"Daily funding tail non disponible ou non confirme: {unavailable_daily[:5]}")
    return warnings


def funding_columns_v9_56() -> list[str]:
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


def build_manifest_v9_56(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": report["created_at_utc"],
        "decision": report["decision"],
        "reports": [REPORT_JSON_PATH.as_posix(), REPORT_MD_PATH.as_posix(), DOC_PATH.as_posix()],
        "manifest_path": MANIFEST_PATH.as_posix(),
        "raw_dir": RAW_DIR.as_posix(),
        "actual_feature_window": report["actual_feature_window"],
        "network_used": report["network_used"],
        "new_data_downloaded": report["new_data_downloaded"],
        "no_sidecars": True,
        "no_zip_fingerprints": True,
    }


def build_markdown_v9_56(report: dict[str, Any]) -> str:
    actual = report.get("actual_feature_window", {})
    full_quality = report.get("full_target_window_quality", {})
    closed_quality = report.get("closed_common_window_quality", {})
    return (
        "# V9.56 - Resolution queue funding et fenetre commune\n\n"
        f"- Decision : `{report['decision']}`.\n"
        f"- Statut queue funding : `{report['funding_tail_status']}`.\n"
        f"- Fenetre retenue : `{actual.get('start')}` -> `{actual.get('end')}`.\n"
        f"- Qualite cible complete : `{full_quality.get('quality_status')}` avec `{full_quality.get('missing_intervals')}` intervalles manquants.\n"
        f"- Qualite fenetre fermee : `{closed_quality.get('quality_status')}` avec `{closed_quality.get('missing_intervals')}` intervalles manquants.\n"
        f"- Feature store funding autorise : `{report['funding_feature_store_authorized']}`.\n"
        f"- OI : `{report['oi_status']}`.\n\n"
        "Aucune imputation des intervalles funding manquants. Aucun trading, paper live, ordre, ML, dataset supervise, label, backtest, walk-forward, strategie ou signal.\n"
    )


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
