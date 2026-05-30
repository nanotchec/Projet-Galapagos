from __future__ import annotations

from copy import deepcopy

from galapagos.labels.ohlcv_aggtrades_5y_label_factory_v9_40_validation import (
    validate_manifest_payload_v9_40,
    validate_report_payload_v9_40,
)
from galapagos.labels.ohlcv_aggtrades_5y_label_factory_v9_40_schemas import (
    EXPECTED_FEATURE_ROWS,
    LABEL_DESIGNS,
    SAFETY_FLAGS,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    TIMEFRAMES,
    VERSION,
)


def base_report() -> dict:
    return {
        "version": VERSION,
        "source_version": "V9.39",
        "target_window": {"start": TARGET_WINDOW_START, "end": TARGET_WINDOW_END, "days_expected": 1827},
        "timeframes": list(TIMEFRAMES),
        "decision": "ohlcv_aggtrades_5y_labels_created_with_warnings",
        "labels_created": True,
        "dataset_created": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "leakage_guard": {"status": "PASS"},
        "forbidden_column_scan": {"status": "PASS"},
        "row_counts": dict(EXPECTED_FEATURE_ROWS),
        "selected_primary_label": next(iter(LABEL_DESIGNS)),
        "outputs": {timeframe: {"created": True, "path": f"labels/{timeframe}.parquet", "rows": rows} for timeframe, rows in EXPECTED_FEATURE_ROWS.items()},
        "valid_label_counts": {timeframe: {next(iter(LABEL_DESIGNS)): rows - 10} for timeframe, rows in EXPECTED_FEATURE_ROWS.items()},
        "quality_status": "PASS_WITH_WARNINGS",
        "coverage_status": "target_5y_label_window_complete",
        "safety_flags": dict(SAFETY_FLAGS),
    }


def test_validator_accepts_created_label_report_payload() -> None:
    errors = validate_report_payload_v9_40(base_report())

    assert errors == []


def test_validator_rejects_supervised_dataset_creation() -> None:
    report = deepcopy(base_report())
    report["dataset_created"] = True

    errors = validate_report_payload_v9_40(report)

    assert "V9.40 must not create a supervised dataset" in errors


def test_validator_rejects_network_or_ml_execution() -> None:
    report = deepcopy(base_report())
    report["network_used"] = True
    report["ml_executed"] = True

    errors = validate_report_payload_v9_40(report)

    assert "V9.40 must report network_used=false" in errors
    assert "V9.40 must report ml_executed=false" in errors


def test_manifest_must_match_report_decision_and_flags() -> None:
    report = base_report()
    manifest = {
        "version": report["version"],
        "source_version": report["source_version"],
        "decision": "ohlcv_aggtrades_5y_labels_blocked_by_quality",
        "labels_created": report["labels_created"],
        "dataset_created": report["dataset_created"],
        "selected_primary_label": report["selected_primary_label"],
        "row_counts": report["row_counts"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "safety_flags": report["safety_flags"],
        "report_path": "reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40.json",
        "leakage_guard_status": "PASS",
    }

    errors = validate_manifest_payload_v9_40(report, manifest)

    assert "manifest mismatch for decision" in errors
