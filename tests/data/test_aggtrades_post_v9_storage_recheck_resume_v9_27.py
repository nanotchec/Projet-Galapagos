from __future__ import annotations

import ast
from pathlib import Path

from galapagos.data.aggtrades_post_v9_collection_v9_18 import raw_zip_path_for_date_v9_18, silver_path_for_date_v9_18
from galapagos.data.aggtrades_post_v9_storage_recheck_resume_v9_27 import (
    MIN_FREE_BYTES,
    build_next_storage_recheck_batch_v9_27,
    build_local_coverage_inventory_v9_27,
    build_storage_recheck_batches_v9_27,
    classify_disk_policy_v9_27,
    date_range_v9_27,
    parse_df_available_gib_v9_27,
)


def test_disk_policy_blocks_below_sixty_gib_v9_27() -> None:
    policy = classify_disk_policy_v9_27(MIN_FREE_BYTES - 1)

    assert policy["safe_to_continue_now"] is False
    assert policy["resume_allowed_now"] is False
    assert policy["storage_blocker"] is True
    assert policy["batch_size_days"] == 0


def test_disk_policy_allows_seven_day_batches_above_sixty_gib_v9_27() -> None:
    policy = classify_disk_policy_v9_27(75 * 1024**3)

    assert policy["safe_to_continue_now"] is True
    assert policy["resume_allowed_now"] is True
    assert policy["batch_size_days"] == 7


def test_disk_policy_allows_sixty_day_batches_above_one_hundred_fifty_gib_v9_27() -> None:
    policy = classify_disk_policy_v9_27(160 * 1024**3)

    assert policy["safe_to_continue_now"] is True
    assert policy["resume_allowed_now"] is True
    assert policy["completion_campaign_allowed_now"] is False
    assert policy["batch_size_days"] == 60


def test_disk_policy_allows_ninety_day_batches_above_one_hundred_eighty_gib_v9_27() -> None:
    policy = classify_disk_policy_v9_27(200 * 1024**3)

    assert policy["safe_to_continue_now"] is True
    assert policy["resume_allowed_now"] is True
    assert policy["completion_campaign_allowed_now"] is True
    assert policy["batch_size_days"] == 90


def test_parse_df_available_gib_reads_df_g_output_v9_27() -> None:
    output = "Filesystem 1G-blocks Used Available Capacity Mounted on\n/dev/disk3s5 926 838 59 94% /System/Volumes/Data\n"

    assert parse_df_available_gib_v9_27(output) == 59.0


def test_local_coverage_identifies_first_missing_after_complete_prefix_v9_27(tmp_path: Path) -> None:
    for day_value in ["2024-05-05", "2024-05-06"]:
        raw_path = tmp_path / raw_zip_path_for_date_v9_18(day_value)
        silver_path = tmp_path / silver_path_for_date_v9_18(day_value)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        silver_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(b"raw")
        silver_path.write_bytes(b"silver")

    inventory = build_local_coverage_inventory_v9_27(tmp_path, "2024-05-05", "2024-05-08")

    assert inventory["local_contiguous_coverage_end"] == "2024-05-06"
    assert inventory["first_missing_day"] == "2024-05-07"
    assert inventory["days_complete"] == 2
    assert inventory["days_missing"] == 2
    assert inventory["days_partial"] == 0


def test_storage_recheck_batches_adapt_to_first_missing_day_v9_27() -> None:
    batches = build_storage_recheck_batches_v9_27("2025-02-04", "2025-05-06", 90)

    assert [batch.batch_id for batch in batches] == ["V9.27_batch_01", "V9.27_batch_02"]
    assert batches[0].start_date == "2025-02-04"
    assert batches[0].end_date == "2025-05-04"
    assert batches[0].max_downloads == 90
    assert batches[1].start_date == "2025-05-05"
    assert batches[1].end_date == "2025-05-06"
    assert batches[1].max_downloads == 2


def test_next_storage_recheck_batch_keeps_strict_max_downloads_v9_27() -> None:
    batch = build_next_storage_recheck_batch_v9_27(
        first_missing_day="2025-02-04",
        end="2026-05-05",
        batch_size_days=60,
        batch_index=3,
    )

    assert batch.batch_id == "V9.27_batch_03"
    assert batch.start_date == "2025-02-04"
    assert batch.end_date == "2025-04-04"
    assert batch.max_downloads == 60


def test_v9_27_date_range_is_inclusive() -> None:
    assert date_range_v9_27("2026-04-30", "2026-05-05") == [
        "2026-04-30",
        "2026-05-01",
        "2026-05-02",
        "2026-05-03",
        "2026-05-04",
        "2026-05-05",
    ]


def test_v9_27_tests_do_not_use_placeholder_bodies() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert not any(isinstance(node, ast.Pass) for node in ast.walk(tree))
    assert ("assert" + " True") not in source
    assert ("or" + " True") not in source
