from __future__ import annotations

from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48 import _decide, _readiness


def test_v9_48_readiness_accepts_successful_v9_47_payload():
    readiness = _readiness(
        {
            "v9_47": {
                "decision": "ohlcv_aggtrades_exact_5y_feature_store_created_with_warnings",
                "quality_status": "PASS",
                "combined_feature_columns_count": 97,
            }
        }
    )

    assert readiness["ready"] is True


def test_v9_48_decision_validated_with_warnings():
    decision = _decide(
        {"ready": True, "errors": []},
        coverage_pass=True,
        schema_pass=True,
        quality_pass=True,
        leakage_pass=True,
        forbidden_pass=True,
        warnings=["warmup warning"],
        errors=[],
    )

    assert decision == "combined_feature_store_validated_with_warnings"


def test_v9_48_decision_blocks_leakage():
    decision = _decide(
        {"ready": True, "errors": []},
        coverage_pass=True,
        schema_pass=True,
        quality_pass=True,
        leakage_pass=False,
        forbidden_pass=True,
        warnings=[],
        errors=[],
    )

    assert decision == "combined_feature_store_blocked_by_leakage"
