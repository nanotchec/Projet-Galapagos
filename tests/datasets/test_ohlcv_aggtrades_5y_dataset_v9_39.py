from __future__ import annotations

import json
from pathlib import Path

from galapagos.datasets.ohlcv_aggtrades_5y_dataset_v9_39 import (
    assess_label_readiness_v9_39,
    build_dataset_readiness_report_v9_39,
    parse_window_from_path_v9_39,
)
from galapagos.datasets.ohlcv_aggtrades_5y_dataset_v9_39_schemas import LABEL_CANDIDATE_REPORTS


def test_v9_39_parses_windows_from_materialized_paths() -> None:
    start, end = parse_window_from_path_v9_39("data/research/v9_12/labels/x/window=2023-03-25_2024-03-24/labels.parquet")

    assert start == "2023-03-25"
    assert end == "2024-03-24"


def test_v9_39_label_readiness_blocks_short_historical_labels(tmp_path: Path) -> None:
    _write_feature_inputs(tmp_path)
    label_report = tmp_path / LABEL_CANDIDATE_REPORTS["horizon_event_v9_12"]
    label_report.parent.mkdir(parents=True, exist_ok=True)
    label_report.write_text(
        json.dumps(
            {
                "version": "V9.12",
                "status": "PASS",
                "window": {"window_start": "2023-03-25", "window_end": "2024-03-24", "total_days": 366},
                "target_name": "up_down_flat_volnorm_h4",
                "label_columns": ["event_ts", "decision_ts", "label_available_ts", "up_down_flat_volnorm_h4"],
                "outputs": {timeframe: {"path": f"data/research/v9_12/labels/timeframe={timeframe}/window=2023-03-25_2024-03-24/labels.parquet"} for timeframe in ["1m", "5m", "15m", "1h"]},
            }
        ),
        encoding="utf-8",
    )

    readiness = assess_label_readiness_v9_39(tmp_path)

    assert readiness["status"] == "MISSING_5Y_COMPATIBLE_LABELS"
    assert readiness["compatible_label_count"] == 0
    assert any(candidate["label_name"] == "horizon_event_v9_12" and not candidate["compatible_with_5y_window"] for candidate in readiness["candidates"])


def test_v9_39_report_does_not_create_fake_dataset_when_labels_missing(tmp_path: Path) -> None:
    _write_feature_inputs(tmp_path)

    report = build_dataset_readiness_report_v9_39(tmp_path)

    assert report["decision"] == "ohlcv_aggtrades_5y_dataset_blocked_by_missing_labels"
    assert report["dataset_created"] is False
    assert report["target_name"] is None
    assert report["dataset_paths"] == {}
    assert set(report["row_counts"].values()) == {0}
    assert report["network_used"] is False
    assert report["ml_executed"] is False
    assert report["backtest_executed"] is False


def test_v9_39_report_selects_created_decision_only_with_compatible_labels(tmp_path: Path) -> None:
    _write_feature_inputs(tmp_path)
    label_report = tmp_path / LABEL_CANDIDATE_REPORTS["max_history_v5_2"]
    label_report.parent.mkdir(parents=True, exist_ok=True)
    label_report.write_text(
        json.dumps(
            {
                "version": "VTEST",
                "status": "PASS",
                "window": {"window_start": "2021-05-05", "window_end": "2026-05-05", "total_days": 1827},
                "target_name": "test_target",
                "label_columns": ["event_ts", "decision_ts", "label_available_ts", "test_target"],
                "outputs": {timeframe: {"path": f"data/research/test/labels/timeframe={timeframe}/window=2021-05-05_2026-05-05/labels.parquet"} for timeframe in ["1m", "5m", "15m", "1h"]},
                "leakage_guard": {"label_available_ts_gt_decision_ts": True},
            }
        ),
        encoding="utf-8",
    )

    report = build_dataset_readiness_report_v9_39(tmp_path)

    assert report["label_readiness"]["status"] == "READY"
    assert report["decision"] == "ohlcv_aggtrades_5y_dataset_partial"


def test_v9_39_tests_do_not_use_placeholder_bodies() -> None:
    source = Path(__file__).read_text(encoding="utf-8")

    assert "pass\n" not in source
    assert ("assert " + "True") not in source


def _write_feature_inputs(root: Path) -> None:
    report = {
        "version": "V9.38",
        "decision": "ohlcv_aggtrades_5y_feature_store_validated_with_non_blocking_warnings",
        "quality_status": "PASS",
        "coverage_status": "target_5y_feature_window_complete",
        "schema_status": "PASS",
        "leakage_guard_status": "PASS",
        "actual_rows": {"1m": 2630880, "5m": 526176, "15m": 175392, "1h": 43848},
        "leakage_guard": {"feature_available_ts_lte_decision_ts": True},
    }
    paths = [
        "reports/features/ohlcv_aggtrades_5y_feature_store_validation_v9_38.json",
        "reports/manifests/ohlcv_aggtrades_5y_feature_store_validation_v9_38_manifest.json",
        "reports/features/ohlcv_aggtrades_5y_feature_store_v9_37.json",
        "reports/manifests/ohlcv_aggtrades_5y_feature_store_v9_37_manifest.json",
        "reports/data/ohlcv_from_aggtrades_5y_validation_v9_36.json",
        "reports/data/aggtrades_5y_full_coverage_validation_v9_32.json",
        "reports/current/latest_metrics.json",
        "reports/PROJECT_STATE.json",
    ]
    for raw in paths:
        path = root / raw
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report), encoding="utf-8")
