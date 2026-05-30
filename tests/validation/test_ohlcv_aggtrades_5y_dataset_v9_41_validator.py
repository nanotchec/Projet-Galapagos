from __future__ import annotations

import json
from pathlib import Path

from galapagos.datasets.ohlcv_aggtrades_5y_dataset_v9_41_schemas import EXPECTED_ROWS, SAFETY_FLAGS, SELECTED_PRIMARY_LABEL
from galapagos.datasets.ohlcv_aggtrades_5y_dataset_v9_41_validation import validate_v9_41_report


def test_validator_accepts_complete_created_report(tmp_path: Path) -> None:
    _write_report_bundle(tmp_path, decision="ohlcv_aggtrades_5y_dataset_created_with_warnings")

    result = validate_v9_41_report(tmp_path)

    assert result["passed"] is True
    assert result["decision"] == "ohlcv_aggtrades_5y_dataset_created_with_warnings"
    assert result["dataset_created"] is True


def test_validator_rejects_network_usage(tmp_path: Path) -> None:
    report = _write_report_bundle(tmp_path, decision="ohlcv_aggtrades_5y_dataset_created")
    report["network_used"] = True
    report["safety_flags"]["network_used"] = True
    _write_json(tmp_path / "reports/datasets/ohlcv_aggtrades_5y_dataset_v9_41.json", report)

    result = validate_v9_41_report(tmp_path)

    assert result["passed"] is False
    assert any("network" in error for error in result["errors"])


def test_validator_rejects_leakage_created_report(tmp_path: Path) -> None:
    report = _write_report_bundle(tmp_path, decision="ohlcv_aggtrades_5y_dataset_created")
    report["leakage_guard"]["status"] = "FAIL"
    _write_json(tmp_path / "reports/datasets/ohlcv_aggtrades_5y_dataset_v9_41.json", report)

    result = validate_v9_41_report(tmp_path)

    assert result["passed"] is False
    assert any("leakage" in error for error in result["errors"])


def _write_report_bundle(tmp_path: Path, *, decision: str) -> dict:
    outputs = {}
    for timeframe in EXPECTED_ROWS:
        path = tmp_path / f"data/research/v9_41/datasets/{timeframe}/dataset.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"parquet-placeholder")
        outputs[timeframe] = {
            "created": True,
            "path": path.relative_to(tmp_path).as_posix(),
            "bytes": path.stat().st_size,
            "rows": EXPECTED_ROWS[timeframe],
        }
    report = {
        "version": "V9.41",
        "source_version": "V9.40",
        "target_window": {"start": "2021-05-05", "end": "2026-05-05", "days_expected": 1827},
        "timeframes": list(EXPECTED_ROWS),
        "decision": decision,
        "dataset_created": True,
        "target_name": SELECTED_PRIMARY_LABEL,
        "selected_primary_label": SELECTED_PRIMARY_LABEL,
        "row_counts": dict(EXPECTED_ROWS),
        "valid_row_counts": {timeframe: rows - 10 for timeframe, rows in EXPECTED_ROWS.items()},
        "invalid_row_counts": {timeframe: 10 for timeframe in EXPECTED_ROWS},
        "quality_status": "PASS_WITH_WARNINGS",
        "coverage_status": "target_5y_dataset_window_complete",
        "feature_readiness": {"ready": True},
        "label_readiness": {"ready": True},
        "leakage_guard": {"status": "PASS"},
        "forbidden_column_scan": {"status": "PASS"},
        "outputs": outputs,
        "network_used": False,
        "new_data_downloaded": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "signal_created": False,
        "strategy_created": False,
        "safety_flags": dict(SAFETY_FLAGS),
    }
    manifest = {
        "version": report["version"],
        "source_version": report["source_version"],
        "decision": report["decision"],
        "dataset_created": report["dataset_created"],
        "target_name": report["target_name"],
        "selected_primary_label": report["selected_primary_label"],
        "row_counts": report["row_counts"],
        "valid_row_counts": report["valid_row_counts"],
        "invalid_row_counts": report["invalid_row_counts"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "safety_flags": report["safety_flags"],
        "report_path": "reports/datasets/ohlcv_aggtrades_5y_dataset_v9_41.json",
    }
    _write_json(tmp_path / "reports/datasets/ohlcv_aggtrades_5y_dataset_v9_41.json", report)
    _write_json(tmp_path / "reports/manifests/ohlcv_aggtrades_5y_dataset_v9_41_manifest.json", manifest)
    return report


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
