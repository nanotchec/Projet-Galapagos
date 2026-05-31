from __future__ import annotations

import pandas as pd

from galapagos.features.funding_only_feature_store_v9_57 import (
    align_funding_to_timeframe_v9_57,
    build_funding_event_features_v9_57,
    decide_v9_57,
)


def test_v9_57_builds_causal_funding_only_features():
    funding = pd.DataFrame(
        {
            "funding_time": pd.to_datetime(["2021-05-05T00:00:00Z", "2021-05-05T08:00:00Z"], utc=True),
            "available_ts": pd.to_datetime(["2021-05-05T00:00:00Z", "2021-05-05T08:00:00Z"], utc=True),
            "funding_rate": [0.0001, 0.0002],
            "funding_interval_hours": [8, 8],
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
    source_report = {
        "actual_feature_window": {"start": "2021-05-05T00:00:00Z", "end": "2021-05-05T09:00:00Z"},
        "common_window_policy": "unit",
    }

    events = build_funding_event_features_v9_57(
        funding,
        start=pd.Timestamp("2021-05-05T00:00:00Z"),
        end=pd.Timestamp("2021-05-05T09:00:00Z"),
    )
    features = align_funding_to_timeframe_v9_57(base, events, timeframe="1h", run_id="test", source_report=source_report)

    assert features.loc[0, "funding_rate_current"] == 0.0002
    assert features.loc[0, "funding_missing_flag"] == 0
    assert bool(features.loc[0, "row_valid_for_funding_features"])


def test_v9_57_decision_closed_window_warning():
    source_report = {"decision": "funding_tail_unavailable_use_closed_common_window"}

    assert decide_v9_57({"safe_to_run": True}, True, True, True, True, source_report) == "funding_only_feature_store_created_with_warnings"
