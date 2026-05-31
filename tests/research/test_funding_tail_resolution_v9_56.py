from __future__ import annotations

import pandas as pd

from galapagos.research.funding_tail_resolution_v9_56 import (
    CLOSED_WINDOW_END_TS,
    CLOSED_WINDOW_START_TS,
    decide_v9_56,
    normalize_funding_rows_v9_56,
    validate_funding_window_v9_56,
)


def test_v9_56_validates_closed_common_window_without_tail():
    source = pd.DataFrame(
        {
            "calc_time": [
                int(pd.Timestamp("2021-05-05T00:00:00.001Z").timestamp() * 1000),
                int(pd.Timestamp("2021-05-05T08:00:00Z").timestamp() * 1000),
            ],
            "last_funding_rate": [0.0001, 0.0002],
            "funding_interval_hours": [8, 8],
        }
    )
    funding = normalize_funding_rows_v9_56(source)
    quality = validate_funding_window_v9_56(
        funding,
        start_ts=CLOSED_WINDOW_START_TS,
        end_ts="2021-05-05T08:00:00Z",
        expected_end_label="unit",
    )

    assert quality["quality_status"] == "PASS"
    assert quality["missing_intervals"] == 0


def test_v9_56_prefers_closed_window_when_full_tail_missing():
    full_quality = {"quality_status": "FAIL", "errors": ["missing funding intervals"]}
    closed_quality = {"quality_status": "PASS", "window_end": CLOSED_WINDOW_END_TS}
    checks = {"monthly_tail": {"status": "unavailable"}, "rest_tail": {"status": "unavailable"}}

    assert decide_v9_56(full_quality, closed_quality, checks) == "funding_tail_unavailable_use_closed_common_window"
