from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


VERSION = "V9.17"
LAST_VALIDATED_VERSION = "V9.16"
SOURCE_VERSION = "V9.16"
DIRECTION = "derivatives_history_collection_plan"
REPORT_JSON_PATH = Path("reports/research_decisions/derivatives_history_collection_plan_v9_17.json")
REPORT_MD_PATH = Path("reports/research_decisions/derivatives_history_collection_plan_v9_17.md")
MANIFEST_PATH = Path("reports/manifests/derivatives_history_collection_plan_v9_17_manifest.json")
DOC_PATH = Path("docs/derivatives_history_collection_plan_v9_17.md")

ALLOWED_DECISIONS = {
    "collection_plan_priority_aggtrades_post_v9_and_funding",
    "collection_plan_priority_historical_funding_for_v9_window",
    "collection_plan_priority_derivatives_native_4h",
    "collection_plan_priority_open_interest_history",
    "collection_plan_not_ready_need_manual_source_research",
    "stop_derivatives_collection_branch",
}

INPUT_PATHS = {
    "v9_16_decision": Path("reports/research_decisions/derivatives_window_extension_v9_16.json"),
    "v9_16_manifest": Path("reports/manifests/derivatives_window_extension_v9_16_manifest.json"),
    "v9_15_decision": Path("reports/research_decisions/derivatives_data_extension_readiness_v9_15.json"),
    "v9_14_1_decision": Path("reports/research_decisions/feature_label_separability_v9_14_1.json"),
    "derivatives_coverage_v1_14": Path("reports/research/derivatives_coverage_v1_14.json"),
    "derivatives_data_quality_v1_14": Path("reports/research/derivatives_data_quality_v1_14.json"),
    "derivatives_features_v1_14": Path("reports/research/derivatives_features_v1_14.json"),
    "derivatives_coverage_expansion_v1_14": Path("reports/research/derivatives_coverage_expansion_v1_14.json"),
    "max_history_public_market_data_v5_0_manifest": Path("reports/manifests/max_history_public_market_data_v5_0_manifest.json"),
    "public_trades_1y_window_v8_2_manifest": Path("reports/manifests/public_trades_1y_window_v8_2_manifest.json"),
    "refined_ohlcv_trades_feature_store_v9_0_manifest": Path("reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "latest_summary": Path("reports/current/latest_summary.md"),
    "project_state": Path("reports/PROJECT_STATE.json"),
    "project_state_md": Path("reports/PROJECT_STATE.md"),
}

LOCAL_METADATA_PATHS = {
    "data_raw": Path("data/raw"),
    "raw_binance_public": Path("data/raw/binance_public"),
    "raw_public_market": Path("data/raw/public_market"),
    "raw_public_trades": Path("data/raw/public_trades"),
    "data_silver": Path("data/silver"),
    "data_gold": Path("data/gold"),
    "reports_manifests": Path("reports/manifests"),
    "reports_research": Path("reports/research"),
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
    "no_strategy": True,
    "no_actionable_signal": True,
    "no_persistent_model": True,
    "api_key_used": False,
    "private_endpoint_used": False,
    "network_used": False,
    "no_new_data_download": True,
    "no_ingestion_executed": True,
    "no_sidecars": True,
    "no_zip_fingerprints": True,
}

SAFETY = {
    "public_read_only_plan": True,
    "authentication_used": False,
    "api_key_used": False,
    "private_endpoint_used": False,
    "network_used": False,
    "new_data_downloaded": False,
    "ingestion_executed": False,
    "orders_enabled": False,
    "paper_live_enabled": False,
    "trading_enabled": False,
    "labels_generated": False,
    "feature_store_generated": False,
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


def run_derivatives_history_collection_plan_v9_17(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_derivatives_history_collection_plan_report_v9_17(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_17(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    manifest = build_manifest_v9_17(report)
    _write_json(root / MANIFEST_PATH, manifest)
    update_state_surfaces_v9_17(root, report)
    return report


def build_derivatives_history_collection_plan_report_v9_17(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    payloads = {name: item["payload"] for name, item in inputs.items()}
    local_metadata = inspect_local_metadata_v9_17(root)
    gap_summary = build_current_data_gap_summary_v9_17(payloads)
    source_candidates = build_source_collection_candidates_v9_17(gap_summary, payloads)
    target_windows = build_candidate_target_windows_v9_17(gap_summary)
    future_plan = build_future_collection_plan_v9_17(source_candidates, target_windows)
    storage_plan = build_storage_plan_v9_17()
    quality_plan = build_quality_validation_plan_v9_17()
    anti_leakage_plan = build_anti_leakage_plan_v9_17()
    decision = decide_v9_17(source_candidates, target_windows)
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "inputs_used": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "local_metadata_inventory": local_metadata,
        "current_data_gap_summary": gap_summary,
        "source_collection_candidates": source_candidates,
        "candidate_target_windows": target_windows,
        "future_collection_plan": future_plan,
        "storage_plan": storage_plan,
        "quality_validation_plan": quality_plan,
        "anti_leakage_plan": anti_leakage_plan,
        "v9_17_decision": decision,
        "next_recommendation": decision["next_recommendation"],
        "collection_executed": False,
        "features_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "blockers": [
            "Les aggTrades locaux valides s'arretent le 2024-03-24 alors que le funding local commence le 2024-05-05.",
            "Open interest local ne couvre qu'une fenetre recente trop courte pour une recherche robuste.",
            "V9.17 est un plan: aucune collecte future n'est executee dans cette version.",
        ],
        "warnings": [
            "La future collecte devra etre publique, read-only, reproductible et separee d'un audit externe.",
            "OI ne doit pas bloquer la premiere branche si le chemin funding-only est plus simple et auditable.",
        ],
        "limitations": [
            "V9.17 ne verifie pas en ligne la disponibilite reelle des endpoints publics.",
            "Les estimations de fenetre viennent des rapports/manifests locaux existants.",
            "Aucun fichier full Parquet/CSV n'est lu massivement.",
        ],
        "findings": dict(FINDINGS),
        "safety": dict(SAFETY),
        "safety_flags": dict(SAFETY_FLAGS),
    }


def inspect_local_metadata_v9_17(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, path in LOCAL_METADATA_PATHS.items():
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
    result["network_used_in_v9_17"] = False
    result["new_data_downloaded_in_v9_17"] = False
    result["ingestion_executed_in_v9_17"] = False
    return result


def build_current_data_gap_summary_v9_17(payloads: dict[str, Any]) -> dict[str, Any]:
    v9_16 = payloads.get("v9_16_decision", {})
    inventory = {item.get("source_name"): item for item in v9_16.get("data_sources_inventory", [])}
    ohlcv = inventory.get("OHLCV", {})
    trades = inventory.get("trades_aggTrades", {})
    funding = inventory.get("funding_rates", {})
    open_interest = inventory.get("open_interest", {})
    other = inventory.get("other_derivatives_local", {})
    funding_gap = gap_between_v9_17(trades.get("coverage_end"), funding.get("coverage_start"))
    oi_gap = gap_between_v9_17(trades.get("coverage_end"), open_interest.get("coverage_start"))
    return {
        "source_version": SOURCE_VERSION,
        "v9_16_decision": v9_16.get("v9_16_decision", {}).get("decision"),
        "ohlcv_window": {"start": ohlcv.get("coverage_start"), "end": ohlcv.get("coverage_end"), "total_rows": ohlcv.get("total_rows")},
        "aggtrades_window": {"start": trades.get("coverage_start"), "end": trades.get("coverage_end"), "total_rows": trades.get("total_rows")},
        "funding_window": {"start": funding.get("coverage_start"), "end": funding.get("coverage_end"), "total_rows": funding.get("total_rows")},
        "open_interest_window": {"start": open_interest.get("coverage_start"), "end": open_interest.get("coverage_end"), "total_rows": open_interest.get("total_rows")},
        "other_derivatives_window": {"start": other.get("coverage_start"), "end": other.get("coverage_end"), "total_rows": other.get("total_rows")},
        "aggtrades_to_funding_gap_days": funding_gap,
        "aggtrades_to_open_interest_gap_days": oi_gap,
        "primary_gap": "aggTrades post-2024-03-24 are missing for the already-local funding window.",
        "open_interest_gap": "Open interest starts too late and should not be priority 1.",
        "current_common_window_ohlcv_aggtrades_funding_days": 0,
        "current_common_window_ohlcv_aggtrades_funding_oi_days": 0,
        "collection_needed_before_feature_candidate": True,
    }


def build_source_collection_candidates_v9_17(gap_summary: dict[str, Any], payloads: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        source_candidate_v9_17(
            source_name="aggTrades_public_trades_post_v9",
            target_symbol="BTCUSDT",
            market_type="spot",
            desired_start="2024-03-25T00:00:00Z",
            desired_end=gap_summary["funding_window"]["end"],
            desired_frequency="event-level aggregate trades partitioned daily",
            public_source_candidate="Binance public archive aggTrades daily files",
            needs_api_key=False,
            network_required_future_collection=True,
            expected_file_format="zip csv raw, parquet silver/research after validation",
            target_storage_layer="bronze/raw then silver/research",
            expected_partitioning="source=binance_archive/market_type=spot/symbol=BTCUSDT/date=YYYY-MM-DD",
            expected_causal_timestamp_fields=["event_ts", "trade_ts", "ingest_ts", "available_ts", "decision_ts"],
            quality_checks_required=["date completeness", "schema strictness", "monotonic aggregate_trade_id", "duplicate aggregate_trade_id", "price_quantity_positive", "timezone_utc", "checksum_manifest"],
            leakage_risks=["using files not available by decision_ts", "mixing partial days with complete historical windows"],
            integration_priority="priority_1",
            recommendation="Collect and validate post-V9 aggTrades first because funding is already local after 2024-05-05.",
        ),
        source_candidate_v9_17(
            source_name="funding_rates_historical",
            target_symbol="BTCUSDT",
            market_type="derivatives",
            desired_start="2023-03-25T00:00:00Z",
            desired_end="2026-05-05T08:00:00Z",
            desired_frequency="8h native",
            public_source_candidate="Public futures funding history endpoints or archival source, to be confirmed in a future collection implementation plan",
            needs_api_key=False,
            network_required_future_collection=True,
            expected_file_format="json/csv raw, parquet silver/research after validation",
            target_storage_layer="bronze/raw then silver/research",
            expected_partitioning="source=<venue>/market_type=derivatives/symbol=BTCUSDT/date=YYYY-MM-DD or month=YYYY-MM",
            expected_causal_timestamp_fields=["event_ts", "source_publish_ts", "ingest_ts", "available_ts"],
            quality_checks_required=["coverage start/end", "8h cadence", "duplicate timestamp", "timezone_utc", "available_ts_not_before_publish", "gap report"],
            leakage_risks=["backfilling funding rows into earlier decision times without publish timestamp", "provider revisions without versioned raw snapshots"],
            integration_priority="priority_1",
            recommendation="Attempt historical funding coverage for the V9 window only after preserving a no-key public read-only collection design.",
        ),
        source_candidate_v9_17(
            source_name="open_interest_history",
            target_symbol="BTCUSDT",
            market_type="derivatives",
            desired_start="2024-05-05T00:00:00Z",
            desired_end="2026-05-05T12:00:00Z",
            desired_frequency="4h or provider-native historical cadence",
            public_source_candidate="Public open interest historical endpoints if available; otherwise manual source research",
            needs_api_key=False,
            network_required_future_collection=True,
            expected_file_format="json/csv raw, parquet silver/research after validation",
            target_storage_layer="bronze/raw then silver/research",
            expected_partitioning="source=<venue>/market_type=derivatives/symbol=BTCUSDT/frequency=<freq>/date=YYYY-MM-DD",
            expected_causal_timestamp_fields=["event_ts", "source_publish_ts", "ingest_ts", "available_ts"],
            quality_checks_required=["coverage", "frequency consistency", "staleness", "duplicates", "gaps", "unit consistency"],
            leakage_risks=["snapshot-only OI treated as historical", "silent provider lookback limits"],
            integration_priority="priority_2",
            recommendation="Do not block the first funding branch on OI; collect only after funding/aggTrades coverage is solved.",
        ),
        source_candidate_v9_17(
            source_name="derivatives_ohlcv_futures_klines_4h",
            target_symbol="BTCUSDT",
            market_type="derivatives",
            desired_start="2024-05-05T00:00:00Z",
            desired_end="2026-05-05T00:00:00Z",
            desired_frequency="4h",
            public_source_candidate="Local Binance public futures 4h archive plus future validated extension if needed",
            needs_api_key=False,
            network_required_future_collection=False,
            expected_file_format="zip csv raw, parquet silver/research after validation",
            target_storage_layer="bronze/raw then silver/research",
            expected_partitioning="source=binance_public/market_type=futures_um/symbol=BTCUSDT/timeframe=4h/month=YYYY-MM",
            expected_causal_timestamp_fields=["event_ts", "close_ts", "ingest_ts", "available_ts", "decision_ts"],
            quality_checks_required=["monthly completeness", "4h row count", "ohlc validity", "timezone_utc", "monotonic close_ts", "gap report"],
            leakage_risks=["using close_ts before candle close", "mixing spot and futures features without explicit market_type"],
            integration_priority="priority_2",
            recommendation="Keep as a 4h-native backup branch, not as the first branch if aggTrades can be extended.",
        ),
        source_candidate_v9_17(
            source_name="liquidations_long_short_ratios",
            target_symbol="BTCUSDT",
            market_type="derivatives",
            desired_start="2024-05-05T00:00:00Z",
            desired_end="2026-05-05T00:00:00Z",
            desired_frequency="provider-native",
            public_source_candidate="Only public no-key historical sources if proven; no private provider in V9.17",
            needs_api_key=False,
            network_required_future_collection=True,
            expected_file_format="json/csv raw, parquet silver/research after validation",
            target_storage_layer="bronze/raw then silver/research or not collected",
            expected_partitioning="source=<venue>/market_type=derivatives/symbol=BTCUSDT/metric=<metric>/date=YYYY-MM-DD",
            expected_causal_timestamp_fields=["event_ts", "source_publish_ts", "ingest_ts", "available_ts"],
            quality_checks_required=["source availability proof", "coverage", "gap report", "duplicates", "timezone_utc"],
            leakage_risks=["provider-derived aggregates with unknown publication time", "requiring private API keys"],
            integration_priority="later",
            recommendation="Do not prioritize before aggTrades/funding; reject if a key or private endpoint is required.",
        ),
    ]


def source_candidate_v9_17(**kwargs: Any) -> dict[str, Any]:
    return dict(kwargs)


def build_candidate_target_windows_v9_17(gap_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        target_window_v9_17(
            window_name="funding_first_post_v9",
            desired_start="2024-05-05T00:00:00Z",
            desired_end="2026-05-05T00:00:00Z",
            included_sources=["OHLCV", "aggTrades", "funding_rates"],
            missing_sources=["aggTrades post-2024-03-24"],
            minimum_required_history_days=366,
            currently_available_history_days=0,
            extra_collection_needed=["Collect aggTrades from 2024-03-25 through 2026-05-05 and validate day completeness."],
            compatible_timeframes=["1m", "5m", "15m", "1h", "4h_after_resample"],
            suitable_for_future_features=True,
            suitable_for_future_dataset=True,
            suitable_for_future_ml=True,
            suitable_for_future_walk_forward=True,
            recommendation_status="priority_1_collection_plan",
        ),
        target_window_v9_17(
            window_name="v9_historical_with_added_funding",
            desired_start="2023-03-25T00:00:00Z",
            desired_end="2024-03-24T23:59:59Z",
            included_sources=["OHLCV", "aggTrades", "funding_rates"],
            missing_sources=["funding rates before 2024-03-24"],
            minimum_required_history_days=366,
            currently_available_history_days=0,
            extra_collection_needed=["Prove and collect historical funding covering the V9 window."],
            compatible_timeframes=["1m", "5m", "15m", "1h", "4h_after_asof_join"],
            suitable_for_future_features=True,
            suitable_for_future_dataset=True,
            suitable_for_future_ml=True,
            suitable_for_future_walk_forward=False,
            recommendation_status="priority_2_collection_plan",
        ),
        target_window_v9_17(
            window_name="funding_open_interest_recent",
            desired_start="2026-04-02T08:00:00Z",
            desired_end="2026-05-05T12:00:00Z",
            included_sources=["OHLCV", "funding_rates", "open_interest"],
            missing_sources=["aggTrades for recent window if OHLCV+trades is required"],
            minimum_required_history_days=366,
            currently_available_history_days=34,
            extra_collection_needed=["Much longer OI history and recent aggTrades would be required."],
            compatible_timeframes=["4h_only_for_smoke_quality"],
            suitable_for_future_features=False,
            suitable_for_future_dataset=False,
            suitable_for_future_ml=False,
            suitable_for_future_walk_forward=False,
            recommendation_status="reject_too_short",
        ),
        target_window_v9_17(
            window_name="derivatives_native_4h",
            desired_start="2024-05-05T00:00:00Z",
            desired_end="2026-05-05T00:00:00Z",
            included_sources=["derivatives_ohlcv_futures_klines_4h", "funding_rates", "open_interest_optional"],
            missing_sources=["validated OI history, explicit derivatives-native labels, optional aggTrades if required"],
            minimum_required_history_days=366,
            currently_available_history_days=731,
            extra_collection_needed=["Validate futures 4h raw archive and choose whether OI remains optional."],
            compatible_timeframes=["4h"],
            suitable_for_future_features=True,
            suitable_for_future_dataset=True,
            suitable_for_future_ml=True,
            suitable_for_future_walk_forward=False,
            recommendation_status="priority_2_collection_plan",
        ),
    ]


def target_window_v9_17(**kwargs: Any) -> dict[str, Any]:
    return dict(kwargs)


def build_future_collection_plan_v9_17(source_candidates: list[dict[str, Any]], target_windows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "collection_order": [
            "1. Freeze a public read-only no-key collection spec and expected manifests.",
            "2. Extend aggTrades/public trades after 2024-03-24 through at least 2026-05-05.",
            "3. Validate existing funding rates and attempt historical funding only through public no-key sources.",
            "4. Add open interest only after funding + aggTrades coverage is coherent.",
            "5. Evaluate a derivatives-native 4h branch only if the spot+trades+funding branch remains blocked.",
        ],
        "priority_sources": [item["source_name"] for item in source_candidates if item["integration_priority"] == "priority_1"],
        "priority_windows": [item["window_name"] for item in target_windows if item["recommendation_status"] == "priority_1_collection_plan"],
        "pre_execution_requirements": [
            "External audit must approve the collection plan before any network collection.",
            "Every future command must be explicit, public, read-only and runnable without secrets.",
            "No private endpoint, no exchange authentication and no order-capable client.",
        ],
        "success_criteria_before_feature_store": [
            "All target days/months present with documented gaps only.",
            "Raw checksums and manifests created for source files, without ZIP sidecars.",
            "Silver rows have strict schema and UTC timestamps.",
            "available_ts is present and never after future decision alignment.",
            "Coverage overlap is long enough for future train/validation/test research.",
        ],
    }


def build_storage_plan_v9_17() -> dict[str, Any]:
    return {
        "bronze_raw": {
            "purpose": "Immutable public source files only.",
            "partitioning": ["source", "market_type", "symbol", "dataset", "date_or_month"],
            "forbidden": ["secrets", "private_api_payloads", "orders", "execution_payloads"],
        },
        "silver_normalized": {
            "purpose": "Strict schema normalized rows with causal timestamps.",
            "required_timestamps": ["event_ts", "close_ts_if_applicable", "source_publish_ts_if_applicable", "ingest_ts", "available_ts"],
            "partitioning": ["source", "market_type", "symbol", "timeframe_or_frequency", "window"],
        },
        "research_candidate": {
            "purpose": "Future audited feature candidates only after coverage validation.",
            "rule": "No supervised dataset, ML, walk-forward or backtest in the collection step.",
        },
    }


def build_quality_validation_plan_v9_17() -> list[dict[str, Any]]:
    checks = [
        ("coverage", "Verify start/end, expected partitions and documented gaps."),
        ("duplicates", "Reject duplicate natural keys per source and timestamp."),
        ("timezone", "Require UTC normalized timestamps."),
        ("frequency", "Check expected cadence or event ordering by source."),
        ("monotonicity", "Require monotonic event_ts/close_ts within each partition."),
        ("schema", "Reject extra forbidden fields such as prediction, signal, order or trading payloads."),
        ("checksums_manifests", "Persist source manifests/checksums for data files; do not create ZIP sidecars."),
        ("quarantine", "Move invalid or partial partitions to a quarantine status before downstream use."),
    ]
    return [{"check_name": name, "requirement": requirement} for name, requirement in checks]


def build_anti_leakage_plan_v9_17() -> dict[str, Any]:
    return {
        "timestamp_rules": [
            "Every future row must preserve event_ts and available_ts.",
            "Funding/OI rows must use source_publish_ts where available; otherwise a conservative available_ts policy is required.",
            "Feature alignment must use available_ts <= decision_ts.",
            "No future labels, predictions, scores or strategy outputs may enter source features.",
        ],
        "forbidden_outputs": ["prediction", "model_score", "signal", "trading_signal", "order", "backtest", "position_size", "strategy"],
        "future_collection_boundary": "Collection may create raw/silver data only after separate approval; it must not create a trading workflow.",
    }


def decide_v9_17(source_candidates: list[dict[str, Any]], target_windows: list[dict[str, Any]]) -> dict[str, Any]:
    priority_windows = {item["window_name"]: item for item in target_windows if item["recommendation_status"] == "priority_1_collection_plan"}
    if "funding_first_post_v9" in priority_windows:
        decision = "collection_plan_priority_aggtrades_post_v9_and_funding"
        recommendation = "V9.18 - AggTrades Post-V9 Collection Pack."
        confidence = "high"
        justification = "OHLCV already extends beyond funding and funding is local after 2024-05-05; the missing practical blocker is validated aggTrades after 2024-03-24."
    else:
        decision = "collection_plan_not_ready_need_manual_source_research"
        recommendation = "V9.18 - Manual Source Research Pack."
        confidence = "medium"
        justification = "No priority collection window is sufficiently concrete without source research."
    return {
        "decision": decision,
        "confidence": confidence,
        "justification": justification,
        "next_recommendation": recommendation,
        "no_backtest": True,
        "no_walk_forward": True,
        "no_trading": True,
        "collection_executed": False,
    }


def build_manifest_v9_17(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": report["status"],
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "v9_17_decision": report["v9_17_decision"],
        "source_collection_candidates_count": len(report["source_collection_candidates"]),
        "candidate_target_windows_count": len(report["candidate_target_windows"]),
        "collection_executed": report["collection_executed"],
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


def build_markdown_v9_17(report: dict[str, Any]) -> str:
    gap = report["current_data_gap_summary"]
    decision = report["v9_17_decision"]
    windows = {item["window_name"]: item for item in report["candidate_target_windows"]}
    lines = [
        "# V9.17 - Derivatives History Collection Plan",
        "",
        "## Resume executif",
        f"- Decision V9.17 : `{decision['decision']}`.",
        f"- Justification : {decision['justification']}",
        f"- Recommandation suivante : {decision['next_recommendation']}",
        "- V9.17 produit uniquement un plan de collecte historique; aucune collecte n'est executee.",
        "- Aucun feature store full, dataset, ML, walk-forward, backtest, strategie ou signal actionnable.",
        "",
        "## Gap actuel",
        f"- OHLCV local : `{gap['ohlcv_window']['start']}` -> `{gap['ohlcv_window']['end']}`.",
        f"- aggTrades valides : `{gap['aggtrades_window']['start']}` -> `{gap['aggtrades_window']['end']}`.",
        f"- Funding local : `{gap['funding_window']['start']}` -> `{gap['funding_window']['end']}`.",
        f"- Open interest local : `{gap['open_interest_window']['start']}` -> `{gap['open_interest_window']['end']}`.",
        f"- Gap aggTrades vers funding : `{gap['aggtrades_to_funding_gap_days']}` jours.",
        "",
        "## Sources a collecter",
        "- Priorite 1 : aggTrades/public trades post-V9 et funding historique public si disponible.",
        "- Priorite 2 : open interest historique et branche derivatives-native 4h.",
        "- Plus tard : liquidations et long/short ratios uniquement si public no-key et historises proprement.",
        "",
        "## Fenetres cibles",
        f"- Funding-first post-V9 : `{windows['funding_first_post_v9']['recommendation_status']}`.",
        f"- V9 historical with added funding : `{windows['v9_historical_with_added_funding']['recommendation_status']}`.",
        f"- Funding + OI recent : `{windows['funding_open_interest_recent']['recommendation_status']}`.",
        f"- Derivatives-native 4h : `{windows['derivatives_native_4h']['recommendation_status']}`.",
        "",
        "## Plan bronze/silver/research",
        "- Bronze/raw : fichiers publics immuables, sans secret et sans endpoint prive.",
        "- Silver : schemas stricts, timestamps UTC, `event_ts`, `close_ts` si applicable, `source_publish_ts` si applicable, `ingest_ts`, `available_ts`.",
        "- Research : uniquement apres validation de couverture; aucun dataset supervise ni entrainement dans la collecte.",
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
        "- Aucun reseau, aucun telechargement et aucune ingestion executee.",
        "- Aucun sidecar et aucune empreinte ZIP.",
    ]
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_17(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_17_decision": report["v9_17_decision"]["decision"],
        "recommended_next_step": report["next_recommendation"],
        "collection_executed": False,
        "features_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "no_new_data_download": True,
        "no_ingestion_executed": True,
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
        "# Synthese courante - V9.17\n\n"
        "- Derniere version validee : `V9.16`.\n"
        "- Candidate : `V9.17`.\n"
        "- Statut : `pending_external_audit`.\n"
        "- Direction : plan de collecte historique derivatives.\n"
        f"- Decision V9.17 : `{report['v9_17_decision']['decision']}`.\n"
        f"- Recommandation : {report['next_recommendation']}\n"
        "- Aucun telechargement, aucune ingestion, aucun feature store full, dataset, ML, walk-forward, backtest, strategie ou signal actionnable.\n"
        "- Aucun trading, paper live, ordre, modele persistant, API privee ou cle API.\n"
        "- Aucun reseau, aucun sidecar et aucune empreinte ZIP.\n"
    )
    _write_text(root / "reports/PROJECT_STATE.md", summary)
    _write_text(root / "reports/current/latest_summary.md", summary)
    _write_text(root / "reports/current/latest_metrics.md", summary)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        "- Derniere version validee : V9.16.\n"
        "- Candidate : V9.17, plan de collecte historique derivatives.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun reseau, aucun telechargement, aucune ingestion, aucun sidecar et aucune empreinte ZIP.\n",
    )


def gap_between_v9_17(end: str | None, next_start: str | None) -> int | None:
    end_dt = _parse_timestamp(end)
    start_dt = _parse_timestamp(next_start)
    if end_dt is None or start_dt is None:
        return None
    if start_dt <= end_dt:
        return 0
    return (start_dt.date() - end_dt.date()).days


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
