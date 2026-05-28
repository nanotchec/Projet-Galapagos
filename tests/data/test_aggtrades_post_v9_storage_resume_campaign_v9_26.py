from __future__ import annotations

import ast
from pathlib import Path

from galapagos.data.aggtrades_post_v9_collection_v9_18 import raw_zip_path_for_date_v9_18, silver_path_for_date_v9_18
from galapagos.data.aggtrades_post_v9_storage_resume_campaign_v9_26 import (
    MIN_FREE_BYTES,
    build_local_coverage_inventory_v9_26,
    build_storage_resume_batches_v9_26,
    classify_disk_policy_v9_26,
    date_range_v9_26,
)


def test_disk_policy_blocks_below_sixty_gib_v9_26() -> None:
    policy = classify_disk_policy_v9_26(MIN_FREE_BYTES - 1)

    assert policy["safe_to_continue_now"] is False
    assert policy["resume_allowed_now"] is False
    assert policy["storage_blocker"] is True
    assert policy["batch_size_days"] == 0


def test_disk_policy_uses_micro_batches_between_sixty_and_hundred_gib_v9_26() -> None:
    policy = classify_disk_policy_v9_26(75 * 1024**3)

    assert policy["safe_to_continue_now"] is True
    assert policy["resume_allowed_now"] is False
    assert policy["storage_blocker"] is False
    assert policy["batch_size_days"] == 7


def test_disk_policy_allows_resume_above_one_hundred_fifty_gib_v9_26() -> None:
    policy = classify_disk_policy_v9_26(181 * 1024**3)

    assert policy["safe_to_continue_now"] is True
    assert policy["resume_allowed_now"] is True
    assert policy["completion_campaign_allowed_now"] is True
    assert policy["batch_size_days"] == 90


def test_local_coverage_identifies_first_missing_after_complete_prefix_v9_26(tmp_path: Path) -> None:
    for day_value in ["2024-05-05", "2024-05-06"]:
        raw_path = tmp_path / raw_zip_path_for_date_v9_18(day_value)
        silver_path = tmp_path / silver_path_for_date_v9_18(day_value)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        silver_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(b"raw")
        silver_path.write_bytes(b"silver")

    inventory = build_local_coverage_inventory_v9_26(tmp_path, "2024-05-05", "2024-05-08")

    assert inventory["local_contiguous_coverage_start"] == "2024-05-05"
    assert inventory["local_contiguous_coverage_end"] == "2024-05-06"
    assert inventory["first_missing_day"] == "2024-05-07"
    assert inventory["days_complete"] == 2
    assert inventory["days_missing"] == 2
    assert inventory["days_partial"] == 0


def test_storage_resume_batches_adapt_to_first_missing_day_v9_26() -> None:
    batches = build_storage_resume_batches_v9_26("2025-02-04", "2025-05-06", 90)

    assert [batch.batch_id for batch in batches] == ["V9.26_batch_01", "V9.26_batch_02"]
    assert batches[0].start_date == "2025-02-04"
    assert batches[0].end_date == "2025-05-04"
    assert batches[0].max_downloads == 90
    assert batches[1].start_date == "2025-05-05"
    assert batches[1].end_date == "2025-05-06"
    assert batches[1].max_downloads == 2


def test_v9_26_date_range_is_inclusive() -> None:
    assert date_range_v9_26("2026-04-30", "2026-05-05") == [
        "2026-04-30",
        "2026-05-01",
        "2026-05-02",
        "2026-05-03",
        "2026-05-04",
        "2026-05-05",
    ]


def test_v9_26_tests_do_not_use_placeholder_bodies() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert not any(isinstance(node, ast.Pass) for node in ast.walk(tree))
    assert ("assert" + " True") not in source
    assert ("or" + " True") not in source
