from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


VERSION = "V9.52"
SOURCE_VERSION = "V9.48_to_V9.51"
DIRECTION = "derivatives_source_readiness"
SYMBOL = "BTCUSDT"
TARGET_WINDOW_START = "2021-05-05"
TARGET_WINDOW_END = "2026-05-05"
MINIMUM_WINDOW_START = "2024-05-05"
MINIMUM_WINDOW_END = "2026-05-05"
HOST = "data.binance.vision"

REPORT_JSON_PATH = Path("reports/research_decisions/derivatives_source_readiness_v9_52.json")
REPORT_MD_PATH = Path("reports/research_decisions/derivatives_source_readiness_v9_52.md")
MANIFEST_PATH = Path("reports/manifests/derivatives_source_readiness_v9_52_manifest.json")
DOC_PATH = Path("docs/derivatives_source_readiness_v9_52.md")

INPUT_PATHS = {
    "derivatives_coverage_v1_14": Path("reports/research/derivatives_coverage_v1_14.json"),
    "derivatives_data_quality_v1_14": Path("reports/research/derivatives_data_quality_v1_14.json"),
    "derivatives_features_v1_14": Path("reports/research/derivatives_features_v1_14.json"),
    "derivatives_data_extension_readiness_v9_15": Path("reports/research_decisions/derivatives_data_extension_readiness_v9_15.json"),
    "derivatives_window_extension_v9_16": Path("reports/research_decisions/derivatives_window_extension_v9_16.json"),
    "derivatives_history_collection_plan_v9_17": Path("reports/research_decisions/derivatives_history_collection_plan_v9_17.json"),
    "feature_label_separability_v9_14_1": Path("reports/research_decisions/feature_label_separability_v9_14_1.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "latest_summary": Path("reports/current/latest_summary.md"),
    "project_state": Path("reports/PROJECT_STATE.json"),
    "project_state_md": Path("reports/PROJECT_STATE.md"),
}

LOCAL_METADATA_PATHS = {
    "raw": Path("data/raw"),
    "silver": Path("data/silver"),
    "gold": Path("data/gold"),
    "research": Path("data/research"),
    "raw_binance_public": Path("data/raw/binance_public"),
    "silver_derivatives": Path("data/silver/derivatives"),
    "gold_derivatives_features": Path("data/gold/derivatives_features"),
    "reports_manifests": Path("reports/manifests"),
    "scripts": Path("scripts"),
    "data_code": Path("src/galapagos/data"),
    "features_code": Path("src/galapagos/features"),
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

ALLOWED_DECISIONS = {
    "derivatives_source_readiness_funding_ready",
    "derivatives_source_readiness_funding_ready_oi_limited",
    "derivatives_source_readiness_not_ready_source_uncertainty",
    "derivatives_source_readiness_not_ready_no_public_source",
    "derivatives_source_readiness_manual_review_required",
}


def run_derivatives_source_readiness_v9_52(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_derivatives_source_readiness_report_v9_52(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_52(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_52(report))
    return report


def build_derivatives_source_readiness_report_v9_52(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    inputs = {name: _load_input(root / path) for name, path in INPUT_PATHS.items()}
    local_inventory = inspect_local_metadata_v9_52(root)
    source_assessments = build_source_assessments_v9_52(root, inputs, local_inventory)
    funding = source_assessments["funding_rate"]
    open_interest = source_assessments["open_interest"]
    decision = decide_source_readiness_v9_52(funding, open_interest)
    status = "PASS" if decision in {
        "derivatives_source_readiness_funding_ready",
        "derivatives_source_readiness_funding_ready_oi_limited",
    } else "FAIL"
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": _utc_now(),
        "status": status,
        "direction": DIRECTION,
        "target_window": {"start": TARGET_WINDOW_START, "end": TARGET_WINDOW_END},
        "minimum_acceptable_window": {"start": MINIMUM_WINDOW_START, "end": MINIMUM_WINDOW_END},
        "symbol": SYMBOL,
        "inputs_used": {name: {"path": path.as_posix(), "available": item["available"]} for name, (path, item) in zip(INPUT_PATHS, [(p, inputs[n]) for n, p in INPUT_PATHS.items()])},
        "local_metadata_inventory": local_inventory,
        "source_assessments": source_assessments,
        "funding_source_status": funding["readiness_decision"],
        "oi_source_status": open_interest["readiness_decision"],
        "decision": decision,
        "next_recommendation": "V9.53 - Funding / OI Collection or Source Probe" if status == "PASS" else "V9.53 - Historical Source Manual Review",
        "blockers": build_blockers_v9_52(funding, open_interest),
        "warnings": [
            "La disponibilite 5Y funding doit etre confirmee par telechargement public dans V9.53.",
            "Open interest est traite comme limite historiquement tant qu'aucune archive publique fiable n'est prouvee.",
        ],
        "limitations": [
            "V9.52 ne telecharge aucune donnee et ne lance aucune ingestion.",
            "La readiness funding repose sur la convention Binance public archive et les rapports derivatives existants; la confirmation reseau arrive en V9.53.",
            "Aucune amelioration ML n'est revendiquee.",
        ],
        "collection_executed": False,
        "feature_store_created": False,
        "feature_store_validated": False,
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


def inspect_local_metadata_v9_52(root: Path) -> dict[str, Any]:
    inventory: dict[str, Any] = {}
    for name, rel_path in LOCAL_METADATA_PATHS.items():
        path = root / rel_path
        file_count = 0
        if path.is_file():
            file_count = 1
        elif path.is_dir():
            file_count = sum(1 for item in path.rglob("*") if item.is_file())
        inventory[name] = {
            "path": rel_path.as_posix(),
            "exists": path.exists(),
            "is_dir": path.is_dir(),
            "files_count": file_count,
        }
    funding_dir = root / "data/raw/binance_public/futures_um/fundingRate/BTCUSDT"
    inventory["local_funding_archive"] = {
        "path": funding_dir.relative_to(root).as_posix() if funding_dir.exists() else "data/raw/binance_public/futures_um/fundingRate/BTCUSDT",
        "exists": funding_dir.exists(),
        "zip_count": sum(1 for item in funding_dir.glob("*.zip")) if funding_dir.exists() else 0,
    }
    return inventory


def build_source_assessments_v9_52(root: Path, inputs: dict[str, dict[str, Any]], local_inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    old_coverage = inputs.get("derivatives_history_collection_plan_v9_17", {}).get("payload", {}).get("current_data_gap_summary", {})
    funding_window = old_coverage.get("funding_window", {})
    oi_window = old_coverage.get("open_interest_window", {})
    return {
        "funding_rate": {
            "source_name": "Binance public archive fundingRate monthly",
            "public_archive_available": "probable",
            "local_data_available": bool(funding_window.get("total_rows")) or local_inventory["local_funding_archive"]["zip_count"] > 0,
            "evidence_paths": [
                "reports/research_decisions/derivatives_history_collection_plan_v9_17.json",
                "reports/research/derivatives_collection_v1_14.json",
                "data/raw/binance_public/futures_um/fundingRate/BTCUSDT",
            ],
            "expected_symbol": SYMBOL,
            "expected_market_type": "futures_um",
            "expected_frequency": "8h native funding events",
            "coverage_start_known": funding_window.get("start"),
            "coverage_end_known": funding_window.get("end"),
            "historical_availability_assumption": "monthly public archive files should exist under data/futures/um/monthly/fundingRate/BTCUSDT/",
            "availability_needs_network_confirmation": True,
            "needs_api_key": False,
            "uses_private_endpoint": False,
            "rate_limit_or_history_limit": None,
            "causal_timestamp_fields": ["funding_time", "available_ts"],
            "leakage_risk": "medium_until_available_ts_policy_documented",
            "integration_complexity": "moderate",
            "priority": "priority_1",
            "expected_url_pattern": f"https://{HOST}/data/futures/um/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-YYYY-MM.zip",
            "readiness_decision": "funding_ready_for_public_archive_probe_and_collection",
        },
        "mark_price_klines": {
            "source_name": "Binance public archive markPriceKlines monthly",
            "public_archive_available": "probable",
            "local_data_available": local_inventory["raw_binance_public"]["exists"],
            "evidence_paths": ["data/raw/binance_public/futures_um/BTCUSDT/4h"],
            "expected_symbol": SYMBOL,
            "expected_market_type": "futures_um",
            "expected_frequency": "kline timeframes",
            "coverage_start_known": None,
            "coverage_end_known": None,
            "historical_availability_assumption": "optional context source; not required for first funding-only layer",
            "availability_needs_network_confirmation": True,
            "needs_api_key": False,
            "uses_private_endpoint": False,
            "rate_limit_or_history_limit": None,
            "causal_timestamp_fields": ["open_time", "close_time", "available_ts"],
            "leakage_risk": "medium_if_close_time_not_respected",
            "integration_complexity": "moderate",
            "priority": "optional",
            "expected_url_pattern": f"https://{HOST}/data/futures/um/monthly/markPriceKlines/BTCUSDT/<timeframe>/BTCUSDT-<timeframe>-YYYY-MM.zip",
            "readiness_decision": "optional_not_required_for_v9_53",
        },
        "premium_index_klines": {
            "source_name": "Binance public archive premiumIndexKlines monthly",
            "public_archive_available": "probable",
            "local_data_available": False,
            "evidence_paths": [],
            "expected_symbol": SYMBOL,
            "expected_market_type": "futures_um",
            "expected_frequency": "kline timeframes",
            "coverage_start_known": None,
            "coverage_end_known": None,
            "historical_availability_assumption": "optional context source; not required for first funding-only layer",
            "availability_needs_network_confirmation": True,
            "needs_api_key": False,
            "uses_private_endpoint": False,
            "rate_limit_or_history_limit": None,
            "causal_timestamp_fields": ["open_time", "close_time", "available_ts"],
            "leakage_risk": "medium_if_close_time_not_respected",
            "integration_complexity": "moderate",
            "priority": "optional",
            "expected_url_pattern": f"https://{HOST}/data/futures/um/monthly/premiumIndexKlines/BTCUSDT/<timeframe>/BTCUSDT-<timeframe>-YYYY-MM.zip",
            "readiness_decision": "optional_not_required_for_v9_53",
        },
        "open_interest": {
            "source_name": "Binance public openInterestHist",
            "public_archive_available": "not_confirmed",
            "local_data_available": bool(oi_window.get("total_rows")),
            "evidence_paths": [
                "reports/research_decisions/derivatives_history_collection_plan_v9_17.json",
                "reports/research/derivatives_collection_v1_14.json",
            ],
            "expected_symbol": SYMBOL,
            "expected_market_type": "futures_um",
            "expected_frequency": "endpoint-dependent, often 5m/15m/1h/4h",
            "coverage_start_known": oi_window.get("start"),
            "coverage_end_known": oi_window.get("end"),
            "historical_availability_assumption": "REST endpoint is likely history-limited and no proven 5Y public archive is present locally",
            "availability_needs_network_confirmation": True,
            "needs_api_key": False,
            "uses_private_endpoint": False,
            "rate_limit_or_history_limit": "history_limited_public_endpoint",
            "causal_timestamp_fields": ["timestamp", "available_ts"],
            "leakage_risk": "medium",
            "integration_complexity": "high_until_historical_source_proven",
            "priority": "non_blocking_optional",
            "expected_url_pattern": "public REST /futures/data/openInterestHist, not a proven multi-year archive",
            "readiness_decision": "oi_not_ready_history_limited",
        },
    }


def decide_source_readiness_v9_52(funding: dict[str, Any], open_interest: dict[str, Any]) -> str:
    funding_ready = funding.get("readiness_decision") == "funding_ready_for_public_archive_probe_and_collection"
    oi_limited = open_interest.get("readiness_decision") == "oi_not_ready_history_limited"
    if funding_ready and oi_limited:
        return "derivatives_source_readiness_funding_ready_oi_limited"
    if funding_ready:
        return "derivatives_source_readiness_funding_ready"
    return "derivatives_source_readiness_not_ready_source_uncertainty"


def build_blockers_v9_52(funding: dict[str, Any], open_interest: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not funding.get("readiness_decision", "").startswith("funding_ready"):
        blockers.append("funding public source is not ready")
    if open_interest.get("readiness_decision") == "oi_not_ready_history_limited":
        blockers.append("open interest is non-blocking but not ready for multi-year history")
    return blockers


def build_manifest_v9_52(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": report["created_at_utc"],
        "decision": report["decision"],
        "reports": [REPORT_JSON_PATH.as_posix(), REPORT_MD_PATH.as_posix(), DOC_PATH.as_posix()],
        "manifest_path": MANIFEST_PATH.as_posix(),
        "target_window": report["target_window"],
        "funding_source_status": report["funding_source_status"],
        "oi_source_status": report["oi_source_status"],
        "network_used": False,
        "new_data_downloaded": False,
        "no_sidecars": True,
        "no_zip_fingerprints": True,
    }


def build_markdown_v9_52(report: dict[str, Any]) -> str:
    return (
        "# V9.52 - Derivatives Source Readiness\n\n"
        f"- Decision : `{report['decision']}`.\n"
        f"- Funding : `{report['funding_source_status']}`.\n"
        f"- Open interest : `{report['oi_source_status']}`.\n"
        f"- Fenetre cible : `{TARGET_WINDOW_START}` -> `{TARGET_WINDOW_END}`.\n"
        "- Conclusion : funding public archive est prioritaire; OI reste optionnel et limite historiquement.\n\n"
        "Aucun trading, ML, dataset supervise, backtest, walk-forward, strategie, signal, telechargement ou ingestion dans V9.52.\n"
    )


def _load_input(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"available": False, "payload": None}
    if path.suffix == ".json":
        return {"available": True, "payload": json.loads(path.read_text(encoding="utf-8"))}
    return {"available": True, "payload": path.read_text(encoding="utf-8")}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
