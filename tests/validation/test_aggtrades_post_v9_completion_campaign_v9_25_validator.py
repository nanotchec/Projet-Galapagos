from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from galapagos.data.aggtrades_post_v9_completion_campaign_v9_25 import (
    BASE_SAFETY_FLAGS,
    FINDINGS,
    SILVER_COLUMNS_V9_18,
    VERSION,
)
from galapagos.data.aggtrades_post_v9_completion_campaign_v9_25_validation import (
    validate_campaign_summary_v9_25,
    validate_manifest_payload_v9_25,
    validate_markdown_v9_25,
    validate_report_payload_v9_25,
    validate_source_design_v9_25,
)


def _source_design() -> dict:
    return {
        "source_name": "Binance public archive aggTrades daily files",
        "host": "data.binance.vision",
        "allowed_public_hosts": ["data.binance.vision"],
        "venue": "binance",
        "market_type": "spot",
        "symbol": "BTCUSDT",
        "account_required": False,
        "api_key_required": False,
        "private_endpoint_required": False,
        "exchange_auth_required": False,
        "websocket_live_required": False,
        "download_url_template": "https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-YYYY-MM-DD.zip",
        "expected_silver_columns": list(SILVER_COLUMNS_V9_18),
    }


def _summary() -> dict:
    return {
        "campaign_start": "2024-12-08",
        "campaign_end": "2026-05-05",
        "target_window_start": "2024-05-05",
        "target_window_end": "2026-05-05",
        "previous_coverage_start": "2024-05-05",
        "previous_coverage_end": "2024-12-07",
        "final_coverage_start": "2024-05-05",
        "final_coverage_end": "2026-05-05",
        "batches_planned": 6,
        "batches_executed": 6,
        "batches_complete": 6,
        "batches_failed": 0,
        "failed_batch_ids": [],
        "days_requested_total": 514,
        "days_attempted_total": 514,
        "days_downloaded_total": 514,
        "days_normalized_total": 514,
        "days_complete_total": 514,
        "days_failed_total": 0,
        "days_quarantined_total": 0,
        "days_skipped_existing_total": 0,
        "total_rows_new": 1000,
        "total_rows_cumulative": 2000,
        "raw_bytes_new": 3000,
        "silver_bytes_new": 4000,
        "raw_bytes_cumulative": 5000,
        "silver_bytes_cumulative": 6000,
        "runtime_seconds_total": 12.0,
        "average_rows_per_day": 1,
        "average_raw_bytes_per_day": 2,
        "aggregate_trade_id_gap_warnings": [],
        "timestamp_gap_warnings": [],
        "local_file_coverage_start": "2024-05-05",
        "local_file_coverage_end": "2026-05-05",
        "reported_cumulative_coverage_start": "2024-05-05",
        "reported_cumulative_coverage_end": "2026-05-05",
        "complete_collection_reached": True,
        "future_full_coverage_complete": True,
        "quality_status": "PASS",
        "coverage_status": "target_window_complete",
        "restartability_status": "resumable_campaign_skips_existing_complete_days_and_stops_on_first_failed_batch",
        "storage_warning": "free_disk_between_60gb_and_100gb_continue_with_warning",
        "stop_reason": None,
    }


def _report(batch_paths: list[str]) -> dict:
    flags = dict(BASE_SAFETY_FLAGS)
    flags.update(
        {
            "network_used": True,
            "new_data_downloaded": True,
            "ingestion_executed": True,
            "no_new_data_download": False,
            "no_ingestion_executed": False,
            "network_scope": "public_archive_read_only",
            "new_data_download_scope": "public_historical_aggtrades_remaining_window_only",
            "ingestion_scope": "public_aggtrades_bronze_silver_completion_campaign_only",
        }
    )
    summary = _summary()
    return {
        "version": VERSION,
        "source_version": "V9.24",
        "status": "PASS",
        "direction": "aggtrades_post_v9_remaining_window_completion_campaign",
        "campaign_summary": summary,
        **summary,
        "source_public_target": _source_design(),
        "batch_report_paths": batch_paths,
        "reported_cumulative_coverage": {
            "reported_cumulative_coverage_start": "2024-05-05",
            "reported_cumulative_coverage_end": "2026-05-05",
        },
        "local_file_coverage": {
            "local_file_coverage_start": "2024-05-05",
            "local_file_coverage_end": "2026-05-05",
        },
        "anti_leakage_plan": {"rules": ["available_ts >= event_ts"]},
        "silver_schema_columns": list(SILVER_COLUMNS_V9_18),
        "decision": "aggtrades_post_v9_remaining_window_collection_complete",
        "v9_25_decision": {
            "decision": "aggtrades_post_v9_remaining_window_collection_complete",
            "next_recommendation": "V9.26 - AggTrades Full Coverage Validation.",
            "complete_collection_reached": True,
        },
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "collection_executed": True,
        "network_used": True,
        "new_data_downloaded": True,
        "ingestion_executed": True,
        "findings": dict(FINDINGS),
        "safety_flags": flags,
    }


def test_validator_accepts_complete_campaign_report_v9_25(tmp_path: Path) -> None:
    batch_paths = []
    for index in range(1, 7):
        path = tmp_path / f"reports/data/aggtrades_post_v9_completion_batch{index:02d}_v9_25.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
        batch_paths.append(path.relative_to(tmp_path).as_posix())

    assert validate_report_payload_v9_25(_report(batch_paths), tmp_path) == []


def test_validator_rejects_private_source_host_v9_25() -> None:
    source = _source_design()
    source["host"] = "api.binance.com"

    errors = validate_source_design_v9_25(source)

    assert "V9.25 source host must be data.binance.vision" in errors


def test_validator_rejects_complete_collection_without_target_coverage_v9_25(tmp_path: Path) -> None:
    report = _report([])
    report["campaign_summary"]["local_file_coverage_end"] = "2026-05-04"

    errors = validate_campaign_summary_v9_25(report, tmp_path)

    assert "V9.25 complete collection must match local target coverage" in errors


def test_validator_rejects_feature_creation_v9_25(tmp_path: Path) -> None:
    report = _report([])
    report["features_created"] = True

    errors = validate_report_payload_v9_25(report, tmp_path)

    assert "V9.25 must keep features_created=false" in errors


def test_validator_rejects_wrong_download_scope_v9_25(tmp_path: Path) -> None:
    report = _report([])
    report["safety_flags"]["new_data_download_scope"] = "full_exchange"

    errors = validate_report_payload_v9_25(report, tmp_path)

    assert "V9.25 collect must limit downloads to the remaining aggTrades window" in errors


def test_validator_rejects_manifest_sidecar_field_v9_25() -> None:
    report = _report([])
    manifest = deepcopy(report["campaign_summary"])
    manifest.update(
        {
            "version": VERSION,
            "status": "PASS",
            "decision": report["decision"],
            "findings": report["findings"],
            "safety_flags": report["safety_flags"],
            "sidecar_json": "forbidden",
        }
    )

    errors = validate_manifest_payload_v9_25(manifest, report)

    assert "V9.25 manifest must not contain sidecar or ZIP hash fields" in errors


def test_validator_rejects_markdown_forbidden_metric_v9_25() -> None:
    text = "aggTrades Binance lots internes jours couverture aucun trading aucun paper live aucun ordre aucun backtest aucun walk-forward aucune strategie aucun signal actionnable aucun modele persistant aucune api privee aucune cle api aucun client exchange authentifie aucun websocket live aucun sidecar aucune empreinte zip Sharpe"

    errors = validate_markdown_v9_25(text)

    assert any("forbidden metric term" in error for error in errors)
