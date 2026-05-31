from __future__ import annotations

import pandas as pd

from galapagos.features.ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59 import decide_v9_59, merge_feature_frames_v9_59
from galapagos.features.ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59_schemas import STRICT_COLUMNS


def _base_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source": ["binance_archive"],
            "venue": ["binance"],
            "market_type": ["spot"],
            "symbol": ["BTCUSDT"],
            "timeframe": ["1h"],
            "event_ts": pd.to_datetime(["2021-05-05T00:00:00Z"], utc=True),
            "open_ts": pd.to_datetime(["2021-05-05T00:00:00Z"], utc=True),
            "close_ts": pd.to_datetime(["2021-05-05T01:00:00Z"], utc=True),
            "decision_ts": pd.to_datetime(["2021-05-05T01:00:00Z"], utc=True),
            "available_ts": pd.to_datetime(["2021-05-05T01:00:00Z"], utc=True),
            "feature_available_ts": pd.to_datetime(["2021-05-05T01:00:00Z"], utc=True),
            "close_return_1": [0.1],
            "warmup_row": [False],
            "zero_trade_bucket": [False],
            "feature_null_count": [0],
            "feature_error_count": [0],
            "combined_feature_null_count": [0],
            "combined_feature_error_count": [0],
            "row_valid_for_combined_features": [True],
            "combined_feature_invalid_reason": [""],
        }
    )


def test_v9_59_decision_warns_when_warmup_rows_retained():
    assert decide_v9_59({"safe_to_run": True}, True, True, True, True, ["warmup"]) == "funding_common_window_feature_store_created_with_warnings"


def test_v9_59_schema_is_strict_name_list():
    assert "row_valid_for_funding_common_features" in STRICT_COLUMNS
    assert len(STRICT_COLUMNS) == len(set(STRICT_COLUMNS))
