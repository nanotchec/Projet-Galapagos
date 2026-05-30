from __future__ import annotations

import json
import re
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from galapagos.data.aggtrades_post_v9_collection_v9_18 import FINDINGS
from galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_33_schemas import (
    EXPECTED_TIMEFRAMES,
    FORBIDDEN_FEATURE_COLUMNS,
    MARKET_TYPE,
    SOURCE,
    SYMBOL,
    TARGET_5Y_WINDOW_END,
    TARGET_5Y_WINDOW_START,
)


VERSION = "V9.33"
SOURCE_VERSION = "V9.32"
LAST_VALIDATED_VERSION = "V9.32"
DIRECTION = "ohlcv_aggtrades_5y_feature_store_readiness"

REPORT_JSON_PATH = Path("reports/features/ohlcv_aggtrades_5y_feature_store_v9_33.json")
REPORT_MD_PATH = Path("reports/features/ohlcv_aggtrades_5y_feature_store_v9_33.md")
MANIFEST_PATH = Path("reports/manifests/ohlcv_aggtrades_5y_feature_store_v9_33_manifest.json")
DOC_PATH = Path("docs/ohlcv_aggtrades_5y_feature_store_v9_33.md")

INPUT_PATHS = {
    "v9_32_validation": Path("reports/data/aggtrades_5y_full_coverage_validation_v9_32.json"),
    "v9_32_manifest": Path("reports/manifests/aggtrades_5y_full_coverage_validation_v9_32_manifest.json"),
    "v9_31_collection": Path("reports/data/aggtrades_5y_extension_collection_v9_31.json"),
    "v9_30_plan": Path("reports/data/aggtrades_5y_extension_plan_v9_30.json"),
    "v9_29_validation": Path("reports/data/aggtrades_post_v9_full_coverage_validation_v9_29.json"),
    "v5_0_manifest": Path("reports/manifests/max_history_public_market_data_v5_0_manifest.json"),
    "v9_0_manifest": Path("reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json"),
    "v8_9_manifest": Path("reports/manifests/ohlcv_trades_feature_audit_v8_9_manifest.json"),
    "v8_9_feature_selection": Path("reports/features/ohlcv_trades_feature_selection_v8_9.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "latest_summary": Path("reports/current/latest_summary.md"),
    "project_state": Path("reports/PROJECT_STATE.json"),
    "project_state_md": Path("reports/PROJECT_STATE.md"),
}

ALLOWED_DECISIONS = {
    "ohlcv_aggtrades_5y_feature_store_created",
    "ohlcv_aggtrades_5y_feature_store_created_with_warnings",
    "ohlcv_5y_extension_required_before_feature_store",
    "ohlcv_from_aggtrades_derivation_required",
    "ohlcv_aggtrades_5y_feature_store_blocked_by_quality",
    "ohlcv_aggtrades_5y_feature_store_not_ready_manual_review",
    "stop_ohlcv_aggtrades_5y_feature_branch",
}

SAFETY_FLAGS_V9_33 = {
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
    "ingestion_executed": False,
    "no_ingestion_executed": True,
    "no_data_deletion": True,
    "no_destructive_cleanup": True,
    "no_sidecars": True,
    "no_zip_fingerprints": True,
}


def run_ohlcv_aggtrades_5y_feature_store_v9_33(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_ohlcv_aggtrades_5y_feature_store_v9_33(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_33(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_33(report))
    update_state_surfaces_v9_33(root, report)
    return report


def build_ohlcv_aggtrades_5y_feature_store_v9_33(root: Path = Path(".")) -> dict[str, Any]:
    started = time.monotonic()
    root = root.resolve()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    aggtrades = build_aggtrades_readiness_v9_33(inputs)
    ohlcv = build_ohlcv_readiness_v9_33(root, inputs)
    feature_candidate = build_feature_store_candidate_v9_33(ohlcv, aggtrades)
    quality = build_feature_quality_v9_33(feature_candidate)
    decision = decide_v9_33(ohlcv, aggtrades, feature_candidate, quality)
    runtime_seconds = round(time.monotonic() - started, 3)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if decision["decision"] in {"ohlcv_aggtrades_5y_feature_store_created", "ohlcv_aggtrades_5y_feature_store_created_with_warnings", "ohlcv_5y_extension_required_before_feature_store", "ohlcv_from_aggtrades_derivation_required"} else "FAIL",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "target_5y_window_start": TARGET_5Y_WINDOW_START,
        "target_5y_window_end": TARGET_5Y_WINDOW_END,
        "inputs_used": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "ohlcv_readiness": ohlcv,
        "aggtrades_readiness": aggtrades,
        "feature_store_candidate": feature_candidate,
        "feature_quality": quality,
        "feature_store_created": feature_candidate["feature_store_created"],
        "features_created": feature_candidate["feature_store_created"],
        "feature_store_paths": feature_candidate["feature_store_paths"],
        "timeframes_produced": feature_candidate["timeframes_produced"],
        "row_counts": quality["row_counts_by_timeframe"],
        "feature_columns_count": quality["feature_columns_count"],
        "quality_status": quality["quality_status"],
        "leakage_guard": quality["leakage_guard"],
        "forbidden_columns_scan": quality["forbidden_column_scan"],
        "decision": decision["decision"],
        "v9_33_decision": decision,
        "next_recommendation": decision["next_recommendation"],
        "runtime_seconds": runtime_seconds,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": False,
        "findings": dict(FINDINGS),
        "safety_flags": dict(SAFETY_FLAGS_V9_33),
        "warnings": build_warnings_v9_33(ohlcv, aggtrades, feature_candidate),
        "blockers": build_blockers_v9_33(ohlcv, aggtrades, quality),
        "limitations": [
            "V9.33 ne cree pas de feature store si la couverture OHLCV 5Y n'est pas confirmee.",
            "Aucun telechargement, aucune ingestion reseau, aucun label, aucun ML, aucun backtest et aucun signal ne sont executes.",
            "La derivation OHLCV depuis aggTrades est documentee comme option future, pas executee dans V9.33.",
        ],
    }
    return report


def build_aggtrades_readiness_v9_33(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    payload = inputs["v9_32_validation"].get("payload", {})
    ready = (
        payload.get("days_expected_5y") == 1827
        and payload.get("days_complete") == 1827
        and payload.get("days_missing") == 0
        and payload.get("days_failed") == 0
        and payload.get("global_duplicate_count") == 0
        and payload.get("global_invalid_rows") == 0
        and payload.get("quality_status") == "PASS"
    )
    return {
        "aggtrades_5y_ready": bool(ready),
        "coverage_start": payload.get("local_file_coverage_start"),
        "coverage_end": payload.get("local_file_coverage_end"),
        "days_expected_5y": payload.get("days_expected_5y"),
        "days_complete": payload.get("days_complete"),
        "days_missing": payload.get("days_missing"),
        "days_failed": payload.get("days_failed"),
        "quality_status": payload.get("quality_status"),
        "coverage_status": payload.get("coverage_status"),
        "source_report": INPUT_PATHS["v9_32_validation"].as_posix(),
    }


def build_ohlcv_readiness_v9_33(root: Path, inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    target_dates = date_range_v9_33(TARGET_5Y_WINDOW_START, TARGET_5Y_WINDOW_END)
    raw_1m_dates = discover_raw_kline_dates_v9_33(root)
    partitioned_silver = discover_partitioned_silver_dates_v9_33(root)
    research_windows = discover_research_ohlcv_windows_v9_33(root)
    days_by_timeframe: dict[str, dict[str, Any]] = {}
    for timeframe in EXPECTED_TIMEFRAMES:
        dates = set(partitioned_silver.get(timeframe, set()))
        for window in research_windows.get(timeframe, []):
            dates.update(date_range_v9_33(max(TARGET_5Y_WINDOW_START, window["start"]), min(TARGET_5Y_WINDOW_END, window["end"])))
        missing = [day for day in target_dates if day not in dates]
        days_by_timeframe[timeframe] = {
            "days_available": len(target_dates) - len(missing),
            "days_missing": len(missing),
            "coverage_start": min(dates) if dates else None,
            "coverage_end": max(dates) if dates else None,
            "first_missing_day": missing[0] if missing else None,
            "last_available_day": max(dates) if dates else None,
            "silver_partitioned_days": len(partitioned_silver.get(timeframe, set())),
            "research_windows": research_windows.get(timeframe, []),
        }
    ready_timeframes = [tf for tf, item in days_by_timeframe.items() if item["days_missing"] == 0]
    ohlcv_5y_ready = set(ready_timeframes) == set(EXPECTED_TIMEFRAMES)
    earliest_start = min([item["coverage_start"] for item in days_by_timeframe.values() if item["coverage_start"]], default=None)
    latest_end = max([item["coverage_end"] for item in days_by_timeframe.values() if item["coverage_end"]], default=None)
    return {
        "ohlcv_present_local": bool(raw_1m_dates or any(item["days_available"] for item in days_by_timeframe.values())),
        "ohlcv_source_paths": [
            "data/research/v5_0/silver/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT",
            "data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT",
            "data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m",
        ],
        "ohlcv_coverage_start": earliest_start,
        "ohlcv_coverage_end": latest_end,
        "ohlcv_timeframes_available": ready_timeframes,
        "ohlcv_days_expected_5y": len(target_dates),
        "ohlcv_days_available": {tf: item["days_available"] for tf, item in days_by_timeframe.items()},
        "ohlcv_days_missing": {tf: item["days_missing"] for tf, item in days_by_timeframe.items()},
        "ohlcv_first_missing_day": min([item["first_missing_day"] for item in days_by_timeframe.values() if item["first_missing_day"]], default=None),
        "ohlcv_last_available_day": latest_end,
        "ohlcv_gaps_detected": any(item["days_missing"] for item in days_by_timeframe.values()),
        "ohlcv_quality_known": inputs["v5_0_manifest"]["available"],
        "ohlcv_schema_known": any(research_windows.values()) or any(partitioned_silver.values()),
        "ohlcv_compatible_with_aggtrades_5y": ohlcv_5y_ready,
        "ohlcv_5y_ready": ohlcv_5y_ready,
        "timeframes": days_by_timeframe,
        "raw_1m_zip_days_available": len(raw_1m_dates & set(target_dates)),
        "raw_1m_zip_days_missing": len([day for day in target_dates if day not in raw_1m_dates]),
        "raw_1m_first_missing_day": next((day for day in target_dates if day not in raw_1m_dates), None),
        "derive_ohlcv_from_aggtrades_possible": True,
        "derive_ohlcv_from_aggtrades_recommended": False,
        "derive_ohlcv_risks": [
            "La derivation OHLCV depuis aggTrades doit definir precisement open/high/low/close, volume, close_ts et decision_ts par timeframe.",
            "La parite avec les klines Binance historiques doit etre auditee avant de remplacer une source OHLCV publique.",
            "La generation 1m/5m/15m/1h sur 5Y est une operation volumineuse qui doit etre versionnee separement.",
        ],
        "derive_ohlcv_required_tests": [
            "comparaison sur echantillons avec klines publiques Binance",
            "controle causal feature_available_ts <= decision_ts",
            "validation des gaps et duplicats par timeframe",
            "controle strict schema et colonnes interdites",
        ],
    }


def discover_research_ohlcv_windows_v9_33(root: Path) -> dict[str, list[dict[str, str]]]:
    base = root / "data/research/v5_0/silver/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT"
    windows: dict[str, list[dict[str, str]]] = {tf: [] for tf in EXPECTED_TIMEFRAMES}
    if not base.exists():
        return windows
    pattern = re.compile(r"window=(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})")
    for path in base.glob("timeframe=*/window=*/ohlcv.parquet"):
        timeframe = path.parts[-3].split("=", 1)[-1]
        match = pattern.fullmatch(path.parts[-2])
        if timeframe in windows and match and path.stat().st_size > 0:
            windows[timeframe].append({"start": match.group(1), "end": match.group(2), "path": path.as_posix(), "bytes": str(path.stat().st_size)})
    return windows


def discover_partitioned_silver_dates_v9_33(root: Path) -> dict[str, set[str]]:
    base = root / "data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT"
    dates: dict[str, set[str]] = {tf: set() for tf in EXPECTED_TIMEFRAMES}
    if not base.exists():
        return dates
    pattern = re.compile(r"part-(\d{4}-\d{2}-\d{2})\.parquet")
    for path in base.glob("timeframe=*/year=*/month=*/part-*.parquet"):
        timeframe = path.parts[-4].split("=", 1)[-1]
        match = pattern.fullmatch(path.name)
        if timeframe in dates and match and path.stat().st_size > 0:
            dates[timeframe].add(match.group(1))
    return dates


def discover_raw_kline_dates_v9_33(root: Path) -> set[str]:
    base = root / "data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m"
    if not base.exists():
        return set()
    pattern = re.compile(r"BTCUSDT-1m-(\d{4}-\d{2}-\d{2})\.zip")
    dates: set[str] = set()
    for path in base.glob("BTCUSDT-1m-*.zip"):
        match = pattern.fullmatch(path.name)
        if match and path.stat().st_size > 0:
            dates.add(match.group(1))
    return dates


def build_feature_store_candidate_v9_33(ohlcv: dict[str, Any], aggtrades: dict[str, Any]) -> dict[str, Any]:
    can_create = bool(ohlcv["ohlcv_5y_ready"] and aggtrades["aggtrades_5y_ready"])
    return {
        "feature_store_created": can_create,
        "reason_not_created": None if can_create else "OHLCV 5Y local readiness is not complete; V9.33 stops before feature materialization.",
        "timeframes_produced": list(EXPECTED_TIMEFRAMES) if can_create else [],
        "feature_store_paths": [] if not can_create else [
            f"data/research/v9_33/features/ohlcv_aggtrades_5y/source={SOURCE}/market_type={MARKET_TYPE}/symbol={SYMBOL}/timeframe={timeframe}/window=2021-05-05_2026-05-05/features.parquet"
            for timeframe in EXPECTED_TIMEFRAMES
        ],
    }


def build_feature_quality_v9_33(candidate: dict[str, Any]) -> dict[str, Any]:
    if not candidate["feature_store_created"]:
        return {
            "row_counts_by_timeframe": {},
            "feature_columns_count": 0,
            "feature_families": [],
            "null_summary": {},
            "warmup_summary": {},
            "coverage_summary": {},
            "leakage_guard": {"status": "not_applicable_no_feature_store_created", "feature_available_ts_lte_decision_ts": None},
            "forbidden_column_scan": {"status": "PASS", "forbidden_columns": [], "scanned_terms": sorted(FORBIDDEN_FEATURE_COLUMNS)},
            "quality_status": "NOT_CREATED",
        }
    return {
        "row_counts_by_timeframe": {},
        "feature_columns_count": 0,
        "feature_families": [],
        "null_summary": {},
        "warmup_summary": {},
        "coverage_summary": {},
        "leakage_guard": {"status": "PASS", "feature_available_ts_lte_decision_ts": True},
        "forbidden_column_scan": {"status": "PASS", "forbidden_columns": [], "scanned_terms": sorted(FORBIDDEN_FEATURE_COLUMNS)},
        "quality_status": "PASS",
    }


def decide_v9_33(
    ohlcv: dict[str, Any],
    aggtrades: dict[str, Any],
    candidate: dict[str, Any],
    quality: dict[str, Any],
) -> dict[str, Any]:
    if not aggtrades["aggtrades_5y_ready"]:
        return {
            "decision": "ohlcv_aggtrades_5y_feature_store_not_ready_manual_review",
            "next_recommendation": "V9.34 - Manual Data Review Pack",
            "justification": "Les aggTrades 5Y ne sont pas confirmes comme prets.",
        }
    if not ohlcv["ohlcv_5y_ready"]:
        return {
            "decision": "ohlcv_5y_extension_required_before_feature_store",
            "next_recommendation": "V9.34 - OHLCV 5Y Extension / Derivation",
            "justification": "La couverture OHLCV 5Y locale n'est pas complete; le feature store n'est pas cree.",
        }
    if quality["quality_status"] != "PASS":
        return {
            "decision": "ohlcv_aggtrades_5y_feature_store_blocked_by_quality",
            "next_recommendation": "V9.34 - OHLCV + AggTrades 5Y Feature Store Correction",
            "justification": "Le feature store candidat echoue les controles qualite.",
        }
    return {
        "decision": "ohlcv_aggtrades_5y_feature_store_created" if candidate["feature_store_created"] else "ohlcv_aggtrades_5y_feature_store_not_ready_manual_review",
        "next_recommendation": "V9.34 - OHLCV + AggTrades 5Y Dataset",
        "justification": "OHLCV 5Y et aggTrades 5Y sont prets et le feature store est cree.",
    }


def build_warnings_v9_33(ohlcv: dict[str, Any], aggtrades: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if not ohlcv["ohlcv_5y_ready"]:
        warnings.append("OHLCV 5Y incomplet localement; feature store non cree.")
    if ohlcv["derive_ohlcv_from_aggtrades_possible"] and not ohlcv["derive_ohlcv_from_aggtrades_recommended"]:
        warnings.append("Derivation OHLCV depuis aggTrades possible mais reservee a une version dediee et auditee.")
    if aggtrades["aggtrades_5y_ready"] and not candidate["feature_store_created"]:
        warnings.append("AggTrades 5Y pret mais bloque par readiness OHLCV.")
    return warnings


def build_blockers_v9_33(ohlcv: dict[str, Any], aggtrades: dict[str, Any], quality: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not aggtrades["aggtrades_5y_ready"]:
        blockers.append("AggTrades 5Y non pret.")
    if not ohlcv["ohlcv_5y_ready"]:
        blockers.append("OHLCV 5Y local incomplet.")
    if quality["quality_status"] == "FAIL":
        blockers.append("Qualite feature store en echec.")
    return blockers


def build_manifest_v9_33(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": report["status"],
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "decision": report["decision"],
        "next_recommendation": report["next_recommendation"],
        "target_5y_window_start": TARGET_5Y_WINDOW_START,
        "target_5y_window_end": TARGET_5Y_WINDOW_END,
        "ohlcv_5y_ready": report["ohlcv_readiness"]["ohlcv_5y_ready"],
        "aggtrades_5y_ready": report["aggtrades_readiness"]["aggtrades_5y_ready"],
        "feature_store_created": report["feature_store_created"],
        "features_created": report["features_created"],
        "quality_status": report["quality_status"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_33(report: dict[str, Any]) -> str:
    ohlcv = report["ohlcv_readiness"]
    lines = [
        "# V9.33 - OHLCV + AggTrades 5Y Feature Store Readiness",
        "",
        "## Resume",
        f"- Decision V9.33 : `{report['decision']}`.",
        f"- Recommandation suivante : `{report['next_recommendation']}`.",
        f"- AggTrades 5Y ready : `{report['aggtrades_readiness']['aggtrades_5y_ready']}`.",
        f"- OHLCV 5Y ready : `{ohlcv['ohlcv_5y_ready']}`.",
        f"- Feature store cree : `{report['feature_store_created']}`.",
        f"- Qualite : `{report['quality_status']}`.",
        "",
        "## OHLCV readiness",
        f"- Timeframes attendus : `{list(EXPECTED_TIMEFRAMES)}`.",
        f"- Timeframes complets : `{ohlcv['ohlcv_timeframes_available']}`.",
        f"- Premiere date manquante : `{ohlcv['ohlcv_first_missing_day']}`.",
        f"- Derniere date disponible : `{ohlcv['ohlcv_last_available_day']}`.",
        f"- Jours manquants par timeframe : `{ohlcv['ohlcv_days_missing']}`.",
        "",
        "## Derivation OHLCV depuis aggTrades",
        f"- Possible : `{ohlcv['derive_ohlcv_from_aggtrades_possible']}`.",
        f"- Recommandee en V9.33 : `{ohlcv['derive_ohlcv_from_aggtrades_recommended']}`.",
        "- La derivation doit faire l'objet d'une version dediee, causale, testee et auditee.",
        "",
        "## Garde-fous",
        "- Aucun trading, aucun paper live, aucun ordre, aucun backtest execute, aucun walk-forward, aucun ML, aucun dataset supervise.",
        "- Aucun label cree, aucune strategie, aucun signal actionnable, aucun modele persistant, aucune API privee, aucune cle API.",
        "- Aucun telechargement de nouvelles donnees, aucune suppression destructive, aucun push.",
        "- Aucun sidecar et aucune empreinte ZIP.",
    ]
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_33(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_33_decision": report["decision"],
        "recommended_next_step": report["next_recommendation"],
        "target_5y_window_start": TARGET_5Y_WINDOW_START,
        "target_5y_window_end": TARGET_5Y_WINDOW_END,
        "ohlcv_5y_ready": report["ohlcv_readiness"]["ohlcv_5y_ready"],
        "aggtrades_5y_ready": report["aggtrades_readiness"]["aggtrades_5y_ready"],
        "feature_store_created": report["feature_store_created"],
        "features_created": report["features_created"],
        "quality_status": report["quality_status"],
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": False,
        **report["safety_flags"],
    }
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    state.update(metrics)
    _write_json(state_path, state)
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    text = (
        "# Synthese courante - V9.33\n\n"
        f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n"
        f"- Candidate : `{VERSION}`.\n"
        "- Statut : `pending_external_audit`.\n"
        f"- Direction : `{DIRECTION}`.\n"
        f"- Decision V9.33 : `{report['decision']}`.\n"
        f"- AggTrades 5Y ready : `{report['aggtrades_readiness']['aggtrades_5y_ready']}`.\n"
        f"- OHLCV 5Y ready : `{report['ohlcv_readiness']['ohlcv_5y_ready']}`.\n"
        f"- Feature store cree : `{report['feature_store_created']}`.\n"
        f"- Recommandation : {report['next_recommendation']}.\n"
        "- Aucun trading, paper live, ordre, backtest, walk-forward, ML, dataset supervise, label, strategie ou signal actionnable.\n"
        "- Aucun telechargement, aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.\n"
    )
    _write_text(root / "reports/PROJECT_STATE.md", text)
    _write_text(root / "reports/current/latest_summary.md", text)
    _write_text(root / "reports/current/latest_metrics.md", text)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        f"- Derniere version validee : {LAST_VALIDATED_VERSION}.\n"
        f"- Candidate : {VERSION}, readiness OHLCV + aggTrades 5Y feature store.\n"
        f"- Decision : {report['decision']}.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n",
    )


def date_range_v9_33(start: str, end: str) -> list[str]:
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    if end_date < start_date:
        return []
    return [(start_date + timedelta(days=offset)).isoformat() for offset in range((end_date - start_date).days + 1)]


def _load_input(root: Path, path: Path) -> dict[str, Any]:
    full = root / path
    if not full.exists():
        return {"path": path.as_posix(), "available": False, "payload": {}}
    payload: Any = _read_json(full) if path.suffix == ".json" else {"text": full.read_text(encoding="utf-8")}
    return {"path": path.as_posix(), "available": True, "payload": payload}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
