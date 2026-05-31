from __future__ import annotations

from galapagos.features.ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59_schemas import SAFETY_FLAGS
from galapagos.features.ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59_validation import validate_v9_59_report


def test_v9_59_validator_requires_files(tmp_path):
    assert validate_v9_59_report(tmp_path)["passed"] is False


def test_v9_59_safety_flags_disable_network_and_ml():
    assert SAFETY_FLAGS["network_used"] is False
    assert SAFETY_FLAGS["no_new_data_download"] is True
    assert SAFETY_FLAGS["ml_executed"] is False
