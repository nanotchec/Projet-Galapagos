from __future__ import annotations

import ast
import zipfile
from pathlib import Path

import pandas as pd

from galapagos.data.aggtrades_post_v9_bad_day_repair_v9_28 import (
    BAD_DAY,
    TAIL_END,
    TAIL_START,
    apply_bad_day_repair_v9_28,
    date_range_v9_28,
    diagnose_bad_day_v9_28,
    raw_csv_columns_v9_28,
    safety_flags_v9_28,
)
from galapagos.data.aggtrades_post_v9_batch3_collection_v9_24 import validate_batch_day_v9_24
from galapagos.data.aggtrades_post_v9_collection_v9_18 import raw_zip_path_for_date_v9_18


def write_duplicate_bad_day_raw(root: Path) -> None:
    raw_path = root / raw_zip_path_for_date_v9_18(BAD_DAY)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        [10, "42000.0", "0.10", 100, 100, 1770768001000, True, True],
        [9, "41999.0", "0.20", 99, 99, 1770768000000, False, True],
        [10, "42000.0", "0.10", 100, 100, 1770768001000, True, True],
        [11, "42001.0", "0.30", 101, 101, 1770768002000, False, True],
    ]
    with zipfile.ZipFile(raw_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        csv_text = "\n".join(",".join(map(str, row)) for row in rows) + "\n"
        archive.writestr("BTCUSDT-aggTrades-2026-02-11.csv", csv_text)


def test_v9_28_date_range_is_inclusive() -> None:
    assert date_range_v9_28(TAIL_START, TAIL_END)[0] == "2026-03-31"
    assert date_range_v9_28(TAIL_START, TAIL_END)[-1] == "2026-05-05"
    assert len(date_range_v9_28(TAIL_START, TAIL_END)) == 36


def test_raw_csv_columns_keep_binance_aggtrades_order_v9_28() -> None:
    assert raw_csv_columns_v9_28() == [
        "aggregate_trade_id",
        "price",
        "quantity",
        "first_trade_id",
        "last_trade_id",
        "trade_time",
        "is_buyer_maker",
        "is_best_match",
    ]


def test_diagnose_bad_day_allows_exact_duplicate_repair_v9_28(tmp_path: Path) -> None:
    write_duplicate_bad_day_raw(tmp_path)

    diagnosis = diagnose_bad_day_v9_28(tmp_path)

    assert diagnosis["raw_zip_readable"] is True
    assert diagnosis["csv_internal_unique"] is True
    assert diagnosis["duplicate_count"] == 1
    assert diagnosis["duplicate_exact_count"] == 1
    assert diagnosis["duplicate_conflict_count"] == 0
    assert diagnosis["duplicate_repair_possible"] is True
    assert diagnosis["repair_strategy"] == "exact_deduplicate_then_sort_by_aggregate_trade_id"


def test_apply_bad_day_repair_writes_valid_silver_v9_28(tmp_path: Path) -> None:
    write_duplicate_bad_day_raw(tmp_path)
    diagnosis = diagnose_bad_day_v9_28(tmp_path)

    repair = apply_bad_day_repair_v9_28(tmp_path, diagnosis)
    validation = validate_batch_day_v9_24(tmp_path, BAD_DAY)

    assert repair["repair_applied"] is True
    assert repair["duplicate_exact_count"] == 1
    assert repair["duplicate_conflict_count"] == 0
    assert repair["rows_after"] == 3
    assert validation["status"] == "day_complete"
    assert validation["duplicates"] == 0
    assert validation["rows"] == 3


def test_safety_flags_mark_network_only_when_tail_attempted_v9_28() -> None:
    flags = safety_flags_v9_28({"repair_applied": True}, {"days_attempted": 2, "days_downloaded": 2, "days_normalized": 2})

    assert flags["network_used"] is True
    assert flags["network_scope"] == "public_archive_read_only"
    assert flags["new_data_download_scope"] == "public_historical_aggtrades_bad_day_or_final_tail_only"
    assert flags["ingestion_executed"] is True
    assert flags["no_backtest"] is True


def test_v9_28_tests_do_not_use_placeholder_bodies() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert not any(isinstance(node, ast.Pass) for node in ast.walk(tree))
    assert ("assert" + " True") not in source
    assert ("or" + " True") not in source
