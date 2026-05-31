from __future__ import annotations

import pandas as pd

from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_v9_47 import column_collision_summary_v9_47, combine_frames_v9_47, decide_v9_47
from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_v9_47_schemas import FEATURE_COLUMNS, SOURCE_AUDIT_COLUMNS_INHERITED_AS_FEATURES, STRICT_COLUMNS


def test_v9_47_combined_feature_count_is_base_plus_exact():
    assert len(FEATURE_COLUMNS) == 97
    assert len(STRICT_COLUMNS) == len(set(STRICT_COLUMNS))
    assert set(SOURCE_AUDIT_COLUMNS_INHERITED_AS_FEATURES).issubset(set(FEATURE_COLUMNS))


def test_v9_47_decision_uses_warnings_for_non_blocking_boundary_convention():
    decision = decide_v9_47(
        {"safe_to_run": True, "source_reports_ready": True},
        coverage_pass=True,
        schema_pass=True,
        quality_pass=True,
        leakage_pass=True,
        forbidden_pass=True,
        warnings=["boundary convention warning"],
        timeframe_reports={"1m": {"alignment": {"status": "PASS"}}},
    )

    assert decision == "ohlcv_aggtrades_exact_5y_feature_store_created_with_warnings"


def test_v9_47_collision_summary_has_no_feature_overwrite():
    base, exact = _sample_sources()
    summary = column_collision_summary_v9_47(base, exact)

    assert summary["silent_overwrite"] is False
    assert summary["feature_collisions"] == []
    assert "event_ts" in summary["metadata_collisions"]


def test_v9_47_combines_sources_with_expected_audit_columns():
    base, exact = _sample_sources()
    combined = combine_frames_v9_47(base, exact, timeframe="1m", run_id="test")

    assert list(combined.columns) == STRICT_COLUMNS
    assert combined.loc[0, "combined_feature_schema_version"] == "ohlcv_aggtrades_exact_5y_features_v9_47_v1"
    assert combined.loc[0, "source_base_feature_store_version"] == "V9.37"
    assert combined.loc[0, "source_exact_feature_validation_version"] == "V9.46"
    assert combined["row_valid_for_combined_features"].all()
    assert combined["combined_feature_null_count"].sum() == 0


def _sample_sources() -> tuple[pd.DataFrame, pd.DataFrame]:
    ts = pd.to_datetime(["2021-05-05T00:00:00Z", "2021-05-05T00:01:00Z"], utc=True)
    base = pd.DataFrame(
        {
            "source": "binance_archive",
            "venue": "binance",
            "market_type": "spot",
            "symbol": "BTCUSDT",
            "timeframe": "1m",
            "event_ts": ts,
            "open_ts": ts,
            "close_ts": ts + pd.Timedelta(minutes=1) - pd.Timedelta(milliseconds=1),
            "decision_ts": ts + pd.Timedelta(minutes=1) - pd.Timedelta(milliseconds=1),
            "available_ts": ts + pd.Timedelta(minutes=1) - pd.Timedelta(milliseconds=1),
            "feature_available_ts": ts + pd.Timedelta(minutes=1) - pd.Timedelta(milliseconds=1),
            "warmup_row": [1, 0],
            "zero_trade_bucket": [0, 0],
            "feature_null_count": [0, 0],
            "feature_error_count": [0, 0],
            "row_valid_for_features": [True, True],
        }
    )
    exact = pd.DataFrame(
        {
            "source": "binance_archive",
            "venue": "binance",
            "market_type": "spot",
            "symbol": "BTCUSDT",
            "timeframe": "1m",
            "event_ts": ts,
            "open_ts": ts,
            "close_ts": ts + pd.Timedelta(minutes=1),
            "decision_ts": ts + pd.Timedelta(minutes=1),
            "available_ts": ts + pd.Timedelta(minutes=1),
            "feature_available_ts": ts + pd.Timedelta(minutes=1),
            "no_trade_bucket": [0, 0],
            "exact_feature_null_count": [0, 0],
            "exact_feature_error_count": [0, 0],
            "row_valid_for_exact_features": [True, True],
        }
    )
    for column in FEATURE_COLUMNS:
        if column not in base.columns:
            base[column] = 0.0
        if column not in exact.columns:
            exact[column] = 0.0
    return base, exact
