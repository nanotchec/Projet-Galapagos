from __future__ import annotations

from galapagos.datasets.ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61 import SAFETY_FLAGS, VERSION
from galapagos.datasets.ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61_validation import _result


def test_v9_61_validator_result_passes_without_errors() -> None:
    result = _result([], {"decision": "funding_common_window_dataset_validated"})
    assert result["version"] == VERSION
    assert result["passed"] is True
    assert result["decision"] == "funding_common_window_dataset_validated"


def test_v9_61_safety_flags_prevent_ml_and_network() -> None:
    assert SAFETY_FLAGS["network_used"] is False
    assert SAFETY_FLAGS["ml_executed"] is False
    assert SAFETY_FLAGS["no_backtest"] is True
    assert SAFETY_FLAGS["no_walk_forward"] is True
