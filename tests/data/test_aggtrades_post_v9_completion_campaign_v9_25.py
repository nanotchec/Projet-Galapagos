from __future__ import annotations

import ast
import zipfile
from collections import namedtuple
from pathlib import Path

from galapagos.data import aggtrades_post_v9_completion_campaign_v9_25 as v925
from galapagos.data.aggtrades_post_v9_collection_v9_18 import raw_zip_path_for_date_v9_18, silver_path_for_date_v9_18
from galapagos.data.aggtrades_post_v9_completion_campaign_v9_25 import (
    INTERNAL_BATCHES,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    CompletionBatchSpec,
    build_global_campaign_summary_v9_25,
    build_local_file_coverage_v9_25,
    build_source_design_v9_25,
    collect_internal_batch_public_aggtrades_v9_25,
    date_range_v9_25,
    decide_v9_25,
    normalize_raw_zip_to_silver_v9_25,
    safety_flags_v9_25,
    validate_batch_spec_v9_25,
)


def test_internal_batches_cover_remaining_window_without_overlap_v9_25() -> None:
    all_dates: list[str] = []
    expected_lengths = [90, 90, 90, 90, 90, 64]

    for batch, expected_length in zip(INTERNAL_BATCHES, expected_lengths):
        batch_dates = date_range_v9_25(batch.start_date, batch.end_date)
        validate_batch_spec_v9_25(batch, batch_dates)
        all_dates.extend(batch_dates)
        assert len(batch_dates) == expected_length
        assert len(batch_dates) <= batch.max_downloads

    assert all_dates[0] == "2024-12-08"
    assert all_dates[-1] == "2026-05-05"
    assert len(all_dates) == 514
    assert len(set(all_dates)) == 514


def test_source_design_is_public_archive_without_auth_v9_25() -> None:
    source = build_source_design_v9_25()

    assert source["host"] == "data.binance.vision"
    assert source["market_type"] == "spot"
    assert source["symbol"] == "BTCUSDT"
    assert source["api_key_required"] is False
    assert source["private_endpoint_required"] is False
    assert source["exchange_auth_required"] is False
    assert source["websocket_live_required"] is False
    assert source["max_internal_downloads_per_batch"] == 90


def test_batch_spec_rejects_more_than_max_downloads_v9_25() -> None:
    batch = CompletionBatchSpec("V9.25_test", "2025-01-01", "2025-04-15", 90)
    requested_dates = date_range_v9_25(batch.start_date, batch.end_date)

    try:
        validate_batch_spec_v9_25(batch, requested_dates)
    except ValueError as exc:
        assert "exceeds max_downloads" in str(exc)
    else:
        raise AssertionError("expected max_downloads validation error")


def test_collect_internal_batch_skips_existing_complete_days_v9_25(tmp_path: Path) -> None:
    batch = CompletionBatchSpec("V9.25_test", "2024-12-08", "2024-12-09", 2)
    for day_value in date_range_v9_25(batch.start_date, batch.end_date):
        raw_path = tmp_path / raw_zip_path_for_date_v9_18(day_value)
        silver_path = tmp_path / silver_path_for_date_v9_18(day_value)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        silver_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(b"raw-present")
        silver_path.write_bytes(b"silver-present")

    result = collect_internal_batch_public_aggtrades_v9_25(tmp_path, batch, date_range_v9_25(batch.start_date, batch.end_date))

    assert result["status"] == "PASS"
    assert result["days_attempted"] == 0
    assert result["days_skipped_existing"] == 2
    assert result["network_used"] is False
    assert result["new_data_downloaded"] is False


def test_collect_internal_batch_stops_before_day_when_storage_guard_trips_v9_25(tmp_path: Path, monkeypatch) -> None:
    DiskUsage = namedtuple("DiskUsage", ["total", "used", "free"])
    monkeypatch.setattr(v925.shutil, "disk_usage", lambda _: DiskUsage(total=100, used=95, free=v925.MIN_FREE_BYTES))
    batch = CompletionBatchSpec("V9.25_test", "2025-02-01", "2025-02-01", 1)

    result = collect_internal_batch_public_aggtrades_v9_25(tmp_path, batch, ["2025-02-01"])

    assert result["status"] == "FAIL"
    assert result["failure_type"] == "storage"
    assert result["days_attempted"] == 0
    assert result["days_downloaded"] == 0
    assert "storage guard stopped collection" in result["errors"][0]


def test_normalizer_accepts_microsecond_trade_time_v9_25(tmp_path: Path) -> None:
    import pandas as pd

    raw_path = tmp_path / raw_zip_path_for_date_v9_18("2025-01-01")
    silver_path = tmp_path / silver_path_for_date_v9_18("2025-01-01")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(raw_path, "w") as archive:
        archive.writestr(
            "BTCUSDT-aggTrades-2025-01-01.csv",
            "3358804174,93576.00000000,0.00136000,4359935386,4359935386,1735689600010866,True,True\n",
        )

    normalize_raw_zip_to_silver_v9_25(raw_path, silver_path, "2025-01-01")
    frame = pd.read_parquet(silver_path)

    assert len(frame) == 1
    assert frame["event_ts"].iloc[0].startswith("2025-01-01T00:00:00.010866")
    assert frame["available_ts"].iloc[0] == "2025-01-02T00:00:00Z"
    assert bool(frame["row_valid"].iloc[0]) is True


def test_local_file_coverage_stops_at_first_gap_v9_25(tmp_path: Path) -> None:
    for day_value in ["2024-05-05", "2024-05-06"]:
        raw_path = tmp_path / raw_zip_path_for_date_v9_18(day_value)
        silver_path = tmp_path / silver_path_for_date_v9_18(day_value)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        silver_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(b"raw")
        silver_path.write_bytes(b"silver")

    coverage = build_local_file_coverage_v9_25(tmp_path, "2024-05-05", "2024-05-08")

    assert coverage["local_file_coverage_start"] == "2024-05-05"
    assert coverage["local_file_coverage_end"] == "2024-05-06"
    assert coverage["days_contiguous_complete"] == 2
    assert coverage["missing_or_incomplete_count"] == 2


def test_global_summary_complete_requires_all_batches_and_full_coverage_v9_25(tmp_path: Path) -> None:
    batch_reports = []
    for batch, day_count in zip(INTERNAL_BATCHES, [90, 90, 90, 90, 90, 64]):
        batch_reports.append(
            {
                "batch_summary": {
                    "batch_id": batch.batch_id,
                    "batch_start": batch.start_date,
                    "batch_end": batch.end_date,
                    "batch_success": True,
                    "days_requested": day_count,
                    "days_attempted": day_count,
                    "days_downloaded": day_count,
                    "days_normalized": day_count,
                    "days_complete": day_count,
                    "days_failed": 0,
                    "days_quarantined": 0,
                    "days_skipped_existing": 0,
                    "total_rows_new": day_count * 10,
                    "raw_bytes_new": day_count * 100,
                    "silver_bytes_new": day_count * 200,
                },
                "day_results": [],
            }
        )
    previous_metrics = {"rows_collected_total": 1000, "raw_bytes_collected_total": 2000, "silver_bytes_collected_total": 3000}
    preflight = {"storage_warning": "free_disk_between_60gb_and_100gb_continue_with_warning"}
    local_coverage = {"local_file_coverage_start": TARGET_WINDOW_START, "local_file_coverage_end": TARGET_WINDOW_END}

    summary = build_global_campaign_summary_v9_25(
        root=tmp_path,
        previous_metrics=previous_metrics,
        preflight=preflight,
        batch_reports=batch_reports,
        local_file_coverage=local_coverage,
        runtime_seconds_total=12.5,
        stop_reason=None,
    )
    decision = decide_v9_25(summary, {"preflight_status": "warning"}, None)

    assert summary["days_complete_total"] == 514
    assert summary["complete_collection_reached"] is True
    assert summary["future_full_coverage_complete"] is True
    assert summary["storage_warning"] == "free_disk_between_60gb_and_100gb_continue_with_warning"
    assert decision["decision"] == "aggtrades_post_v9_remaining_window_collection_complete"


def test_safety_flags_mark_public_campaign_scope_v9_25() -> None:
    flags = safety_flags_v9_25(
        {
            "days_attempted_total": 1,
            "days_downloaded_total": 1,
            "days_normalized_total": 1,
        },
        {"decision": "aggtrades_post_v9_remaining_window_collection_complete"},
    )

    assert flags["network_scope"] == "public_archive_read_only"
    assert flags["new_data_download_scope"] == "public_historical_aggtrades_remaining_window_only"
    assert flags["ingestion_scope"] == "public_aggtrades_bronze_silver_completion_campaign_only"
    assert flags["api_key_used"] is False
    assert flags["private_endpoint_used"] is False
    assert flags["exchange_auth_used"] is False
    assert flags["websocket_live_used"] is False
    assert flags["no_backtest"] is True
    assert flags["no_walk_forward"] is True


def test_v9_25_tests_do_not_use_placeholder_bodies() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    pass_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Pass)]

    assert pass_nodes == []
