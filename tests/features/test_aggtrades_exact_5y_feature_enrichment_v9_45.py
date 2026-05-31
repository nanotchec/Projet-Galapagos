from __future__ import annotations

from pathlib import Path

import pandas as pd

from galapagos.features.aggtrades_exact_5y_feature_enrichment_v9_45 import build_day_timeframe_features_v9_45, build_preflight_v9_45, finalize_feature_frame_v9_45, add_rolling_features_v9_45, validate_exact_feature_frame_v9_45
from galapagos.features.aggtrades_exact_5y_feature_enrichment_v9_45_schemas import EXPECTED_DAYS, EXPECTED_ROWS_BY_TIMEFRAME, FEATURE_COLUMNS, STRICT_COLUMNS


def test_v9_45_expected_5y_row_counts_are_fixed():
    assert EXPECTED_DAYS == 1827
    assert EXPECTED_ROWS_BY_TIMEFRAME == {"1m": 2_630_880, "5m": 526_176, "15m": 175_392, "1h": 43_848}


def test_v9_45_day_builder_computes_exact_side_counts_and_volumes():
    frame = _sample_trades()
    output = build_day_timeframe_features_v9_45(frame, day=pd.Timestamp("2021-05-05").date(), timeframe="1m", run_id="test_run")
    first = output.iloc[0]

    assert list(output.columns) == STRICT_COLUMNS
    assert len(output) == 1440
    assert first["agg_trade_count_exact"] == 3
    assert first["taker_buy_count_exact"] == 2
    assert first["taker_sell_count_exact"] == 1
    assert first["buyer_maker_true_count_exact"] == 1
    assert first["buyer_maker_false_count_exact"] == 2
    assert first["agg_trade_volume_exact"] == 3.5
    assert first["taker_buy_base_volume_exact"] == 3.0
    assert first["taker_sell_base_volume_exact"] == 0.5
    assert first["no_trade_bucket"] == 0
    assert output.iloc[1]["no_trade_bucket"] == 1


def test_v9_45_rolling_features_are_past_only_on_ordered_buckets():
    frame = build_day_timeframe_features_v9_45(_sample_trades(), day=pd.Timestamp("2021-05-05").date(), timeframe="1m", run_id="test_run")
    enriched = finalize_feature_frame_v9_45(add_rolling_features_v9_45(frame))

    assert enriched["feature_available_ts"].le(enriched["decision_ts"]).all()
    assert enriched.loc[0, "rolling_exact_trade_count_mean_5"] == 3.0
    assert enriched.loc[1, "rolling_exact_trade_count_mean_5"] == 1.5
    assert enriched[list(FEATURE_COLUMNS)].isna().sum().sum() == 0


def test_v9_45_validation_allows_signed_imbalance_features():
    frame = build_day_timeframe_features_v9_45(_sample_trades(), day=pd.Timestamp("2021-05-05").date(), timeframe="1m", run_id="test_run")
    enriched = finalize_feature_frame_v9_45(add_rolling_features_v9_45(frame))

    report = validate_exact_feature_frame_v9_45(enriched, timeframe="1m", output_path=Path("features.parquet"))

    assert report["range_summary"]["negative_counts"] == 0
    assert report["range_summary"]["negative_volumes"] == 0


def test_v9_45_preflight_is_read_only_and_reports_storage(tmp_path):
    (tmp_path / "data/silver/public_trades").mkdir(parents=True)
    (tmp_path / "data/research/v9_37/features/ohlcv_aggtrades_5y").mkdir(parents=True)
    preflight = build_preflight_v9_45(tmp_path)

    assert "free_gib_data_mount" in preflight
    assert preflight["processing_strategy"] == "parallel_daily_partitioned_aggtrades_scan_then_timeframe_concat"
    assert "12 workers" in preflight["chunking_strategy"]


def _sample_trades() -> pd.DataFrame:
    event_ts = pd.to_datetime(
        [
            "2021-05-05T00:00:00.100Z",
            "2021-05-05T00:00:00.500Z",
            "2021-05-05T00:00:10.000Z",
            "2021-05-05T00:02:01.000Z",
        ],
        utc=True,
    )
    frame = pd.DataFrame(
        {
            "aggregate_trade_id": [1, 2, 3, 4],
            "price": [100.0, 101.0, 99.0, 102.0],
            "quantity": [1.0, 2.0, 0.5, 4.0],
            "event_ts": event_ts,
            "trade_ts": event_ts,
            "available_ts": event_ts,
            "is_buyer_maker": [False, False, True, True],
        }
    )
    frame["quote_quantity"] = frame["price"] * frame["quantity"]
    frame["is_taker_buy"] = ~frame["is_buyer_maker"].astype(bool)
    frame["event_second"] = frame["event_ts"].dt.floor("s")
    return frame
