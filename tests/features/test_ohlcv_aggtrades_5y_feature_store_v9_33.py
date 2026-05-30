from __future__ import annotations

from pathlib import Path

from galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_33 import (
    build_feature_quality_v9_33,
    build_feature_store_candidate_v9_33,
    build_ohlcv_aggtrades_5y_feature_store_v9_33,
    date_range_v9_33,
    discover_research_ohlcv_windows_v9_33,
)
from galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_33_schemas import EXPECTED_TIMEFRAMES


def test_v9_33_detects_local_ohlcv_gap_and_does_not_create_feature_store() -> None:
    report = build_ohlcv_aggtrades_5y_feature_store_v9_33(Path("."))

    assert report["version"] == "V9.33"
    assert report["aggtrades_readiness"]["aggtrades_5y_ready"] is True
    assert report["ohlcv_readiness"]["ohlcv_5y_ready"] is False
    assert report["feature_store_created"] is False
    assert report["features_created"] is False
    assert report["decision"] == "ohlcv_5y_extension_required_before_feature_store"
    assert report["network_used"] is False
    assert report["new_data_downloaded"] is False
    assert report["ingestion_executed"] is False


def test_v9_33_research_window_discovery_is_metadata_only_and_finds_expected_timeframes(tmp_path: Path) -> None:
    base = tmp_path / "data/research/v5_0/silver/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT"
    for timeframe in EXPECTED_TIMEFRAMES:
        path = base / f"timeframe={timeframe}" / "window=2023-03-25_2026-05-23" / "ohlcv.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"metadata-only-test")

    windows = discover_research_ohlcv_windows_v9_33(tmp_path)

    assert set(windows) == set(EXPECTED_TIMEFRAMES)
    for timeframe in EXPECTED_TIMEFRAMES:
        assert windows[timeframe], f"expected a known V5.0 OHLCV research window for {timeframe}"
        assert windows[timeframe][0]["start"] == "2023-03-25"
        assert windows[timeframe][0]["end"] == "2026-05-23"


def test_v9_33_not_created_quality_keeps_forbidden_scan_and_leakage_guard_explicit() -> None:
    candidate = build_feature_store_candidate_v9_33(
        {"ohlcv_5y_ready": False},
        {"aggtrades_5y_ready": True},
    )
    quality = build_feature_quality_v9_33(candidate)

    assert candidate["feature_store_created"] is False
    assert candidate["feature_store_paths"] == []
    assert quality["quality_status"] == "NOT_CREATED"
    assert quality["forbidden_column_scan"]["status"] == "PASS"
    assert quality["forbidden_column_scan"]["forbidden_columns"] == []
    assert quality["leakage_guard"]["status"] == "not_applicable_no_feature_store_created"


def test_v9_33_date_range_is_inclusive() -> None:
    assert date_range_v9_33("2021-05-05", "2021-05-07") == ["2021-05-05", "2021-05-06", "2021-05-07"]
