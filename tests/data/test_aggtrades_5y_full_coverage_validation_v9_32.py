from __future__ import annotations

import ast
import json
from pathlib import Path

from galapagos.data.aggtrades_5y_full_coverage_validation_v9_32 import (
    SAFETY_FLAGS_V9_32,
    TARGET_5Y_WINDOW_END,
    TARGET_5Y_WINDOW_START,
    TOTAL_DAYS_EXPECTED_5Y,
    build_manifest_v9_32,
    date_range_v9_32,
    decide_v9_32,
    load_v9_31_batch_summaries_v9_32,
    reconcile_v9_31_counters_v9_32,
)


def test_v9_32_target_window_has_expected_5y_day_count() -> None:
    dates = date_range_v9_32(TARGET_5Y_WINDOW_START, TARGET_5Y_WINDOW_END)

    assert len(dates) == TOTAL_DAYS_EXPECTED_5Y
    assert dates[0] == "2021-05-05"
    assert dates[-1] == "2026-05-05"


def test_v9_32_decision_accepts_non_blocking_reporting_warning() -> None:
    decision = decide_v9_32(
        {"complete_calendar_coverage": True},
        {"quality_status": "PASS", "aggregate_trade_id_gap_warnings": [], "timestamp_gap_warnings": []},
        {"quarantine_blocking": False, "quarantine_stale_count": 0},
        {"reporting_inconsistency_detected": True},
        {"outlier_count": 0},
    )

    assert decision["decision"] == "aggtrades_5y_full_coverage_validated_with_non_blocking_warnings"
    assert decision["next_recommendation"] == "V9.33 - OHLCV + AggTrades 5Y Feature Store"


def test_v9_32_decision_blocks_missing_calendar_coverage() -> None:
    decision = decide_v9_32(
        {"complete_calendar_coverage": False},
        {"quality_status": "PASS", "aggregate_trade_id_gap_warnings": [], "timestamp_gap_warnings": []},
        {"quarantine_blocking": False, "quarantine_stale_count": 0},
        {"reporting_inconsistency_detected": False},
        {"outlier_count": 0},
    )

    assert decision["decision"] == "aggtrades_5y_full_coverage_blocked_by_missing_days"


def test_v9_32_reconciles_v9_31_counter_ambiguity_with_tmp_path(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports" / "data"
    report_dir.mkdir(parents=True)
    (report_dir / "aggtrades_5y_extension_batch01_v9_31.json").write_text(
        json.dumps(
            {
                "batch_summary": {
                    "batch_id": "V9.31_batch_01",
                    "batch_start": "2021-05-05",
                    "batch_end": "2021-05-06",
                    "days_downloaded": 0,
                    "days_normalized": 2,
                    "days_skipped_existing": 0,
                    "days_already_complete_before": 0,
                    "days_complete": 2,
                }
            }
        ),
        encoding="utf-8",
    )
    day_results = [{"date": "2021-05-05", "status": "day_complete"}, {"date": "2021-05-06", "status": "day_complete"}]
    inputs = {"v9_31_report": {"payload": {"days_downloaded": 0, "days_normalized": 2, "days_skipped_existing": 0, "days_complete": 2}}}

    reconciliation = reconcile_v9_31_counters_v9_32(tmp_path, inputs, day_results)

    assert reconciliation["days_downloaded_canonical"] == 0
    assert reconciliation["days_normalized_canonical"] == 2
    assert reconciliation["reporting_inconsistency_detected"] is True
    assert reconciliation["reporting_inconsistency_blocking"] is False
    assert reconciliation["batches_with_downloaded_zero_but_normalized_positive"][0]["batch_id"] == "V9.31_batch_01"


def test_v9_32_batch_summary_loader_uses_only_reports_data(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports" / "data"
    report_dir.mkdir(parents=True)
    (report_dir / "aggtrades_5y_extension_batch01_v9_31.json").write_text(
        json.dumps({"batch_summary": {"batch_id": "V9.31_batch_01", "days_downloaded": 1}}),
        encoding="utf-8",
    )

    summaries = load_v9_31_batch_summaries_v9_32(tmp_path)

    assert summaries == [{"batch_id": "V9.31_batch_01", "days_downloaded": 1}]


def test_v9_32_manifest_preserves_core_fields() -> None:
    report = {
        "status": "PASS",
        "decision": "aggtrades_5y_full_coverage_validated",
        "next_recommendation": "V9.33 - OHLCV + AggTrades 5Y Feature Store",
        "days_expected_5y": TOTAL_DAYS_EXPECTED_5Y,
        "days_complete": TOTAL_DAYS_EXPECTED_5Y,
        "days_missing": 0,
        "days_failed": 0,
        "global_duplicate_count": 0,
        "global_invalid_rows": 0,
        "quarantine_active_count": 0,
        "quarantine_stale_count": 0,
        "complete_collection_reached": True,
        "future_full_coverage_complete": True,
        "reporting_inconsistency_detected": False,
        "reporting_inconsistency_blocking": False,
        "findings": {},
        "safety_flags": dict(SAFETY_FLAGS_V9_32),
    }

    manifest = build_manifest_v9_32(report)

    assert manifest["version"] == "V9.32"
    assert manifest["days_expected_5y"] == TOTAL_DAYS_EXPECTED_5Y
    assert manifest["safety_flags"]["network_used"] is False


def test_v9_32_tests_do_not_use_placeholder_bodies() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert not any(isinstance(node, ast.Pass) for node in ast.walk(tree))
    assert ("assert" + " True") not in source
    assert ("or" + " True") not in source
