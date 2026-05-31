from __future__ import annotations

from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48 import FINDINGS, SAFETY_FLAGS
from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48_validation import validate_report_payload_v9_48


def test_v9_48_validator_accepts_valid_payload():
    errors = validate_report_payload_v9_48(
        {
            "version": "V9.48",
            "source_version": "V9.47",
            "decision": "combined_feature_store_validated_with_warnings",
            "combined_feature_columns_count": 97,
            "dataset_created": False,
            "labels_created": False,
            "ml_executed": False,
            "walk_forward_executed": False,
            "backtest_executed": False,
            "signal_created": False,
            "strategy_created": False,
            "network_used": False,
            "new_data_downloaded": False,
            "findings": FINDINGS,
            "safety_flags": SAFETY_FLAGS,
        }
    )

    assert errors == []


def test_v9_48_validator_rejects_network_or_ml():
    payload = {
        "version": "V9.48",
        "source_version": "V9.47",
        "decision": "combined_feature_store_validated",
        "combined_feature_columns_count": 97,
        "dataset_created": False,
        "labels_created": False,
        "ml_executed": True,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "signal_created": False,
        "strategy_created": False,
        "network_used": True,
        "new_data_downloaded": False,
        "findings": FINDINGS,
        "safety_flags": {**SAFETY_FLAGS, "network_used": True},
    }

    errors = validate_report_payload_v9_48(payload)

    assert any("ml_executed" in error for error in errors)
    assert any("network_used" in error for error in errors)
