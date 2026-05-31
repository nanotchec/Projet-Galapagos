from __future__ import annotations

import numpy as np

from galapagos.datasets.ohlcv_aggtrades_exact_funding_5y_dataset_v9_60 import decide_v9_60, split_series_v9_60
from galapagos.datasets.ohlcv_aggtrades_exact_funding_5y_dataset_v9_60_schemas import COMMON_WINDOW_LABEL, DATASET_COLUMNS


def test_v9_60_split_is_temporal_without_shuffle():
    split = split_series_v9_60(10)
    assert split.tolist() == ["train"] * 6 + ["validation"] * 2 + ["test"] * 2
    ranks = np.array([{"train": 0, "validation": 1, "test": 2}[item] for item in split])
    assert np.all(ranks[:-1] <= ranks[1:])


def test_v9_60_decision_warns_for_audit_invalid_rows():
    decision = decide_v9_60(True, {"ready": True}, {"ready": True}, {"status": "PASS"}, "PASS", ["warmup"], [])
    assert decision == "funding_common_window_dataset_created_with_warnings"


def test_v9_60_schema_contains_funding_window_and_target():
    assert "funding_rate_current" in DATASET_COLUMNS
    assert "up_down_flat_volnorm_h1_5y" in DATASET_COLUMNS
    assert COMMON_WINDOW_LABEL.endswith("T16-00-00Z")
