from __future__ import annotations

from pathlib import Path

from galapagos.data.aggtrades_post_v9_collection_v9_18 import (
    BASE_SAFETY_FLAGS,
    build_day_plan_v9_18,
    build_local_raw_inventory_v9_18,
    build_public_archive_url_v9_18,
    date_range_v9_18,
    decide_v9_18,
    detect_storage_convention_v9_18,
    execute_collection_mode_v9_18,
    parse_date_from_raw_name_v9_18,
    raw_zip_path_for_date_v9_18,
    safety_flags_for_mode_v9_18,
    summarize_coverage_v9_18,
)


def test_target_window_has_expected_day_count_v9_18() -> None:
    target_dates = date_range_v9_18("2024-03-25", "2026-05-05")
    funding_dates = date_range_v9_18("2024-05-05", "2026-05-05")

    assert len(target_dates) == 772
    assert target_dates[0] == "2024-03-25"
    assert target_dates[-1] == "2026-05-05"
    assert len(funding_dates) == 731


def test_public_archive_url_is_binance_public_read_only_v9_18() -> None:
    url = build_public_archive_url_v9_18("2024-05-05")

    assert url == "https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-2024-05-05.zip"


def test_parse_raw_date_accepts_expected_filename_v9_18() -> None:
    assert parse_date_from_raw_name_v9_18("BTCUSDT-aggTrades-2024-03-25.zip") == "2024-03-25"
    assert parse_date_from_raw_name_v9_18("BTCUSDT-trades-2024-03-25.zip") is None
    assert parse_date_from_raw_name_v9_18("BTCUSDT-aggTrades-not-a-date.zip") is None


def test_dry_run_inventory_counts_present_and_missing_days_v9_18(tmp_path: Path) -> None:
    present_path = tmp_path / raw_zip_path_for_date_v9_18("2024-03-25")
    present_path.parent.mkdir(parents=True)
    present_path.write_bytes(b"not-read-in-dry-run")
    target_dates = date_range_v9_18("2024-03-25", "2024-03-27")
    inventory = build_local_raw_inventory_v9_18(tmp_path, target_dates)
    day_plan = build_day_plan_v9_18(tmp_path, target_dates, inventory)
    coverage = summarize_coverage_v9_18(target_dates, day_plan)

    assert inventory["files_count"] == 1
    assert inventory["present_dates"] == ["2024-03-25"]
    assert coverage["days_expected"] == 3
    assert coverage["days_already_present"] == 1
    assert coverage["days_missing"] == 2
    assert day_plan[0]["status"] == "day_present"
    assert day_plan[1]["status"] == "day_missing"


def test_storage_convention_prefers_existing_public_trades_path_v9_18(tmp_path: Path) -> None:
    (tmp_path / "data/raw/public_trades/binance_archive/spot/BTCUSDT/aggTrades").mkdir(parents=True)
    convention = detect_storage_convention_v9_18(tmp_path)

    assert convention["selected_convention"] == "existing_public_trades_convention"
    assert "data/raw/public_trades" in convention["bronze_raw_pattern"]
    assert "data/silver/public_trades" in convention["silver_normalized_pattern"]


def test_execute_dry_run_never_uses_network_or_ingestion_v9_18() -> None:
    result = execute_collection_mode_v9_18(Path("."), "dry-run", [])

    assert result["status"] == "PASS"
    assert result["collection_executed"] is False
    assert result["network_used"] is False
    assert result["new_data_downloaded"] is False
    assert result["ingestion_executed"] is False


def test_decision_for_dry_run_pack_ready_v9_18() -> None:
    coverage = {
        "coverage_complete": False,
    }
    collection_result = execute_collection_mode_v9_18(Path("."), "dry-run", [])
    decision = decide_v9_18("dry-run", collection_result, coverage)

    assert decision["decision"] == "aggtrades_post_v9_collection_pack_ready_dry_run_only"
    assert decision["collection_executed"] is False
    assert "V9.19" in decision["next_recommendation"]


def test_safety_flags_for_dry_run_confirm_no_collection_side_effects_v9_18() -> None:
    flags = safety_flags_for_mode_v9_18(False)

    assert flags["network_used"] is False
    assert flags["no_new_data_download"] is True
    assert flags["no_ingestion_executed"] is True
    assert flags["api_key_used"] is False
    assert flags["private_endpoint_used"] is False
    assert flags["exchange_auth_used"] is False
    assert flags["websocket_live_used"] is False
    assert BASE_SAFETY_FLAGS["no_backtest"] is True
