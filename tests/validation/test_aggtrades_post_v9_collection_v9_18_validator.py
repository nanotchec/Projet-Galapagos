from __future__ import annotations

from copy import deepcopy

from galapagos.data.aggtrades_post_v9_collection_v9_18 import BASE_SAFETY_FLAGS, FINDINGS, SILVER_COLUMNS_V9_18, VERSION
from galapagos.data.aggtrades_post_v9_collection_v9_18_validation import (
    validate_manifest_payload_v9_18,
    validate_markdown_v9_18,
    validate_report_payload_v9_18,
    validate_source_design_v9_18,
)


def _source_design() -> dict:
    return {
        "source_name": "Binance public archive aggTrades daily files",
        "host": "data.binance.vision",
        "allowed_public_hosts": ["data.binance.vision"],
        "venue": "binance",
        "market_type": "spot",
        "symbol": "BTCUSDT",
        "trade_source_type": "aggTrades",
        "account_required": False,
        "api_key_required": False,
        "private_endpoint_required": False,
        "exchange_auth_required": False,
        "websocket_live_required": False,
        "download_url_template": "https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-YYYY-MM-DD.zip",
        "bronze_raw_pattern": "data/raw/public_trades/binance_archive/spot/BTCUSDT/aggTrades/BTCUSDT-aggTrades-{date}.zip",
        "silver_normalized_pattern": "data/silver/public_trades/venue=binance/market_type=spot/symbol=BTCUSDT/date={date}/agg_trades.parquet",
        "expected_silver_columns": list(SILVER_COLUMNS_V9_18),
    }


def _report() -> dict:
    flags = dict(BASE_SAFETY_FLAGS)
    flags.update({"network_used": False, "no_new_data_download": True, "no_ingestion_executed": True})
    return {
        "version": VERSION,
        "source_version": "V9.17",
        "status": "PASS",
        "mode": "dry-run",
        "source_public_target": _source_design(),
        "target_window": {"start": "2024-03-25", "end": "2026-05-05", "days_expected": 772},
        "future_funding_first_window": {"start": "2024-05-05", "end": "2026-05-05", "days_expected": 731},
        "coverage_summary": {
            "days_expected": 772,
            "days_already_present": 0,
            "days_missing": 772,
            "days_partial": 0,
            "days_quarantined": 0,
            "coverage_complete": False,
        },
        "collection_result": {
            "days_downloaded": 0,
            "network_scope": None,
        },
        "quality_validation_plan": [{"check_name": "file_present"}],
        "anti_leakage_plan": {"rules": ["available_ts >= event_ts"]},
        "silver_schema_columns": list(SILVER_COLUMNS_V9_18),
        "v9_18_decision": {
            "decision": "aggtrades_post_v9_collection_pack_ready_dry_run_only",
            "collection_executed": False,
            "next_recommendation": "V9.19 - AggTrades Post-V9 Collection Execution.",
        },
        "collection_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": False,
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "findings": dict(FINDINGS),
        "safety_flags": flags,
    }


def test_validator_accepts_valid_dry_run_report_v9_18() -> None:
    assert validate_report_payload_v9_18(_report()) == []


def test_validator_rejects_private_source_host_v9_18() -> None:
    source = _source_design()
    source["host"] = "api.binance.com"

    errors = validate_source_design_v9_18(source)

    assert "V9.18 source host must be data.binance.vision" in errors


def test_validator_rejects_api_key_requirement_v9_18() -> None:
    report = _report()
    report["source_public_target"]["api_key_required"] = True

    errors = validate_report_payload_v9_18(report)

    assert any("api_key_required=false" in error for error in errors)


def test_validator_rejects_wrong_target_day_count_v9_18() -> None:
    report = _report()
    report["coverage_summary"]["days_expected"] = 771

    errors = validate_report_payload_v9_18(report)

    assert "V9.18 target window must contain 772 expected days" in errors


def test_validator_rejects_dry_run_network_used_v9_18() -> None:
    report = _report()
    report["network_used"] = True
    report["safety_flags"]["network_used"] = True

    errors = validate_report_payload_v9_18(report)

    assert "V9.18 dry-run must keep network_used=false" in errors
    assert "V9.18 dry-run safety flag mismatch: network_used" in errors


def test_validator_rejects_feature_creation_v9_18() -> None:
    report = _report()
    report["features_created"] = True

    errors = validate_report_payload_v9_18(report)

    assert "V9.18 must keep features_created=false" in errors


def test_validator_rejects_manifest_sidecar_field_v9_18() -> None:
    report = _report()
    manifest = deepcopy(report)
    manifest.update(
        {
            "days_expected": 772,
            "days_missing": 772,
            "collection_executed": False,
            "network_used": False,
            "api_key_used": False,
            "private_endpoint_used": False,
            "sidecar_json": "forbidden",
        }
    )

    errors = validate_manifest_payload_v9_18(manifest, report)

    assert "V9.18 manifest must not contain sidecar or ZIP hash fields" in errors


def test_validator_rejects_markdown_forbidden_claim_v9_18() -> None:
    text = "aggTrades Binance bronze silver jours attendus jours manquants aucun trading aucun paper live aucun ordre aucun backtest aucun walk-forward aucune strategie aucun signal actionnable aucune api privee aucune cle api aucun websocket live aucun sidecar aucune empreinte zip tradable edge confirmed"

    errors = validate_markdown_v9_18(text)

    assert any("forbidden claim" in error for error in errors)


def test_validator_rejects_markdown_forbidden_metric_v9_18() -> None:
    text = "aggTrades Binance bronze silver jours attendus jours manquants aucun trading aucun paper live aucun ordre aucun backtest aucun walk-forward aucune strategie aucun signal actionnable aucune api privee aucune cle api aucun websocket live aucun sidecar aucune empreinte zip Sharpe"

    errors = validate_markdown_v9_18(text)

    assert any("forbidden metric term" in error for error in errors)
