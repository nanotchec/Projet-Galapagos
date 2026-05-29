from __future__ import annotations

import ast
from pathlib import Path

from galapagos.data.aggtrades_post_v9_full_coverage_validation_v9_29 import (
    SAFETY_FLAGS_V9_29,
    TAIL_END,
    TAIL_START,
    build_calendar_validation_v9_29,
    date_range_v9_29,
    decide_v9_29,
    reconcile_tail_v9_29,
)


def complete_day(day_value: str, rows: int = 10) -> dict:
    return {
        "date": day_value,
        "status": "day_complete",
        "raw_exists": True,
        "silver_exists": True,
        "raw_bytes": 100,
        "silver_bytes": 200,
        "rows": rows,
        "duplicates": 0,
        "invalid_rows": 0,
        "non_positive_price_count": 0,
        "non_positive_quantity_count": 0,
        "available_ts_violation_count": 0,
        "partition_mismatch_count": 0,
        "schema_mismatch": False,
        "raw_errors": [],
        "silver_errors": [],
        "min_aggregate_trade_id": rows,
        "max_aggregate_trade_id": rows + 9,
        "min_event_ts": f"{day_value}T00:00:00Z",
        "max_event_ts": f"{day_value}T23:59:59Z",
    }


def test_v9_29_target_date_range_is_731_days() -> None:
    dates = date_range_v9_29("2024-05-05", "2026-05-05")

    assert dates[0] == "2024-05-05"
    assert dates[-1] == "2026-05-05"
    assert len(dates) == 731


def test_calendar_validation_counts_unique_missing_days_v9_29(tmp_path: Path) -> None:
    first = complete_day("2024-05-05")
    missing_both = dict(complete_day("2024-05-06"))
    missing_both.update({"status": "day_failed", "raw_exists": False, "silver_exists": False, "raw_bytes": 0, "silver_bytes": 0})

    calendar = build_calendar_validation_v9_29(tmp_path, [first, missing_both])

    assert calendar["days_expected"] == 2
    assert calendar["days_complete"] == 1
    assert calendar["days_missing"] == 1
    assert calendar["days_missing_raw"] == 1
    assert calendar["days_missing_silver"] == 1
    assert calendar["first_missing_or_failed_day"] == "2024-05-06"


def test_decision_accepts_stale_quarantine_as_non_blocking_warning_v9_29() -> None:
    calendar = {"complete_calendar_coverage": True}
    quality = {"quality_status": "PASS", "aggregate_trade_id_gap_warnings": [], "timestamp_gap_warnings": []}
    quarantine = {"quarantine_blocking": False, "quarantine_stale_count": 2}
    row_outliers = {"outlier_count": 0}

    decision = decide_v9_29(calendar, quality, quarantine, row_outliers)

    assert decision["decision"] == "aggtrades_full_coverage_validated_with_non_blocking_warnings"
    assert decision["next_recommendation"] == "V9.30 - AggTrades 5Y Historical Extension Plan"


def test_tail_reconciliation_accepts_v9_28_skipped_existing_when_validated_v9_29() -> None:
    tail_dates = date_range_v9_29(TAIL_START, TAIL_END)
    inputs = {"v9_28_tail": {"payload": {"days_downloaded": 0, "days_skipped_existing": 36, "days_complete": 36}}}

    tail = reconcile_tail_v9_29(inputs, [complete_day(day_value) for day_value in tail_dates])

    assert tail["tail_days_expected"] == 36
    assert tail["tail_days_downloaded_by_v9_28"] == 0
    assert tail["tail_days_skipped_existing_by_v9_28"] == 36
    assert tail["tail_days_validated_by_v9_29"] == 36
    assert tail["tail_reporting_acceptable"] is True


def test_v9_29_safety_flags_are_read_only_data_only() -> None:
    assert SAFETY_FLAGS_V9_29["network_used"] is False
    assert SAFETY_FLAGS_V9_29["no_new_data_download"] is True
    assert SAFETY_FLAGS_V9_29["no_ingestion_executed"] is True
    assert SAFETY_FLAGS_V9_29["no_data_deletion"] is True
    assert SAFETY_FLAGS_V9_29["no_destructive_cleanup"] is True


def test_v9_29_tests_do_not_use_placeholder_bodies() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert not any(isinstance(node, ast.Pass) for node in ast.walk(tree))
    assert ("assert" + " True") not in source
    assert ("or" + " True") not in source
