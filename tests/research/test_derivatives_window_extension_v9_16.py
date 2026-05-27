from __future__ import annotations

from pathlib import Path

from galapagos.research.derivatives_window_extension_v9_16 import (
    SAFETY_FLAGS,
    build_candidate_windows_v9_16,
    build_compatibility_analysis_v9_16,
    build_data_sources_inventory_v9_16,
    decide_v9_16,
    duration_days_v9_16,
    inspect_local_source_paths_v9_16,
    overlap_window_v9_16,
)


def _source(name: str, start: str, end: str) -> dict:
    return {
        "source_name": name,
        "coverage_start": start,
        "coverage_end": end,
    }


def _payloads() -> dict:
    return {
        "max_history_public_market_data_v5_0_manifest": {
            "discovery": {"window_start": "2023-03-25", "window_end": "2026-05-23", "missing_dates": []},
            "outputs": {"1m": {"rows": 527040}, "5m": {"rows": 105408}},
        },
        "public_trades_1y_window_v8_2_manifest": {
            "source": {"venue": "binance", "market_type": "spot", "symbol": "BTCUSDT"},
            "discovery": {"window_start": "2023-03-25", "window_end": "2024-03-24", "missing_dates": []},
            "raw_files": {"2023-03-25": {"rows": 817141}, "2023-03-26": {"rows": 786235}},
        },
        "derivatives_coverage_v1_14": {
            "ohlcv_rows": 9486,
            "ohlcv_start": "2022-01-01 00:00:00+00:00",
            "ohlcv_end": "2026-04-30 20:00:00+00:00",
            "checks": [
                {
                    "source": "binance",
                    "metric_name": "funding_rate",
                    "status": "available",
                    "rows": 2190,
                    "start_timestamp": "2024-05-05 16:00:00+00:00",
                    "end_timestamp": "2026-05-05 00:00:00+00:00",
                    "missing_rate": 0.769,
                },
                {
                    "source": "bybit",
                    "metric_name": "open_interest",
                    "status": "available",
                    "rows": 200,
                    "start_timestamp": "2026-04-02 08:00:00+00:00",
                    "end_timestamp": "2026-05-05 12:00:00+00:00",
                    "missing_rate": 0.979,
                },
                {
                    "source": "binance",
                    "metric_name": "long_short_ratio",
                    "status": "history_limited",
                    "rows": 180,
                    "start_timestamp": "2026-04-05 16:00:00+00:00",
                    "end_timestamp": "2026-05-05 12:00:00+00:00",
                },
            ],
        },
        "derivatives_data_quality_v1_14": {"missing_rates": {"funding_rate": 0.04, "open_interest": 0.91}},
        "derivatives_features_v1_14": {"columns": ["available_timestamp"], "missing_rates": {}},
        "derivatives_coverage_expansion_v1_14": {"metrics": []},
    }


def test_overlap_window_returns_zero_duration_when_trades_end_before_funding_v9_16() -> None:
    start, end = overlap_window_v9_16(
        [
            _source("OHLCV", "2023-03-25T00:00:00Z", "2026-05-23T23:59:59Z"),
            _source("trades_aggTrades", "2023-03-25T00:00:00Z", "2024-03-24T23:59:59Z"),
            _source("funding_rates", "2024-05-05T16:00:00Z", "2026-05-05T00:00:00Z"),
        ]
    )

    assert start == "2024-05-05T16:00:00Z"
    assert end == "2024-03-24T23:59:59Z"
    assert duration_days_v9_16(start, end) == 0


def test_inventory_builds_required_sources_without_repo_data_reads_v9_16(tmp_path: Path) -> None:
    inventory = build_data_sources_inventory_v9_16(tmp_path, _payloads())
    names = {item["source_name"] for item in inventory}

    assert {"OHLCV", "trades_aggTrades", "funding_rates", "open_interest", "other_derivatives_local"} <= names
    funding = next(item for item in inventory if item["source_name"] == "funding_rates")
    assert funding["coverage_start"] == "2024-05-05 16:00:00+00:00"
    assert funding["total_rows"] == 2190
    assert funding["available_ts_or_equivalent"] is True


def test_candidate_windows_reject_funding_and_open_interest_overlap_v9_16(tmp_path: Path) -> None:
    inventory = build_data_sources_inventory_v9_16(tmp_path, _payloads())
    candidates = build_candidate_windows_v9_16(inventory)
    by_name = {item["candidate_window_name"]: item for item in candidates}

    assert by_name["funding_only_with_ohlcv_trades"]["recommendation_status"] == "not_viable"
    assert by_name["funding_only_with_ohlcv_trades"]["duration_days"] == 0
    assert by_name["funding_and_open_interest_with_ohlcv_trades"]["recommendation_status"] == "not_viable"
    assert by_name["derivatives_4h_native"]["recommendation_status"] == "too_short"


def test_v9_16_decision_collects_more_history_when_no_aggtrade_funding_overlap(tmp_path: Path) -> None:
    inventory = build_data_sources_inventory_v9_16(tmp_path, _payloads())
    candidates = build_candidate_windows_v9_16(inventory)
    compatibility = build_compatibility_analysis_v9_16(candidates, inventory)
    decision = decide_v9_16(candidates, compatibility)

    assert compatibility["enough_for_future_walk_forward"] is False
    assert compatibility["funding_only_more_realistic_than_oi_plus_funding"] is True
    assert decision["decision"] == "data_extension_should_collect_more_history"
    assert "V9.17" in decision["next_recommendation"]


def test_local_source_inspection_uses_tmp_path_and_no_network_v9_16(tmp_path: Path) -> None:
    (tmp_path / "data/raw/public_trades/binance_archive/spot/BTCUSDT/aggTrades").mkdir(parents=True)
    (tmp_path / "data/raw/public_trades/binance_archive/spot/BTCUSDT/aggTrades/BTCUSDT-aggTrades-2024-01-01.zip").write_text("x", encoding="utf-8")
    inventory = inspect_local_source_paths_v9_16(tmp_path)

    assert inventory["raw_spot_agg_trades"]["files_count"] == 1
    assert SAFETY_FLAGS["network_used"] is False
    assert SAFETY_FLAGS["no_new_data_download"] is True
    assert SAFETY_FLAGS["no_walk_forward"] is True
