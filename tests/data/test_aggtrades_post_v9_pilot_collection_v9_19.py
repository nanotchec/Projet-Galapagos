from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd
import pytest

from galapagos.data.aggtrades_post_v9_collection_v9_18 import (
    SILVER_COLUMNS_V9_18,
    raw_zip_path_for_date_v9_18,
    silver_path_for_date_v9_18,
)
from galapagos.data.aggtrades_post_v9_pilot_collection_v9_19 import (
    MAX_PILOT_DOWNLOADS,
    build_pilot_day_plan_v9_19,
    build_source_design_v9_19,
    collect_pilot_public_aggtrades_v9_19,
    date_range_v9_19,
    decide_v9_19,
    safety_flags_for_pilot_v9_19,
    summarize_pilot_validation_v9_19,
    validate_pilot_day_v9_19,
    validate_pilot_request_v9_19,
)


def test_pilot_window_is_limited_to_seven_days_v9_19() -> None:
    pilot_dates = date_range_v9_19("2024-05-05", "2024-05-11")

    assert len(pilot_dates) == MAX_PILOT_DOWNLOADS
    assert pilot_dates[0] == "2024-05-05"
    assert pilot_dates[-1] == "2024-05-11"


def test_collect_mode_requires_explicit_download_limit_v9_19() -> None:
    pilot_dates = date_range_v9_19("2024-05-05", "2024-05-11")

    with pytest.raises(ValueError, match="requires --max-downloads"):
        validate_pilot_request_v9_19("collect", pilot_dates, None)
    with pytest.raises(ValueError, match="1 <= --max-downloads <= 7"):
        validate_pilot_request_v9_19("collect", pilot_dates, 8)


def test_source_design_is_public_archive_without_auth_v9_19() -> None:
    source = build_source_design_v9_19()

    assert source["host"] == "data.binance.vision"
    assert source["market_type"] == "spot"
    assert source["symbol"] == "BTCUSDT"
    assert source["api_key_required"] is False
    assert source["private_endpoint_required"] is False
    assert source["exchange_auth_required"] is False
    assert source["websocket_live_required"] is False


def test_day_plan_detects_raw_and_silver_pilot_outputs_v9_19(tmp_path: Path) -> None:
    day_value = "2024-05-05"
    raw_path = tmp_path / raw_zip_path_for_date_v9_18(day_value)
    silver_path = tmp_path / silver_path_for_date_v9_18(day_value)
    raw_path.parent.mkdir(parents=True)
    silver_path.parent.mkdir(parents=True)
    raw_path.write_bytes(b"placeholder")
    silver_path.write_bytes(b"placeholder")

    plan = build_pilot_day_plan_v9_19(tmp_path, [day_value])

    assert plan[0]["date"] == day_value
    assert plan[0]["status"] == "day_complete"
    assert plan[0]["raw_exists"] is True
    assert plan[0]["silver_exists"] is True


def test_validate_pilot_day_accepts_small_valid_normalized_sample_v9_19(tmp_path: Path) -> None:
    day_value = "2024-05-05"
    _write_raw_zip(tmp_path, day_value)
    _write_silver_parquet(tmp_path, day_value)

    result = validate_pilot_day_v9_19(tmp_path, day_value)

    assert result["status"] == "day_complete"
    assert result["rows"] == 2
    assert result["duplicates"] == 0
    assert result["invalid_rows"] == 0
    assert result["errors"] == []


def test_validate_pilot_day_rejects_duplicate_aggregate_trade_id_v9_19(tmp_path: Path) -> None:
    day_value = "2024-05-05"
    _write_raw_zip(tmp_path, day_value)
    _write_silver_parquet(tmp_path, day_value, duplicate_id=True)

    result = validate_pilot_day_v9_19(tmp_path, day_value)

    assert result["status"] == "day_failed"
    assert any("duplicate_aggregate_trade_id" in error for error in result["errors"])


def test_decision_success_requires_complete_quality_pilot_v9_19() -> None:
    collection_result = {
        "collection_executed": True,
        "status": "PASS",
        "errors": [],
    }
    pilot_summary = {
        "quality_status": "PASS",
        "days_complete": 7,
        "days_requested": 7,
    }

    decision = decide_v9_19(collection_result, pilot_summary)

    assert decision["decision"] == "aggtrades_post_v9_pilot_collection_success"
    assert "V9.20" in decision["next_recommendation"]
    assert decision["complete_collection_reached"] is False


def test_safety_flags_for_collect_are_public_archive_only_v9_19() -> None:
    flags = safety_flags_for_pilot_v9_19(
        {
            "collection_executed": True,
            "network_used": True,
            "new_data_downloaded": True,
            "ingestion_executed": True,
        }
    )

    assert flags["network_scope"] == "public_archive_read_only"
    assert flags["new_data_download_scope"] == "public_historical_aggtrades_pilot_only"
    assert flags["ingestion_scope"] == "public_aggtrades_bronze_silver_pilot_only"
    assert flags["api_key_used"] is False
    assert flags["private_endpoint_used"] is False
    assert flags["exchange_auth_used"] is False
    assert flags["websocket_live_used"] is False
    assert flags["no_backtest"] is True


def test_collect_pilot_refuses_unbounded_execution_v9_19(tmp_path: Path) -> None:
    pilot_dates = date_range_v9_19("2024-05-05", "2024-05-11")

    with pytest.raises(ValueError, match="requires --max-downloads"):
        collect_pilot_public_aggtrades_v9_19(tmp_path, pilot_dates, max_downloads=None)


def test_pilot_summary_never_claims_full_future_coverage_v9_19() -> None:
    summary = summarize_pilot_validation_v9_19(
        ["2024-05-05"],
        [{"status": "day_missing"}],
        {"days_attempted": 1, "days_downloaded": 1, "days_normalized": 1},
        [
            {
                "date": "2024-05-05",
                "status": "day_complete",
                "raw_bytes": 100,
                "silver_bytes": 200,
                "rows": 10,
                "invalid_rows": 0,
                "duplicates": 0,
                "min_event_ts": "2024-05-05T00:00:00Z",
                "max_event_ts": "2024-05-05T23:59:59Z",
                "min_aggregate_trade_id": 1,
                "max_aggregate_trade_id": 10,
                "errors": [],
            }
        ],
        2.0,
    )

    assert summary["pilot_success"] is True
    assert summary["future_full_coverage_complete"] is False
    assert summary["estimated_full_collection_rows"] == 7720


def _write_raw_zip(root: Path, day_value: str) -> None:
    raw_path = root / raw_zip_path_for_date_v9_18(day_value)
    raw_path.parent.mkdir(parents=True)
    with zipfile.ZipFile(raw_path, "w") as archive:
        archive.writestr(f"BTCUSDT-aggTrades-{day_value}.csv", "1,100.0,0.5,1,1,1714867200000,true,true\n2,101.0,0.4,2,2,1714867201000,false,true\n")


def _write_silver_parquet(root: Path, day_value: str, *, duplicate_id: bool = False) -> None:
    silver_path = root / silver_path_for_date_v9_18(day_value)
    silver_path.parent.mkdir(parents=True)
    aggregate_ids = [1, 1 if duplicate_id else 2]
    frame = pd.DataFrame(
        {
            "source": ["binance_archive", "binance_archive"],
            "venue": ["binance", "binance"],
            "market_type": ["spot", "spot"],
            "symbol": ["BTCUSDT", "BTCUSDT"],
            "aggregate_trade_id": aggregate_ids,
            "price": [100.0, 101.0],
            "quantity": [0.5, 0.4],
            "first_trade_id": [1, 2],
            "last_trade_id": [1, 2],
            "event_ts": ["2024-05-05T00:00:00.000000Z", "2024-05-05T00:00:01.000000Z"],
            "trade_ts": ["2024-05-05T00:00:00.000000Z", "2024-05-05T00:00:01.000000Z"],
            "is_buyer_maker": [True, False],
            "ingest_ts": ["2026-05-27T00:00:00Z", "2026-05-27T00:00:00Z"],
            "available_ts": ["2024-05-06T00:00:00Z", "2024-05-06T00:00:00Z"],
            "source_file": ["sample.zip", "sample.zip"],
            "source_checksum": ["abc", "abc"],
            "row_valid": [True, True],
            "invalid_reason": ["", ""],
        }
    )
    frame[SILVER_COLUMNS_V9_18].to_parquet(silver_path, index=False)
