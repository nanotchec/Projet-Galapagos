from __future__ import annotations

from copy import deepcopy

from galapagos.data.aggtrades_post_v9_batch3_collection_v9_24 import (
    BASE_SAFETY_FLAGS,
    FINDINGS,
    SILVER_COLUMNS_V9_18,
    VERSION,
)
from galapagos.data.aggtrades_post_v9_batch3_collection_v9_24_validation import (
    validate_manifest_payload_v9_24,
    validate_markdown_v9_24,
    validate_batch_scope_v9_24,
    validate_report_payload_v9_24,
    validate_source_design_v9_24,
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
        "expected_silver_columns": list(SILVER_COLUMNS_V9_18),
    }


def _report() -> dict:
    flags = dict(BASE_SAFETY_FLAGS)
    flags.update(
        {
            "network_used": True,
            "new_data_downloaded": True,
            "ingestion_executed": True,
            "no_new_data_download": False,
            "no_ingestion_executed": False,
            "network_scope": "public_archive_read_only",
            "new_data_download_scope": "public_historical_aggtrades_batch3_only",
            "ingestion_scope": "public_aggtrades_bronze_silver_batch3_only",
        }
    )
    summary = {
        "days_requested": 60,
        "days_attempted": 60,
        "days_downloaded": 60,
        "days_normalized": 60,
        "days_skipped_existing": 0,
        "days_complete": 60,
        "days_failed": 0,
        "days_quarantined": 0,
        "total_rows": 100,
        "invalid_rows": 0,
        "duplicates": 0,
        "min_event_ts": "2024-10-09T00:00:00Z",
        "max_event_ts": "2024-12-07T23:59:59Z",
        "min_aggregate_trade_id": 1,
        "max_aggregate_trade_id": 100,
        "aggregate_trade_id_gap_warnings": [],
        "raw_bytes_total": 1000,
        "silver_bytes_total": 2000,
        "reported_cumulative_coverage_start": "2024-05-05",
        "reported_cumulative_coverage_end": "2024-12-07",
        "local_file_coverage_start": "2024-05-05",
        "local_file_coverage_end": "2024-12-07",
        "complete_collection_reached": False,
        "future_full_coverage_complete": False,
        "quality_errors": [],
    }
    return {
        "version": VERSION,
        "source_version": "V9.23",
        "status": "PASS",
        "mode": "collect",
        "source_public_target": _source_design(),
        "global_target_window": {"start": "2024-03-25", "end": "2026-05-05", "days_expected": 772, "complete_collection_reached": False},
        "future_funding_first_window": {"start": "2024-05-05", "end": "2026-05-05", "days_expected": 731, "complete_collection_reached": False},
        "batch_window": {
            "batch_id": "V9.24_batch_03",
            "start": "2024-10-09",
            "end": "2024-12-07",
            "max_downloads": 60,
            "days_requested": 60,
            "requested_dates": [],
        },
        "reported_cumulative_coverage": {
            "reported_cumulative_coverage_start": "2024-05-05",
            "reported_cumulative_coverage_end": "2024-12-07",
            "declarative_from_validated_reports": True,
        },
        "local_file_coverage": {
            "local_file_coverage_start": "2024-05-05",
            "local_file_coverage_end": "2024-12-07",
            "audit_lite_without_full_data_safe": True,
        },
        "collection_result": {
            "collection_executed": True,
            "network_used": True,
            "new_data_downloaded": True,
            "ingestion_executed": True,
            "network_scope": "public_archive_read_only",
            "days_attempted": 60,
            "days_downloaded": 60,
            "days_normalized": 60,
            "days_skipped_existing": 0,
        },
        "batch_validation": {"summary": summary, "day_results": []},
        "anti_leakage_plan": {"rules": ["available_ts >= event_ts"]},
        "silver_schema_columns": list(SILVER_COLUMNS_V9_18),
        "v9_24_decision": {
            "decision": "aggtrades_post_v9_batch3_collection_success",
            "next_recommendation": "V9.25 - AggTrades Post-V9 Batch 4 Collection.",
            "collection_executed": True,
        },
        "collection_executed": True,
        "network_used": True,
        "new_data_downloaded": True,
        "ingestion_executed": True,
        "complete_collection_reached": False,
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "findings": dict(FINDINGS),
        "safety_flags": flags,
    }


def test_validator_accepts_valid_batch_collect_report_v9_24() -> None:
    assert validate_report_payload_v9_24(_report()) == []


def test_validator_rejects_private_source_host_v9_24() -> None:
    source = _source_design()
    source["host"] = "api.binance.com"

    errors = validate_source_design_v9_24(source)

    assert "V9.24 source host must be data.binance.vision" in errors


def test_validator_rejects_collect_without_recorded_limit_v9_24() -> None:
    report = _report()
    report["batch_window"]["max_downloads"] = None

    errors = validate_batch_scope_v9_24(report)

    assert "V9.24 collect mode must record max_downloads" in errors


def test_validator_rejects_more_than_sixty_batch_days_v9_24() -> None:
    report = _report()
    report["batch_window"]["days_requested"] = 61
    report["batch_validation"]["summary"]["days_requested"] = 61

    errors = validate_batch_scope_v9_24(report)

    assert "V9.24 batch must not exceed 60 requested days" in errors


def test_validator_rejects_full_collection_claim_v9_24() -> None:
    report = _report()
    report["complete_collection_reached"] = True

    errors = validate_batch_scope_v9_24(report)

    assert "V9.24 must not mark full collection complete" in errors


def test_validator_rejects_feature_creation_v9_24() -> None:
    report = _report()
    report["features_created"] = True

    errors = validate_report_payload_v9_24(report)

    assert "V9.24 must keep features_created=false" in errors


def test_validator_rejects_wrong_download_scope_v9_24() -> None:
    report = _report()
    report["safety_flags"]["new_data_download_scope"] = "full_window"

    errors = validate_report_payload_v9_24(report)

    assert "V9.24 collect must limit download scope to public_historical_aggtrades_batch3_only" in errors


def test_validator_rejects_manifest_sidecar_field_v9_24() -> None:
    report = _report()
    manifest = deepcopy(report)
    summary = report["batch_validation"]["summary"]
    manifest.update(
        {
            "days_requested": summary["days_requested"],
            "days_attempted": summary["days_attempted"],
            "days_downloaded": summary["days_downloaded"],
            "days_normalized": summary["days_normalized"],
            "days_skipped_existing": summary["days_skipped_existing"],
            "days_complete": summary["days_complete"],
            "days_failed": summary["days_failed"],
            "days_quarantined": summary["days_quarantined"],
            "total_rows": summary["total_rows"],
            "collection_executed": True,
            "network_used": True,
            "api_key_used": False,
            "private_endpoint_used": False,
            "sidecar_json": "forbidden",
        }
    )

    errors = validate_manifest_payload_v9_24(manifest, report)

    assert "V9.24 manifest must not contain sidecar or ZIP hash fields" in errors


def test_validator_rejects_markdown_forbidden_metric_v9_24() -> None:
    text = "aggTrades Binance batch jours demandes jours valides aucun trading aucun paper live aucun ordre aucun backtest aucun walk-forward aucune strategie aucun signal actionnable aucune api privee aucune cle api aucun client exchange authentifie aucun websocket live aucun sidecar aucune empreinte zip Sharpe"

    errors = validate_markdown_v9_24(text)

    assert any("forbidden metric term" in error for error in errors)
