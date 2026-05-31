from __future__ import annotations

import pandas as pd

from galapagos.data.derivatives_funding_oi_collection_v9_53 import (
    decide_v9_53,
    funding_months_v9_53,
    normalize_funding_frame_v9_53,
    validate_funding_silver_v9_53,
)


def test_v9_53_months_are_inclusive():
    assert funding_months_v9_53("2021-05-05", "2021-07-01") == ["2021-05", "2021-06", "2021-07"]


def test_v9_53_normalizes_funding_rows():
    frame = pd.DataFrame(
        {
            "calc_time": [1620172800000, 1620201600000],
            "funding_interval_hours": [8, 8],
            "last_funding_rate": ["0.0001", "-0.0002"],
            "source_file": ["sample.zip", "sample.zip"],
        }
    )

    normalized = normalize_funding_frame_v9_53(frame)

    assert list(normalized["funding_rate"]) == [0.0001, -0.0002]
    assert normalized["row_valid"].all()


def test_v9_53_decision_complete_oi_not_ready():
    assert decide_v9_53([], {"quality_status": "PASS"}) == "funding_collection_complete_oi_not_ready"


def test_v9_53_quality_detects_missing_window_on_sample():
    frame = pd.DataFrame(
        {
            "calc_time": [1620172800000],
            "funding_interval_hours": [8],
            "last_funding_rate": ["0.0001"],
        }
    )

    result = validate_funding_silver_v9_53(normalize_funding_frame_v9_53(frame))

    assert result["quality_status"] == "FAIL"
    assert result["missing_intervals"] > 0
