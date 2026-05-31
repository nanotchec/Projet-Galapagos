from __future__ import annotations

from galapagos.features.funding_only_feature_store_validation_v9_58 import decide_v9_58, forbidden_columns_v9_58


def test_v9_58_decision_preserves_closed_window_warning():
    source_report = {"decision": "funding_only_feature_store_created_with_warnings"}

    assert decide_v9_58(source_report, True, True, True, True) == "funding_only_feature_store_validated_with_warnings"


def test_v9_58_forbidden_column_scan_detects_labels():
    assert forbidden_columns_v9_58(["funding_rate_current", "target_return"]) == ["target_return"]
