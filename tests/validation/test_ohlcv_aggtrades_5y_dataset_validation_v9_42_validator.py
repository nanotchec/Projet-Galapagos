from __future__ import annotations

import json
from pathlib import Path

from galapagos.datasets.ohlcv_aggtrades_5y_dataset_validation_v9_42 import SAFETY_FLAGS
from galapagos.datasets.ohlcv_aggtrades_5y_dataset_validation_v9_42_validation import validate_v9_42_report


def test_v9_42_validator_accepts_audit_lite_without_full_parquets(tmp_path: Path) -> None:
    _write_bundle(tmp_path)

    result = validate_v9_42_report(tmp_path, mode="audit-lite")

    assert result["passed"] is True
    assert result["validation_mode"] == "full-local"


def test_v9_42_validator_rejects_network_usage(tmp_path: Path) -> None:
    report = _write_bundle(tmp_path)
    report["network_used"] = True
    report["safety_flags"]["network_used"] = True
    _write_json(tmp_path / "reports/datasets/ohlcv_aggtrades_5y_dataset_validation_v9_42.json", report)

    result = validate_v9_42_report(tmp_path, mode="audit-lite")

    assert result["passed"] is False
    assert any("network" in error for error in result["errors"])


def test_v9_42_validator_requires_sample_inventory(tmp_path: Path) -> None:
    _write_bundle(tmp_path)
    _write_json(tmp_path / "reports/datasets/ohlcv_aggtrades_5y_dataset_validation_v9_42_samples.json", {"version": "V9.42", "samples": {}})

    result = validate_v9_42_report(tmp_path, mode="audit-lite")

    assert result["passed"] is False
    assert any("missing sample inventory" in error for error in result["errors"])


def _write_bundle(tmp_path: Path) -> dict:
    samples = {}
    for timeframe in ["1m", "5m", "15m", "1h"]:
        sample_path = tmp_path / f"data/audit_samples/v9_42/{timeframe}/dataset_sample.parquet"
        sample_path.parent.mkdir(parents=True, exist_ok=True)
        sample_path.write_bytes(b"small-sample")
        samples[timeframe] = {"path": sample_path.relative_to(tmp_path).as_posix(), "rows": 2, "bytes": sample_path.stat().st_size}
    report = {
        "version": "V9.42",
        "source_version": "V9.41",
        "status": "PASS",
        "validation_mode": "full-local",
        "decision": "ohlcv_aggtrades_5y_dataset_validated",
        "target_name": "up_down_flat_volnorm_h1_5y",
        "coverage_status": "target_5y_dataset_window_complete",
        "schema_status": "PASS",
        "quality_status": "PASS",
        "leakage_guard_status": "PASS",
        "leakage_guard": {"status": "PASS"},
        "forbidden_column_scan": {"status": "PASS"},
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "signal_created": False,
        "strategy_created": False,
        "network_used": False,
        "new_data_downloaded": False,
        "safety_flags": dict(SAFETY_FLAGS),
    }
    manifest = {
        "version": "V9.42",
        "source_version": "V9.41",
        "decision": report["decision"],
        "target_name": report["target_name"],
        "coverage_status": report["coverage_status"],
        "schema_status": report["schema_status"],
        "quality_status": report["quality_status"],
        "leakage_guard_status": report["leakage_guard_status"],
        "dataset_created": report["dataset_created"],
        "network_used": report["network_used"],
        "new_data_downloaded": report["new_data_downloaded"],
        "safety_flags": report["safety_flags"],
        "report_path": "reports/datasets/ohlcv_aggtrades_5y_dataset_validation_v9_42.json",
    }
    _write_json(tmp_path / "reports/datasets/ohlcv_aggtrades_5y_dataset_validation_v9_42.json", report)
    _write_json(tmp_path / "reports/manifests/ohlcv_aggtrades_5y_dataset_validation_v9_42_manifest.json", manifest)
    _write_json(tmp_path / "reports/datasets/ohlcv_aggtrades_5y_dataset_validation_v9_42_samples.json", {"version": "V9.42", "samples": samples})
    return report


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
