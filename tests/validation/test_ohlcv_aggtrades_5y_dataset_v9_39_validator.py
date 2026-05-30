from __future__ import annotations

from copy import deepcopy

from galapagos.datasets.ohlcv_aggtrades_5y_dataset_v9_39 import build_manifest_v9_39
from galapagos.datasets.ohlcv_aggtrades_5y_dataset_v9_39_validation import (
    validate_manifest_payload_v9_39,
    validate_report_payload_v9_39,
)
from galapagos.datasets.ohlcv_aggtrades_5y_dataset_v9_39_schemas import SAFETY_FLAGS


def test_v9_39_validator_accepts_missing_labels_block_payload() -> None:
    report = _report()
    manifest = build_manifest_v9_39(report)

    assert validate_report_payload_v9_39(report) == []
    assert validate_manifest_payload_v9_39(report, manifest) == []


def test_v9_39_validator_rejects_fake_dataset_for_missing_labels() -> None:
    report = _report()
    report["dataset_created"] = True

    errors = validate_report_payload_v9_39(report)

    assert any("must not create" in error for error in errors)


def test_v9_39_validator_rejects_network_usage() -> None:
    report = _report()
    report["network_used"] = True
    report["safety_flags"]["network_used"] = True

    errors = validate_report_payload_v9_39(report)

    assert any("network" in error for error in errors)


def test_v9_39_validator_rejects_ml_or_backtest() -> None:
    report = _report()
    report["ml_executed"] = True

    errors = validate_report_payload_v9_39(report)

    assert any("ML" in error for error in errors)


def test_v9_39_validator_rejects_contradictory_label_readiness() -> None:
    report = _report()
    report["label_readiness"]["candidates"][0]["compatible_with_5y_window"] = True

    errors = validate_report_payload_v9_39(report)

    assert any("contradicts" in error for error in errors)


def test_v9_39_manifest_mismatch_is_detected() -> None:
    report = _report()
    manifest = build_manifest_v9_39(report)
    manifest["dataset_created"] = True

    errors = validate_manifest_payload_v9_39(report, manifest)

    assert any("dataset_created" in error for error in errors)


def _report() -> dict:
    report = {
        "version": "V9.39",
        "source_version": "V9.38",
        "status": "PASS",
        "direction": "ohlcv_aggtrades_5y_dataset",
        "decision": "ohlcv_aggtrades_5y_dataset_blocked_by_missing_labels",
        "target_window": {"start": "2021-05-05", "end": "2026-05-05", "days_expected": 1827},
        "timeframes": ["1m", "5m", "15m", "1h"],
        "dataset_created": False,
        "dataset_paths": {},
        "target_name": None,
        "row_counts": {"1m": 0, "5m": 0, "15m": 0, "1h": 0},
        "label_distribution": {},
        "split_distribution": {},
        "label_readiness": {
            "status": "MISSING_5Y_COMPATIBLE_LABELS",
            "candidates": [
                {
                    "label_name": "horizon_event_v9_12",
                    "coverage_start": "2023-03-25",
                    "coverage_end": "2024-03-24",
                    "compatible_with_5y_window": False,
                }
            ],
        },
        "quality_status": "BLOCKED",
        "coverage_status": "feature_store_ready_labels_missing",
        "next_recommendation": "V9.40 - OHLCV + AggTrades 5Y Label Factory",
        "network_used": False,
        "new_data_downloaded": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "findings": {},
        "safety_flags": dict(SAFETY_FLAGS),
    }
    return deepcopy(report)
