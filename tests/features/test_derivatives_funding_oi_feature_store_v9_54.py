from __future__ import annotations

import pandas as pd

from galapagos.features.derivatives_funding_oi_feature_store_v9_54 import (
    align_funding_to_timeframe_v9_54,
    build_funding_event_features_v9_54,
    decide_v9_54,
)


def test_v9_54_builds_causal_funding_features():
    funding = pd.DataFrame(
        {
            "funding_time": pd.to_datetime(["2021-05-05T00:00:00Z", "2021-05-05T08:00:00Z"], utc=True),
            "available_ts": pd.to_datetime(["2021-05-05T00:00:00Z", "2021-05-05T08:00:00Z"], utc=True),
            "funding_rate": [0.0001, 0.0002],
        }
    )
    base = pd.DataFrame(
        {
            "event_ts": pd.to_datetime(["2021-05-05T08:00:00Z"], utc=True),
            "open_ts": pd.to_datetime(["2021-05-05T08:00:00Z"], utc=True),
            "close_ts": pd.to_datetime(["2021-05-05T09:00:00Z"], utc=True),
            "decision_ts": pd.to_datetime(["2021-05-05T09:00:00Z"], utc=True),
        }
    )

    features = align_funding_to_timeframe_v9_54(base, build_funding_event_features_v9_54(funding), timeframe="1h", run_id="test")

    assert features.loc[0, "funding_rate_current"] == 0.0002
    assert features.loc[0, "funding_missing_flag"] == 0
    assert features.loc[0, "row_valid_for_derivatives_features"] is True or bool(features.loc[0, "row_valid_for_derivatives_features"])


def test_v9_54_decision_success():
    assert decide_v9_54({"safe_to_run": True}, True, True, True, True) == "derivatives_funding_feature_store_created"
