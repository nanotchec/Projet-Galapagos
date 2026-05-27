from __future__ import annotations

from copy import deepcopy

from galapagos.research.derivatives_history_collection_plan_v9_17 import FINDINGS, SAFETY, SAFETY_FLAGS, VERSION
from galapagos.research.derivatives_history_collection_plan_v9_17_validation import (
    validate_manifest_payload_v9_17,
    validate_markdown_v9_17,
    validate_report_payload_v9_17,
    validate_source_candidates_v9_17,
    validate_target_windows_v9_17,
)


def _source(name: str, priority: str = "priority_2") -> dict:
    return {
        "source_name": name,
        "target_symbol": "BTCUSDT",
        "market_type": "derivatives",
        "desired_start": "2024-05-05T00:00:00Z",
        "desired_end": "2026-05-05T00:00:00Z",
        "desired_frequency": "provider-native",
        "public_source_candidate": "public no-key source",
        "needs_api_key": False,
        "network_required_future_collection": True,
        "expected_file_format": "json raw, parquet silver",
        "target_storage_layer": "bronze/raw then silver/research",
        "expected_partitioning": "source=<venue>/symbol=BTCUSDT/date=YYYY-MM-DD",
        "expected_causal_timestamp_fields": ["event_ts", "ingest_ts", "available_ts"],
        "quality_checks_required": ["coverage", "duplicates"],
        "leakage_risks": ["unknown publication time"],
        "integration_priority": priority,
        "recommendation": "Plan only.",
    }


def _sources() -> list[dict]:
    sources = [
        _source("aggTrades_public_trades_post_v9", "priority_1"),
        _source("funding_rates_historical", "priority_1"),
        _source("open_interest_history"),
        _source("derivatives_ohlcv_futures_klines_4h"),
        _source("liquidations_long_short_ratios", "later"),
    ]
    sources[0]["market_type"] = "spot"
    return sources


def _window(name: str, status: str, future_walk_forward: bool = False) -> dict:
    return {
        "window_name": name,
        "desired_start": "2024-05-05T00:00:00Z",
        "desired_end": "2026-05-05T00:00:00Z",
        "included_sources": ["OHLCV", "funding_rates"],
        "missing_sources": ["aggTrades post-2024-03-24"],
        "minimum_required_history_days": 366,
        "currently_available_history_days": 0,
        "extra_collection_needed": ["Collect missing public history."],
        "compatible_timeframes": ["1m", "5m", "15m", "1h"],
        "suitable_for_future_features": status != "reject_too_short",
        "suitable_for_future_dataset": status != "reject_too_short",
        "suitable_for_future_ml": status != "reject_too_short",
        "suitable_for_future_walk_forward": future_walk_forward,
        "recommendation_status": status,
    }


def _windows() -> list[dict]:
    return [
        _window("funding_first_post_v9", "priority_1_collection_plan", True),
        _window("v9_historical_with_added_funding", "priority_2_collection_plan"),
        _window("funding_open_interest_recent", "reject_too_short"),
        _window("derivatives_native_4h", "priority_2_collection_plan"),
    ]


def _report() -> dict:
    return {
        "version": VERSION,
        "source_version": "V9.16",
        "status": "PASS",
        "current_data_gap_summary": {"collection_needed_before_feature_candidate": True},
        "source_collection_candidates": _sources(),
        "candidate_target_windows": _windows(),
        "future_collection_plan": {"collection_order": ["Plan only."]},
        "storage_plan": {"bronze_raw": {"purpose": "raw"}, "silver_normalized": {"purpose": "silver"}},
        "quality_validation_plan": [{"check_name": "coverage", "requirement": "Verify coverage."}],
        "anti_leakage_plan": {"timestamp_rules": ["available_ts <= decision_ts"]},
        "v9_17_decision": {
            "decision": "collection_plan_priority_aggtrades_post_v9_and_funding",
            "collection_executed": False,
            "next_recommendation": "V9.18 - AggTrades Post-V9 Collection Pack.",
        },
        "collection_executed": False,
        "features_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "findings": dict(FINDINGS),
        "safety": dict(SAFETY),
        "safety_flags": dict(SAFETY_FLAGS),
    }


def test_validator_accepts_valid_v9_17_report() -> None:
    assert validate_report_payload_v9_17(_report()) == []


def test_validator_rejects_missing_aggtrades_candidate_v9_17() -> None:
    report = _report()
    report["source_collection_candidates"] = [item for item in report["source_collection_candidates"] if item["source_name"] != "aggTrades_public_trades_post_v9"]

    errors = validate_report_payload_v9_17(report)

    assert any("source candidate missing" in error for error in errors)


def test_validator_rejects_api_key_requirement_v9_17() -> None:
    candidates = _sources()
    candidates[1]["needs_api_key"] = True

    errors = validate_source_candidates_v9_17(candidates)

    assert any("must not require API key" in error for error in errors)


def test_validator_rejects_missing_available_timestamp_v9_17() -> None:
    candidates = _sources()
    candidates[2]["expected_causal_timestamp_fields"] = ["event_ts", "ingest_ts"]

    errors = validate_source_candidates_v9_17(candidates)

    assert any("missing available_ts" in error for error in errors)


def test_validator_rejects_recent_funding_oi_window_as_candidate_v9_17() -> None:
    windows = _windows()
    windows[2]["recommendation_status"] = "priority_2_collection_plan"

    errors = validate_target_windows_v9_17(windows)

    assert "V9.17 recent funding+OI window must be rejected as too short" in errors


def test_validator_rejects_collection_execution_true_v9_17() -> None:
    report = _report()
    report["collection_executed"] = True

    errors = validate_report_payload_v9_17(report)

    assert "V9.17 must not execute collection" in errors


def test_validator_rejects_network_used_true_v9_17() -> None:
    report = _report()
    report["safety_flags"]["network_used"] = True

    errors = validate_report_payload_v9_17(report)

    assert "V9.17 safety flag mismatch: network_used" in errors


def test_validator_rejects_manifest_sidecar_field_v9_17() -> None:
    report = _report()
    manifest = deepcopy(report)
    manifest.update(
        {
            "source_collection_candidates_count": 5,
            "candidate_target_windows_count": 4,
            "sidecar_json": "forbidden",
        }
    )

    errors = validate_manifest_payload_v9_17(manifest, report)

    assert "V9.17 manifest must not contain sidecar or ZIP hash fields" in errors


def test_validator_rejects_markdown_forbidden_claim_v9_17() -> None:
    text = "aggTrades funding open interest bronze silver research aucun backtest aucun trading aucun ordre aucune strategie aucun signal actionnable aucun walk-forward aucun reseau aucun telechargement aucune ingestion tradable edge confirmed"

    errors = validate_markdown_v9_17(text)

    assert any("forbidden claim" in error for error in errors)


def test_validator_rejects_markdown_forbidden_metric_v9_17() -> None:
    text = "aggTrades funding open interest bronze silver research aucun backtest aucun trading aucun ordre aucune strategie aucun signal actionnable aucun walk-forward aucun reseau aucun telechargement aucune ingestion Sharpe"

    errors = validate_markdown_v9_17(text)

    assert any("forbidden metric term" in error for error in errors)
