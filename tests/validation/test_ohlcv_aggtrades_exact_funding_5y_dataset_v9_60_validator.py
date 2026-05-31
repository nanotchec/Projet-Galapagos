from __future__ import annotations

from galapagos.datasets.ohlcv_aggtrades_exact_funding_5y_dataset_v9_60_schemas import SAFETY_FLAGS
from galapagos.datasets.ohlcv_aggtrades_exact_funding_5y_dataset_v9_60_validation import validate_v9_60_report


def test_v9_60_validator_requires_report(tmp_path):
    assert validate_v9_60_report(tmp_path)["passed"] is False


def test_v9_60_safety_flags_allow_dataset_but_no_ml_or_network():
    assert SAFETY_FLAGS["network_used"] is False
    assert SAFETY_FLAGS["ml_executed"] is False
    assert SAFETY_FLAGS["no_new_data_download"] is True
