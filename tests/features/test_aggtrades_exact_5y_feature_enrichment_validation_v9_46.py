from __future__ import annotations

import pandas as pd

from galapagos.features.aggtrades_exact_5y_feature_enrichment_v9_45_schemas import EXPECTED_ROWS_BY_TIMEFRAME, EXPECTED_TIMEFRAMES, FEATURE_COLUMNS
from galapagos.features.aggtrades_exact_5y_feature_enrichment_validation_v9_46 import (
    EXPECTED_ZERO_TRADE_BUCKETS,
    SAFETY_FLAGS,
    _bucket_summary,
    _counts_summary,
    _ratio_summary,
    _zero_trade_summary,
    decide_v9_46,
)


def test_v9_46_expected_rows_and_zero_trade_counts_match_v9_45():
    assert EXPECTED_ROWS_BY_TIMEFRAME == {"1m": 2_630_880, "5m": 526_176, "15m": 175_392, "1h": 43_848}
    assert EXPECTED_TIMEFRAMES == ("1m", "5m", "15m", "1h")
    assert len(FEATURE_COLUMNS) == 56
    assert EXPECTED_ZERO_TRADE_BUCKETS == {"1m": 542, "5m": 108, "15m": 36, "1h": 8}


def test_v9_46_decision_uses_non_blocking_warning_when_quality_passes():
    decision = decide_v9_46(
        coverage_pass=True,
        schema_pass=True,
        quality_pass=True,
        leakage_pass=True,
        forbidden_pass=True,
        zero_trade_blocking=False,
        warnings=["storage warning is non-blocking"],
    )

    assert decision == "aggtrades_exact_5y_feature_enrichment_validated_with_non_blocking_warnings"


def test_v9_46_zero_trade_bucket_validation_accepts_neutral_rows():
    frame = _sample_frame()
    summary = _zero_trade_summary(frame, "1h")

    assert summary["actual_zero_trade_buckets"] == 1
    assert summary["zero_trade_bucket_blocking"] is True
    assert any("expected 8" in error for error in summary["errors"])


def test_v9_46_feature_consistency_summaries_pass_on_valid_rows():
    frame = _sample_frame()

    assert _counts_summary(frame)["status"] == "PASS"
    assert _ratio_summary(frame)["status"] == "PASS"
    assert _bucket_summary(frame)["status"] == "PASS"


def test_v9_46_safety_flags_are_validation_only():
    assert SAFETY_FLAGS["network_used"] is False
    assert SAFETY_FLAGS["no_new_data_download"] is True
    assert SAFETY_FLAGS["no_ml"] is True
    assert SAFETY_FLAGS["no_dataset_supervised"] is True
    assert SAFETY_FLAGS["no_labels"] is True


def _sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "agg_trade_count_exact": [3, 0],
            "taker_buy_count_exact": [2, 0],
            "taker_sell_count_exact": [1, 0],
            "buyer_maker_true_count_exact": [1, 0],
            "buyer_maker_false_count_exact": [2, 0],
            "agg_trade_volume_exact": [3.0, 0.0],
            "agg_trade_quote_volume_exact": [300.0, 0.0],
            "taker_buy_base_volume_exact": [2.0, 0.0],
            "taker_sell_base_volume_exact": [1.0, 0.0],
            "taker_buy_quote_volume_exact": [200.0, 0.0],
            "taker_sell_quote_volume_exact": [100.0, 0.0],
            "taker_buy_sell_count_imbalance_exact": [1 / 3, 0.0],
            "taker_buy_sell_volume_imbalance_exact": [1 / 3, 0.0],
            "taker_buy_ratio_exact": [2 / 3, 0.0],
            "taker_sell_ratio_exact": [1 / 3, 0.0],
            "trade_size_bucket_small_count": [1, 0],
            "trade_size_bucket_medium_count": [1, 0],
            "trade_size_bucket_large_count": [1, 0],
            "trade_size_bucket_whale_count": [0, 0],
            "large_trade_count_p95_exact": [1, 0],
            "large_trade_count_p99_exact": [1, 0],
            "large_trade_volume_p95_exact": [2.0, 0.0],
            "large_trade_volume_p99_exact": [2.0, 0.0],
            "active_seconds_count": [2, 0],
            "active_seconds_ratio": [2 / 3600, 0.0],
            "agg_trade_count_per_second_mean": [1.5, 0.0],
            "agg_trade_count_per_second_max": [2.0, 0.0],
            "max_trades_in_1s": [2.0, 0.0],
            "max_volume_in_1s": [2.0, 0.0],
            "burst_count_1s_p95": [2.0, 0.0],
            "burst_volume_1s_p95": [2.0, 0.0],
            "no_trade_bucket": [0, 1],
            "aggtrades_missing_flag": [0, 0],
            "exact_feature_error_count": [0, 0],
            "row_valid_for_exact_features": [True, True],
        }
    )
