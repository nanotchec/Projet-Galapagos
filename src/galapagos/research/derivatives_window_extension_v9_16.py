from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


VERSION = "V9.16"
LAST_VALIDATED_VERSION = "V9.15"
SOURCE_VERSION = "V9.15"
DIRECTION = "derivatives_window_extension_diagnostic"
REPORT_JSON_PATH = Path("reports/research_decisions/derivatives_window_extension_v9_16.json")
REPORT_MD_PATH = Path("reports/research_decisions/derivatives_window_extension_v9_16.md")
MANIFEST_PATH = Path("reports/manifests/derivatives_window_extension_v9_16_manifest.json")
DOC_PATH = Path("docs/derivatives_window_extension_v9_16.md")

V9_WINDOW = {
    "window_start": "2023-03-25T00:00:00Z",
    "window_end": "2024-03-24T23:59:59Z",
    "window_label": "2023-03-25_2024-03-24",
    "total_days": 366,
}
V9_TIMEFRAMES = ["1m", "5m", "15m", "1h"]
DERIVATIVES_REVIEW_TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h"]

ALLOWED_DECISIONS = {
    "derivatives_window_candidate_funding_only",
    "derivatives_window_candidate_funding_and_open_interest",
    "derivatives_window_candidate_4h_derivatives_native",
    "derivatives_window_not_ready_need_more_local_data",
    "derivatives_window_not_ready_too_short",
    "data_extension_should_collect_more_history",
    "stop_derivatives_extension_branch",
}

INPUT_PATHS = {
    "v9_15_decision": Path("reports/research_decisions/derivatives_data_extension_readiness_v9_15.json"),
    "v9_15_manifest": Path("reports/manifests/derivatives_data_extension_readiness_v9_15_manifest.json"),
    "v9_14_1_decision": Path("reports/research_decisions/feature_label_separability_v9_14_1.json"),
    "derivatives_coverage_v1_14": Path("reports/research/derivatives_coverage_v1_14.json"),
    "derivatives_data_quality_v1_14": Path("reports/research/derivatives_data_quality_v1_14.json"),
    "derivatives_features_v1_14": Path("reports/research/derivatives_features_v1_14.json"),
    "derivatives_coverage_expansion_v1_14": Path("reports/research/derivatives_coverage_expansion_v1_14.json"),
    "derivatives_readiness_v1_12_2": Path("reports/research/derivatives_readiness_v1_12_2.json"),
    "max_history_public_market_data_v5_0_manifest": Path("reports/manifests/max_history_public_market_data_v5_0_manifest.json"),
    "public_trades_1y_window_v8_2_manifest": Path("reports/manifests/public_trades_1y_window_v8_2_manifest.json"),
    "refined_ohlcv_trades_feature_store_v9_0_manifest": Path("reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "latest_summary": Path("reports/current/latest_summary.md"),
    "project_state": Path("reports/PROJECT_STATE.json"),
    "project_state_md": Path("reports/PROJECT_STATE.md"),
}

LOCAL_SOURCE_PATHS = {
    "data_research": Path("data/research"),
    "silver_derivatives": Path("data/silver/derivatives"),
    "gold_derivatives_features": Path("data/gold/derivatives_features"),
    "raw_binance_futures_4h": Path("data/raw/binance_public/futures_um/BTCUSDT/4h"),
    "raw_spot_klines_1m": Path("data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m"),
    "raw_spot_agg_trades": Path("data/raw/public_trades/binance_archive/spot/BTCUSDT/aggTrades"),
    "derivatives_code": Path("src/galapagos/data/derivatives"),
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
    "no_strategy": True,
    "no_actionable_signal": True,
    "no_persistent_model": True,
    "api_key_used": False,
    "private_endpoint_used": False,
    "network_used": False,
    "no_new_data_download": True,
    "no_sidecars": True,
    "no_zip_fingerprints": True,
}

SAFETY = {
    "public_read_only": True,
    "authentication_used": False,
    "api_key_used": False,
    "private_endpoint_used": False,
    "network_used": False,
    "new_data_downloaded": False,
    "orders_enabled": False,
    "paper_live_enabled": False,
    "trading_enabled": False,
    "labels_generated": False,
    "dataset_generated": False,
    "ml_training_enabled": False,
    "walk_forward_enabled": False,
    "backtest_enabled": False,
    "strategy_enabled": False,
    "execution_enabled": False,
    "persistent_model_created": False,
    "sidecars_created": False,
    "zip_fingerprints_created": False,
}


def run_derivatives_window_extension_v9_16(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_derivatives_window_extension_report_v9_16(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_16(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    manifest = build_manifest_v9_16(report)
    _write_json(root / MANIFEST_PATH, manifest)
    update_state_surfaces_v9_16(root, report)
    return report


def build_derivatives_window_extension_report_v9_16(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    payloads = {name: item["payload"] for name, item in inputs.items()}
    data_sources_inventory = build_data_sources_inventory_v9_16(root, payloads)
    candidate_windows = build_candidate_windows_v9_16(data_sources_inventory)
    compatibility = build_compatibility_analysis_v9_16(candidate_windows, data_sources_inventory)
    decision = decide_v9_16(candidate_windows, compatibility)
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "inputs_used": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "v9_15_context": summarize_v9_15_context_v9_16(payloads.get("v9_15_decision", {})),
        "v9_window": dict(V9_WINDOW),
        "v9_timeframes": list(V9_TIMEFRAMES),
        "data_sources_inventory": data_sources_inventory,
        "candidate_windows": candidate_windows,
        "compatibility_analysis": compatibility,
        "v9_16_decision": decision,
        "next_recommendation": decision["next_recommendation"],
        "features_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "findings": dict(FINDINGS),
        "safety": dict(SAFETY),
        "safety_flags": dict(SAFETY_FLAGS),
        "warnings": [
            "Les donnees funding locales commencent apres la fenetre aggTrades V8/V9 validee.",
            "Open interest local est trop tardif et trop court pour une branche research robuste.",
            "Les features derivatives V1.14 sont report-only dans ce diagnostic; V9.16 ne genere aucun feature store full.",
        ],
        "limitations": [
            "V9.16 utilise uniquement les rapports, manifests et metadonnees locales existantes.",
            "Aucun appel reseau, aucune API et aucun telechargement ne sont executes.",
            "Les fichiers Parquet complets ne sont pas lus massivement.",
            "Aucune fenetre n'est consideree viable si elle ne recouvre pas OHLCV, aggTrades et la source derivatives cible.",
        ],
    }


def summarize_v9_15_context_v9_16(v9_15: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": v9_15.get("v9_15_decision", {}).get("decision"),
        "features_candidate_created": v9_15.get("features_candidate_created"),
        "funding_coverage": {
            "start": v9_15.get("funding_readiness", {}).get("combined_coverage_start"),
            "end": v9_15.get("funding_readiness", {}).get("combined_coverage_end"),
        },
        "open_interest_coverage": {
            "start": v9_15.get("open_interest_readiness", {}).get("combined_coverage_start"),
            "end": v9_15.get("open_interest_readiness", {}).get("combined_coverage_end"),
        },
    }


def build_data_sources_inventory_v9_16(root: Path, payloads: dict[str, Any]) -> list[dict[str, Any]]:
    coverage = payloads.get("derivatives_coverage_v1_14", {})
    expansion = payloads.get("derivatives_coverage_expansion_v1_14", {})
    quality = payloads.get("derivatives_data_quality_v1_14", {})
    features = payloads.get("derivatives_features_v1_14", {})
    market_manifest = payloads.get("max_history_public_market_data_v5_0_manifest", {})
    trades_manifest = payloads.get("public_trades_1y_window_v8_2_manifest", {})
    local_paths = inspect_local_source_paths_v9_16(root)
    return [
        inventory_ohlcv_v9_16(local_paths, market_manifest, coverage),
        inventory_trades_v9_16(local_paths, trades_manifest),
        inventory_derivative_metric_v9_16("funding_rates", "funding_rate", coverage, expansion, quality, features),
        inventory_derivative_metric_v9_16("open_interest", "open_interest", coverage, expansion, quality, features),
        inventory_other_derivatives_v9_16(coverage, expansion, quality, features, local_paths),
    ]


def inspect_local_source_paths_v9_16(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, path in LOCAL_SOURCE_PATHS.items():
        full = root / path
        file_count = 0
        if full.is_file():
            file_count = 1
        elif full.is_dir():
            file_count = sum(1 for item in full.rglob("*") if item.is_file())
        result[name] = {
            "path": path.as_posix(),
            "exists": full.exists(),
            "is_dir": full.is_dir(),
            "files_count": file_count,
        }
    result["derivatives_report_paths"] = sorted(path.as_posix() for path in (root / "reports/research").glob("*derivatives*.json"))
    return result


def inventory_ohlcv_v9_16(local_paths: dict[str, Any], market_manifest: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    discovery = market_manifest.get("discovery", {})
    evidence = []
    if market_manifest:
        evidence.append("reports/manifests/max_history_public_market_data_v5_0_manifest.json")
    if coverage:
        evidence.append("reports/research/derivatives_coverage_v1_14.json")
    if local_paths["raw_spot_klines_1m"]["exists"]:
        evidence.append(local_paths["raw_spot_klines_1m"]["path"])
    return {
        "source_name": "OHLCV",
        "present_local": bool(evidence),
        "evidence_paths": evidence,
        "coverage_start": _date_to_timestamp(discovery.get("window_start") or coverage.get("ohlcv_start")),
        "coverage_end": _date_to_timestamp(discovery.get("window_end") or coverage.get("ohlcv_end"), end_of_day=True),
        "total_rows": _sum_output_rows(market_manifest.get("outputs", {})) or coverage.get("ohlcv_rows"),
        "frequency": "1m source, resampled to 5m/15m/1h in validated V9 chain; 4h available in V1.14 derivatives context.",
        "timeframe": "1m/5m/15m/1h and report-level 4h",
        "symbols": ["BTCUSDT"],
        "exchanges": ["binance"],
        "market_type": "spot",
        "data_layer": "raw/research/report",
        "quality_known": "good" if bool(evidence) else "unknown",
        "missing_rate": 0 if discovery.get("missing_dates") == [] else None,
        "available_ts_or_equivalent": True,
        "causal_alignment_feasibility": "good",
        "limitations": "Validated V9 features use the 2023-03-25 to 2024-03-24 slice; OHLCV raw history extends later than aggTrades.",
        "local_file_count": local_paths["raw_spot_klines_1m"]["files_count"],
    }


def inventory_trades_v9_16(local_paths: dict[str, Any], trades_manifest: dict[str, Any]) -> dict[str, Any]:
    discovery = trades_manifest.get("discovery", {})
    evidence = []
    if trades_manifest:
        evidence.append("reports/manifests/public_trades_1y_window_v8_2_manifest.json")
    if local_paths["raw_spot_agg_trades"]["exists"]:
        evidence.append(local_paths["raw_spot_agg_trades"]["path"])
    raw_files = trades_manifest.get("raw_files", {})
    return {
        "source_name": "trades_aggTrades",
        "present_local": bool(evidence),
        "evidence_paths": evidence,
        "coverage_start": _date_to_timestamp(discovery.get("window_start")),
        "coverage_end": _date_to_timestamp(discovery.get("window_end"), end_of_day=True),
        "total_rows": sum(int(item.get("rows") or 0) for item in raw_files.values()) if raw_files else None,
        "frequency": "event-level aggregate trades partitioned by day",
        "timeframe": "daily raw partitions, aggregated into 1m/5m/15m/1h features in V8/V9",
        "symbols": [trades_manifest.get("source", {}).get("symbol", "BTCUSDT")],
        "exchanges": [trades_manifest.get("source", {}).get("venue", "binance")],
        "market_type": trades_manifest.get("source", {}).get("market_type", "spot"),
        "data_layer": "raw/research",
        "quality_known": "good" if discovery.get("missing_dates") == [] else "partial",
        "missing_rate": 0 if discovery.get("missing_dates") == [] else None,
        "available_ts_or_equivalent": True,
        "causal_alignment_feasibility": "good",
        "limitations": "Local aggTrades evidence is the validated V8.2 one-year window only; it ends before funding starts.",
        "local_file_count": local_paths["raw_spot_agg_trades"]["files_count"],
    }


def inventory_derivative_metric_v9_16(
    source_name: str,
    metric_name: str,
    coverage: dict[str, Any],
    expansion: dict[str, Any],
    quality: dict[str, Any],
    features: dict[str, Any],
) -> dict[str, Any]:
    coverage_items = _metric_items(metric_name, coverage, expansion)
    available_items = [item for item in coverage_items if item.get("status") in {"available", "history_limited"} and int(item.get("rows") or item.get("rows_local") or 0) > 0]
    start_values = [item.get("start_timestamp") for item in available_items if item.get("start_timestamp")]
    end_values = [item.get("end_timestamp") for item in available_items if item.get("end_timestamp")]
    exchanges = sorted({item.get("source") for item in coverage_items if item.get("source")})
    missing_rates = _missing_rates_for_metric(metric_name, quality, features)
    return {
        "source_name": source_name,
        "metric_name": metric_name,
        "present_local": bool(coverage_items),
        "evidence_paths": _derivatives_evidence_paths(coverage, expansion, quality, features),
        "coverage_start": min(start_values) if start_values else None,
        "coverage_end": max(end_values) if end_values else None,
        "total_rows": sum(int(item.get("rows") or item.get("rows_local") or 0) for item in available_items),
        "frequency": _frequency_for_metric(metric_name, coverage_items),
        "timeframe": "8h native funding; open interest varies by provider and is reviewed as 4h-aligned in V1.14 reports.",
        "symbols": ["BTCUSDT"],
        "exchanges": exchanges,
        "market_type": "derivatives",
        "data_layer": "report-only/local derivative collection metadata",
        "quality_known": "partial" if available_items else "not_available",
        "missing_rate": missing_rates,
        "available_ts_or_equivalent": "available_timestamp" in features.get("columns", []),
        "causal_alignment_feasibility": "good" if "available_timestamp" in features.get("columns", []) else "medium",
        "limitations": "Coverage is local/report-derived only in V9.16; no network refresh is performed.",
        "coverage_checks": [
            {
                "source": item.get("source"),
                "status": item.get("status"),
                "rows": int(item.get("rows") or item.get("rows_local") or 0),
                "coverage_start": item.get("start_timestamp"),
                "coverage_end": item.get("end_timestamp"),
                "missing_rate": item.get("missing_rate"),
                "granularity": item.get("granularity"),
                "history_limit": item.get("history_limit") or item.get("known_limitations"),
            }
            for item in coverage_items
        ],
    }


def inventory_other_derivatives_v9_16(
    coverage: dict[str, Any],
    expansion: dict[str, Any],
    quality: dict[str, Any],
    features: dict[str, Any],
    local_paths: dict[str, Any],
) -> dict[str, Any]:
    metrics = ["premium", "taker_buy_sell_ratio", "long_short_ratio", "liquidations", "aggregated_open_interest"]
    items = [item for metric in metrics for item in _metric_items(metric, coverage, expansion)]
    available_items = [item for item in items if item.get("status") in {"available", "history_limited"} and int(item.get("rows") or item.get("rows_local") or 0) > 0]
    start_values = [item.get("start_timestamp") for item in available_items if item.get("start_timestamp")]
    end_values = [item.get("end_timestamp") for item in available_items if item.get("end_timestamp")]
    return {
        "source_name": "other_derivatives_local",
        "present_local": bool(items) or local_paths["raw_binance_futures_4h"]["exists"],
        "evidence_paths": _derivatives_evidence_paths(coverage, expansion, quality, features) + [local_paths["raw_binance_futures_4h"]["path"]],
        "coverage_start": min(start_values) if start_values else None,
        "coverage_end": max(end_values) if end_values else None,
        "total_rows": sum(int(item.get("rows") or item.get("rows_local") or 0) for item in available_items),
        "frequency": "mixed; local futures OHLCV is monthly 4h zip archives, derivatives metrics are sparse/report-level.",
        "timeframe": "4h native futures OHLCV and sparse derivatives metrics",
        "symbols": ["BTCUSDT"],
        "exchanges": sorted({item.get("source") for item in items if item.get("source")} | {"binance"}),
        "market_type": "derivatives",
        "data_layer": "raw/report",
        "quality_known": "partial",
        "missing_rate": {key: value for key, value in {**quality.get("missing_rates", {}), **features.get("missing_rates", {})}.items() if any(token in key for token in ["premium", "long_short", "taker", "liquidation"])},
        "available_ts_or_equivalent": "available_timestamp" in features.get("columns", []),
        "causal_alignment_feasibility": "medium",
        "limitations": "Other derivatives are sparse, provider-limited or require API keys; they are not candidates for V9.16 integration.",
        "local_file_count": local_paths["raw_binance_futures_4h"]["files_count"],
        "coverage_checks": [
            {
                "source": item.get("source"),
                "metric_name": item.get("metric_name"),
                "status": item.get("status"),
                "rows": int(item.get("rows") or item.get("rows_local") or 0),
                "coverage_start": item.get("start_timestamp"),
                "coverage_end": item.get("end_timestamp"),
                "known_limitations": item.get("known_limitations") or item.get("history_limit"),
            }
            for item in items
        ],
    }


def build_candidate_windows_v9_16(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name = {item["source_name"]: item for item in inventory}
    ohlcv = by_name["OHLCV"]
    trades = by_name["trades_aggTrades"]
    funding = by_name["funding_rates"]
    oi = by_name["open_interest"]
    other = by_name["other_derivatives_local"]
    return [
        make_candidate_window_v9_16(
            "funding_only_with_ohlcv_trades",
            [ohlcv, trades, funding],
            excluded_sources=["open_interest", "other_derivatives_local"],
            recommended_timeframes=["4h"] if _has_overlap([ohlcv, funding]) else [],
            description="Fenetre OHLCV + aggTrades + funding. Funding seul n'est pas bloquant, mais aggTrades est obligatoire pour rester coherent avec la chaine V9.",
        ),
        make_candidate_window_v9_16(
            "funding_and_open_interest_with_ohlcv_trades",
            [ohlcv, trades, funding, oi],
            excluded_sources=["other_derivatives_local"],
            recommended_timeframes=["4h"] if _has_overlap([ohlcv, funding, oi]) else [],
            description="Fenetre OHLCV + aggTrades + funding + open interest.",
        ),
        make_candidate_window_v9_16(
            "derivatives_4h_native",
            [ohlcv, funding, oi, other],
            excluded_sources=["spot_aggTrades_currently_missing_after_2024-03-24"],
            recommended_timeframes=["4h"],
            description="Fenetre 4h native derivatives. Elle exclut les aggTrades post-V9 faute de preuve locale.",
            force_partial=True,
        ),
        make_candidate_window_v9_16(
            "multi_year_ohlcv_trades_without_derivatives",
            [ohlcv, trades],
            excluded_sources=["funding_rates", "open_interest", "other_derivatives_local"],
            recommended_timeframes=list(V9_TIMEFRAMES),
            description="Comparaison OHLCV + aggTrades sans derivatives; non prioritaire car l'objectif V9.16 est data-extension derivatives.",
            comparison_only=True,
        ),
    ]


def make_candidate_window_v9_16(
    name: str,
    sources: list[dict[str, Any]],
    excluded_sources: list[str],
    recommended_timeframes: list[str],
    description: str,
    force_partial: bool = False,
    comparison_only: bool = False,
) -> dict[str, Any]:
    start, end = overlap_window_v9_16(sources)
    duration_days = duration_days_v9_16(start, end)
    included_names = [source["source_name"] for source in sources]
    status = candidate_status_v9_16(name, duration_days, force_partial, comparison_only, included_names)
    return {
        "candidate_window_name": name,
        "description": description,
        "window_start": start,
        "window_end": end,
        "duration_days": duration_days,
        "included_sources": included_names,
        "excluded_sources": excluded_sources,
        "expected_row_counts_by_timeframe": expected_rows_by_timeframe_v9_16(duration_days, recommended_timeframes),
        "overlap_quality": overlap_quality_v9_16(duration_days, force_partial, comparison_only),
        "coverage_risk": coverage_risk_v9_16(duration_days, included_names),
        "causal_alignment_risk": "medium" if any("derivatives" in name or "funding" in name for name in included_names) else "low",
        "missingness_risk": missingness_risk_v9_16(included_names),
        "recommended_timeframes": recommended_timeframes,
        "compatible_with_existing_v9_features": False if any(name in included_names for name in ["funding_rates", "open_interest", "other_derivatives_local"]) else True,
        "requires_new_feature_store": any(name in included_names for name in ["funding_rates", "open_interest", "other_derivatives_local"]),
        "requires_new_labels": any(name in included_names for name in ["funding_rates", "open_interest", "other_derivatives_local"]),
        "requires_new_dataset": any(name in included_names for name in ["funding_rates", "open_interest", "other_derivatives_local"]),
        "recommendation_status": status,
        "limitations": candidate_limitations_v9_16(name, duration_days, included_names),
    }


def overlap_window_v9_16(sources: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    starts = [_parse_timestamp(source.get("coverage_start")) for source in sources if source.get("coverage_start")]
    ends = [_parse_timestamp(source.get("coverage_end")) for source in sources if source.get("coverage_end")]
    if len(starts) != len(sources) or len(ends) != len(sources):
        return None, None
    start = max(starts)
    end = min(ends)
    if start > end:
        return _format_ts(start), _format_ts(end)
    return _format_ts(start), _format_ts(end)


def duration_days_v9_16(start: str | None, end: str | None) -> int:
    if not start or not end:
        return 0
    start_dt = _parse_timestamp(start)
    end_dt = _parse_timestamp(end)
    if start_dt is None or end_dt is None or start_dt > end_dt:
        return 0
    return max(1, (end_dt.date() - start_dt.date()).days + 1)


def candidate_status_v9_16(name: str, duration_days: int, force_partial: bool, comparison_only: bool, included_sources: list[str]) -> str:
    if comparison_only:
        return "not_viable"
    if duration_days < 90:
        return "too_short" if duration_days > 0 else "not_viable"
    if force_partial or "open_interest" in included_sources:
        return "partial_candidate_requires_alignment"
    if "funding_rates" in included_sources and "trades_aggTrades" in included_sources:
        return "viable_candidate"
    return "unknown"


def expected_rows_by_timeframe_v9_16(duration_days: int, timeframes: list[str]) -> dict[str, int] | None:
    if duration_days <= 0 or not timeframes:
        return None
    per_day = {"1m": 1440, "5m": 288, "15m": 96, "1h": 24, "4h": 6}
    return {timeframe: duration_days * per_day[timeframe] for timeframe in timeframes if timeframe in per_day}


def overlap_quality_v9_16(duration_days: int, force_partial: bool, comparison_only: bool) -> str:
    if comparison_only:
        return "comparison_only"
    if duration_days <= 0:
        return "none"
    if duration_days < 90:
        return "too_short"
    if force_partial:
        return "partial"
    if duration_days < 366:
        return "medium"
    return "good"


def coverage_risk_v9_16(duration_days: int, included_sources: list[str]) -> str:
    if duration_days <= 0:
        return "high_no_overlap"
    if duration_days < 90 or "open_interest" in included_sources:
        return "high"
    if duration_days < 366:
        return "medium"
    return "low"


def missingness_risk_v9_16(included_sources: list[str]) -> str:
    if "open_interest" in included_sources:
        return "high"
    if "funding_rates" in included_sources:
        return "medium"
    return "low"


def candidate_limitations_v9_16(name: str, duration_days: int, included_sources: list[str]) -> list[str]:
    limitations: list[str] = []
    if duration_days <= 0:
        limitations.append("Aucune intersection temporelle exploitable entre toutes les sources incluses.")
    if name == "funding_only_with_ohlcv_trades":
        limitations.append("Funding commence le 2024-05-05 alors que les aggTrades valides s'arretent le 2024-03-24.")
    if name == "funding_and_open_interest_with_ohlcv_trades":
        limitations.append("Open interest commence surtout en 2026 et ne recouvre pas les aggTrades V8/V9.")
    if name == "derivatives_4h_native":
        limitations.append("La piste 4h native exclut les aggTrades post-V9; elle necessite une nouvelle collecte/validation si elle devient prioritaire.")
    if name == "multi_year_ohlcv_trades_without_derivatives":
        limitations.append("Fenetre de comparaison sans derivatives; elle ne repond pas a l'objectif prioritaire d'extension derivatives.")
    if "open_interest" in included_sources:
        limitations.append("Open interest local est trop sparse pour supporter une recherche robuste sans extension historique.")
    return limitations


def build_compatibility_analysis_v9_16(candidate_windows: list[dict[str, Any]], inventory: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {item["source_name"]: item for item in inventory}
    funding_only = _candidate(candidate_windows, "funding_only_with_ohlcv_trades")
    funding_oi = _candidate(candidate_windows, "funding_and_open_interest_with_ohlcv_trades")
    native_4h = _candidate(candidate_windows, "derivatives_4h_native")
    return {
        "enough_for_future_ml": False,
        "enough_for_future_walk_forward": False,
        "compatible_with_temporal_train_validation_test": False,
        "compatible_with_monthly_folds": False,
        "funding_only_more_realistic_than_oi_plus_funding": True,
        "open_interest_window_too_short": True,
        "derivatives_4h_should_be_considered_only_after_data_alignment": True,
        "old_v9_labels_should_not_be_reused_blindly": True,
        "existing_v9_feature_store_reusable": False,
        "requires_new_feature_store": True,
        "requires_new_labels": True,
        "requires_new_dataset": True,
        "funding_only_candidate_status": funding_only["recommendation_status"],
        "funding_and_open_interest_candidate_status": funding_oi["recommendation_status"],
        "derivatives_4h_native_candidate_status": native_4h["recommendation_status"],
        "main_blockers": [
            "Les aggTrades locaux s'arretent le 2024-03-24 alors que le funding local commence le 2024-05-05.",
            "Open interest local couvre surtout 2026-04-02 a 2026-05-05, ce qui est trop court.",
            "Les sorties gold derivatives features V1.14 sont documentees par rapport mais aucun fichier full n'est present sous data/gold/derivatives_features dans l'inspection locale.",
        ],
        "ohlcv_coverage_summary": {
            "start": by_name["OHLCV"].get("coverage_start"),
            "end": by_name["OHLCV"].get("coverage_end"),
        },
        "trades_coverage_summary": {
            "start": by_name["trades_aggTrades"].get("coverage_start"),
            "end": by_name["trades_aggTrades"].get("coverage_end"),
        },
        "funding_coverage_summary": {
            "start": by_name["funding_rates"].get("coverage_start"),
            "end": by_name["funding_rates"].get("coverage_end"),
        },
        "open_interest_coverage_summary": {
            "start": by_name["open_interest"].get("coverage_start"),
            "end": by_name["open_interest"].get("coverage_end"),
        },
        "research_recommendation_boundary": "Ne pas lancer walk-forward, backtest, strategie ou signal; collecter/valider l'historique manquant avant toute branche predictive.",
    }


def decide_v9_16(candidate_windows: list[dict[str, Any]], compatibility: dict[str, Any]) -> dict[str, Any]:
    funding_only = _candidate(candidate_windows, "funding_only_with_ohlcv_trades")
    funding_oi = _candidate(candidate_windows, "funding_and_open_interest_with_ohlcv_trades")
    native_4h = _candidate(candidate_windows, "derivatives_4h_native")
    if funding_oi["recommendation_status"] == "viable_candidate":
        decision = "derivatives_window_candidate_funding_and_open_interest"
        recommendation = "V9.17 - Funding + Open Interest Derivatives Feature Store Candidate."
        confidence = "medium"
        justification = "Funding et open interest recouvrent assez OHLCV/trades pour une future branche."
    elif funding_only["recommendation_status"] == "viable_candidate":
        decision = "derivatives_window_candidate_funding_only"
        recommendation = "V9.17 - Funding-Only Derivatives Feature Store Candidate."
        confidence = "medium"
        justification = "Funding recouvre assez OHLCV/trades et OI peut rester exclu."
    elif native_4h["recommendation_status"] == "viable_candidate":
        decision = "derivatives_window_candidate_4h_derivatives_native"
        recommendation = "V9.17 - 4H Derivatives-Native Research Window Candidate."
        confidence = "medium"
        justification = "La fenetre derivatives 4h native est exploitable et suffisamment longue."
    elif compatibility["open_interest_window_too_short"] and compatibility["funding_only_more_realistic_than_oi_plus_funding"]:
        decision = "data_extension_should_collect_more_history"
        recommendation = "V9.17 - Derivatives History Collection Plan."
        confidence = "high"
        justification = "Funding a une couverture locale post-V9 mais ne recouvre pas les aggTrades; open interest est trop court. Il faut collecter/valider l'historique manquant avant toute feature candidate."
    else:
        decision = "derivatives_window_not_ready_need_more_local_data"
        recommendation = "V9.17 - Derivatives Data Alignment Correction."
        confidence = "medium"
        justification = "Les preuves locales ne suffisent pas pour une fenetre derivatives coherente."
    return {
        "decision": decision,
        "confidence": confidence,
        "justification": justification,
        "next_recommendation": recommendation,
        "no_backtest": True,
        "no_walk_forward": True,
        "no_trading": True,
    }


def build_manifest_v9_16(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": report["status"],
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "v9_16_decision": report["v9_16_decision"],
        "candidate_windows_count": len(report["candidate_windows"]),
        "data_sources_count": len(report["data_sources_inventory"]),
        "features_created": report["features_created"],
        "dataset_created": report["dataset_created"],
        "ml_executed": report["ml_executed"],
        "walk_forward_executed": report["walk_forward_executed"],
        "backtest_executed": report["backtest_executed"],
        "inputs_used": report["inputs_used"],
        "findings": report["findings"],
        "safety": report["safety"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_16(report: dict[str, Any]) -> str:
    decision = report["v9_16_decision"]
    inventory = {item["source_name"]: item for item in report["data_sources_inventory"]}
    candidates = {item["candidate_window_name"]: item for item in report["candidate_windows"]}
    lines = [
        "# V9.16 - Derivatives Window Extension Diagnostic",
        "",
        "## Resume executif",
        f"- Decision V9.16 : `{decision['decision']}`.",
        f"- Justification : {decision['justification']}",
        f"- Recommandation suivante : {decision['next_recommendation']}",
        "- V9.16 est uniquement un diagnostic de fenetre et de disponibilite locale.",
        "- Aucun feature store full, dataset supervise, ML, walk-forward, backtest, strategie ou signal actionnable.",
        "",
        "## Inventaire des fenetres",
        f"- OHLCV : `{inventory['OHLCV']['coverage_start']}` -> `{inventory['OHLCV']['coverage_end']}`.",
        f"- aggTrades : `{inventory['trades_aggTrades']['coverage_start']}` -> `{inventory['trades_aggTrades']['coverage_end']}`.",
        f"- Funding : `{inventory['funding_rates']['coverage_start']}` -> `{inventory['funding_rates']['coverage_end']}`.",
        f"- Open interest : `{inventory['open_interest']['coverage_start']}` -> `{inventory['open_interest']['coverage_end']}`.",
        f"- Autres derivatives : `{inventory['other_derivatives_local']['coverage_start']}` -> `{inventory['other_derivatives_local']['coverage_end']}`.",
        "",
        "## Fenetres candidates",
        f"- Funding-only + OHLCV/trades : `{candidates['funding_only_with_ohlcv_trades']['recommendation_status']}`, duree `{candidates['funding_only_with_ohlcv_trades']['duration_days']}` jours.",
        f"- Funding + OI + OHLCV/trades : `{candidates['funding_and_open_interest_with_ohlcv_trades']['recommendation_status']}`, duree `{candidates['funding_and_open_interest_with_ohlcv_trades']['duration_days']}` jours.",
        f"- Derivatives 4h native : `{candidates['derivatives_4h_native']['recommendation_status']}`, duree `{candidates['derivatives_4h_native']['duration_days']}` jours.",
        f"- Multi-year OHLCV/trades sans derivatives : `{candidates['multi_year_ohlcv_trades_without_derivatives']['recommendation_status']}`.",
        "",
        "## Compatibilite research",
        f"- Suffisant pour futur ML : `{report['compatibility_analysis']['enough_for_future_ml']}`.",
        f"- Suffisant pour futur walk-forward : `{report['compatibility_analysis']['enough_for_future_walk_forward']}`.",
        f"- Funding-only plus realiste que OI+funding : `{report['compatibility_analysis']['funding_only_more_realistic_than_oi_plus_funding']}`.",
        f"- Open interest trop court : `{report['compatibility_analysis']['open_interest_window_too_short']}`.",
        "",
        "## Interdits maintenus",
        "- Aucun trading reel.",
        "- Aucun paper live.",
        "- Aucun ordre.",
        "- Aucun backtest execute.",
        "- Aucun walk-forward.",
        "- Aucune strategie.",
        "- Aucun signal actionnable.",
        "- Aucun modele persistant.",
        "- Aucune API privee.",
        "- Aucune cle API.",
        "- Aucun reseau et aucun telechargement de nouvelles donnees.",
        "- Aucun sidecar et aucune empreinte ZIP.",
    ]
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_16(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_16_decision": report["v9_16_decision"]["decision"],
        "recommended_next_step": report["next_recommendation"],
        "features_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "no_new_data_download": True,
        **SAFETY_FLAGS,
    }
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    for stale_key in ["recommended_next_version", "recommended_next_action"]:
        state.pop(stale_key, None)
    state.update(metrics)
    _write_json(state_path, state)
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    summary = (
        "# Synthese courante - V9.16\n\n"
        "- Derniere version validee : `V9.15`.\n"
        "- Candidate : `V9.16`.\n"
        "- Statut : `pending_external_audit`.\n"
        "- Direction : diagnostic de fenetre derivatives.\n"
        f"- Decision V9.16 : `{report['v9_16_decision']['decision']}`.\n"
        f"- Recommandation : {report['next_recommendation']}\n"
        "- Aucun feature store full, dataset supervise, ML, walk-forward, backtest, strategie, signal actionnable, ordre ou trading.\n"
        "- Aucun reseau, aucun telechargement de nouvelles donnees, aucun sidecar et aucune empreinte ZIP.\n"
    )
    _write_text(root / "reports/PROJECT_STATE.md", summary)
    _write_text(root / "reports/current/latest_summary.md", summary)
    _write_text(root / "reports/current/latest_metrics.md", summary)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        "- Derniere version validee : V9.15.\n"
        "- Candidate : V9.16, diagnostic de fenetre derivatives.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun reseau, aucun telechargement de nouvelles donnees, aucun sidecar et aucune empreinte ZIP.\n",
    )


def _candidate(candidates: list[dict[str, Any]], name: str) -> dict[str, Any]:
    return next(item for item in candidates if item["candidate_window_name"] == name)


def _has_overlap(sources: list[dict[str, Any]]) -> bool:
    start, end = overlap_window_v9_16(sources)
    return duration_days_v9_16(start, end) > 0


def _metric_items(metric_name: str, coverage: dict[str, Any], expansion: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [dict(item) for item in coverage.get("checks", []) if item.get("metric_name") == metric_name]
    expansion_items = [dict(item) for item in expansion.get("metrics", []) if item.get("metric_name") == metric_name]
    seen = {(item.get("source"), item.get("metric_name"), item.get("start_timestamp"), item.get("end_timestamp")) for item in checks}
    for item in expansion_items:
        key = (item.get("source"), item.get("metric_name"), item.get("start_timestamp"), item.get("end_timestamp"))
        if key not in seen:
            checks.append(item)
    return checks


def _derivatives_evidence_paths(coverage: dict[str, Any], expansion: dict[str, Any], quality: dict[str, Any], features: dict[str, Any]) -> list[str]:
    evidence: list[str] = []
    if coverage:
        evidence.append("reports/research/derivatives_coverage_v1_14.json")
    if expansion:
        evidence.append("reports/research/derivatives_coverage_expansion_v1_14.json")
    if quality:
        evidence.append("reports/research/derivatives_data_quality_v1_14.json")
    if features:
        evidence.append("reports/research/derivatives_features_v1_14.json")
    return evidence


def _missing_rates_for_metric(metric_name: str, quality: dict[str, Any], features: dict[str, Any]) -> dict[str, Any]:
    merged = {**quality.get("missing_rates", {}), **features.get("missing_rates", {})}
    if metric_name == "funding_rate":
        tokens = ["funding"]
    elif metric_name == "open_interest":
        tokens = ["open_interest", "oi_"]
    else:
        tokens = [metric_name]
    return {key: value for key, value in merged.items() if any(token in key for token in tokens)}


def _frequency_for_metric(metric_name: str, items: list[dict[str, Any]]) -> str:
    granularities = sorted({item.get("granularity") for item in items if item.get("granularity")})
    if granularities:
        return ", ".join(granularities)
    if metric_name == "funding_rate":
        return "8h native where available"
    return "provider-dependent"


def _sum_output_rows(outputs: dict[str, Any]) -> int | None:
    rows = [int(item.get("rows") or 0) for item in outputs.values() if isinstance(item, dict)]
    return sum(rows) if rows else None


def _date_to_timestamp(value: str | None, end_of_day: bool = False) -> str | None:
    if not value:
        return None
    if "T" in value or " " in value:
        parsed = _parse_timestamp(value)
        return _format_ts(parsed) if parsed else None
    suffix = "T23:59:59Z" if end_of_day else "T00:00:00Z"
    return f"{value}{suffix}"


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        cleaned = value.replace("Z", "+00:00")
        if " " in cleaned and "T" not in cleaned:
            cleaned = cleaned.replace(" ", "T")
        parsed = datetime.fromisoformat(cleaned)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except ValueError:
        return None


def _format_ts(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_input(root: Path, path: Path) -> dict[str, Any]:
    full = root / path
    if not full.exists():
        return {"path": path.as_posix(), "available": False, "payload": {}}
    if path.suffix == ".json":
        payload: Any = _read_json(full)
    else:
        payload = {"text": full.read_text(encoding="utf-8")}
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
