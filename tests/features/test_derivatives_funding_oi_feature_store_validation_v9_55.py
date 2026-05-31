from __future__ import annotations

from galapagos.features.derivatives_funding_oi_feature_store_validation_v9_55 import decide_v9_55


def test_v9_55_decision_validated_with_warnings():
    assert decide_v9_55(True, True, True, True) == "derivatives_feature_store_validated_with_warnings"


def test_v9_55_decision_blocks_leakage():
    assert decide_v9_55(True, True, True, False) == "derivatives_feature_store_blocked_by_leakage"
