from __future__ import annotations

from pathlib import Path

from galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_33 import (
    build_manifest_v9_33,
    build_ohlcv_aggtrades_5y_feature_store_v9_33,
)
from galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_33_validation import (
    validate_manifest_payload_v9_33,
    validate_report_payload_v9_33,
)


def test_v9_33_validator_accepts_current_not_created_readiness_report() -> None:
    report = build_ohlcv_aggtrades_5y_feature_store_v9_33(Path("."))
    manifest = build_manifest_v9_33(report)

    assert validate_report_payload_v9_33(report) == []
    assert validate_manifest_payload_v9_33(report, manifest) == []


def test_v9_33_validator_rejects_network_or_download_flags() -> None:
    report = build_ohlcv_aggtrades_5y_feature_store_v9_33(Path("."))
    report["network_used"] = True
    report["safety_flags"]["network_used"] = True

    errors = validate_report_payload_v9_33(report)

    assert any("network_used" in error for error in errors)


def test_v9_33_validator_rejects_fake_feature_store_when_ohlcv_incomplete() -> None:
    report = build_ohlcv_aggtrades_5y_feature_store_v9_33(Path("."))
    report["feature_store_created"] = True
    report["features_created"] = True

    errors = validate_report_payload_v9_33(report)

    assert any("must not be created" in error for error in errors)


def test_v9_33_validator_rejects_forbidden_feature_columns() -> None:
    report = build_ohlcv_aggtrades_5y_feature_store_v9_33(Path("."))
    report["forbidden_columns_scan"]["forbidden_columns"] = ["future_return"]

    errors = validate_report_payload_v9_33(report)

    assert any("forbidden feature columns" in error for error in errors)
