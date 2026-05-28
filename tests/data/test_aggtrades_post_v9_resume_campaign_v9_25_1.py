from __future__ import annotations

import ast
from collections import namedtuple
from pathlib import Path

from galapagos.data import aggtrades_post_v9_resume_campaign_v9_25_1 as resume
from galapagos.data.aggtrades_post_v9_collection_v9_18 import raw_zip_path_for_date_v9_18, silver_path_for_date_v9_18
from galapagos.data.aggtrades_post_v9_resume_campaign_v9_25_1 import (
    MIN_FREE_BYTES,
    build_disk_preflight_v9_25_1,
    build_local_coverage_inventory_v9_25_1,
    build_resume_batches_v9_25_1,
    date_range_v9_25_1,
    decide_v9_25_1,
    safety_flags_v9_25_1,
)


def _mark_complete(root: Path, day_value: str) -> None:
    raw_path = root / raw_zip_path_for_date_v9_18(day_value)
    silver_path = root / silver_path_for_date_v9_18(day_value)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    silver_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(b"raw")
    silver_path.write_bytes(b"silver")


def test_local_coverage_identifies_first_missing_day_v9_25_1(tmp_path: Path) -> None:
    _mark_complete(tmp_path, "2024-05-05")
    _mark_complete(tmp_path, "2024-05-06")

    coverage = build_local_coverage_inventory_v9_25_1(tmp_path, "2024-05-05", "2024-05-08")

    assert coverage["days_complete"] == 2
    assert coverage["first_missing_day"] == "2024-05-07"
    assert coverage["last_complete_day_before_gap"] == "2024-05-06"
    assert coverage["gaps_detected"] == [{"start": "2024-05-07", "end": "2024-05-08"}]


def test_resume_batches_follow_disk_batch_size_v9_25_1() -> None:
    batches = build_resume_batches_v9_25_1("2025-02-03", "2025-04-05", 30)

    assert [batch.max_downloads for batch in batches] == [30, 30, 2]
    assert batches[0].start_date == "2025-02-03"
    assert batches[-1].end_date == "2025-04-05"
    assert sum(len(date_range_v9_25_1(batch.start_date, batch.end_date)) for batch in batches) == 62


def test_disk_preflight_blocks_below_sixty_gib_v9_25_1(tmp_path: Path, monkeypatch) -> None:
    DiskUsage = namedtuple("DiskUsage", ["total", "used", "free"])
    monkeypatch.setattr(resume.shutil, "disk_usage", lambda _: DiskUsage(total=200 * 1024**3, used=150 * 1024**3, free=MIN_FREE_BYTES - 1))
    canonical = {
        "days_missing": 10,
        "days_partial": 0,
        "canonical_raw_bytes_new": 1000,
        "canonical_silver_bytes_new": 2000,
        "canonical_days_newly_completed": 1,
    }

    preflight = build_disk_preflight_v9_25_1(tmp_path, canonical)

    assert preflight["safe_to_continue_now"] is False
    assert preflight["storage_blocker"] is True
    assert preflight["batch_size_days"] == 0


def test_disk_preflight_uses_micro_batches_between_sixty_and_hundred_gib_v9_25_1(tmp_path: Path, monkeypatch) -> None:
    DiskUsage = namedtuple("DiskUsage", ["total", "used", "free"])
    monkeypatch.setattr(resume.shutil, "disk_usage", lambda _: DiskUsage(total=200 * 1024**3, used=130 * 1024**3, free=70 * 1024**3))
    canonical = {
        "days_missing": 10,
        "days_partial": 0,
        "canonical_raw_bytes_new": 1000,
        "canonical_silver_bytes_new": 2000,
        "canonical_days_newly_completed": 1,
    }

    preflight = build_disk_preflight_v9_25_1(tmp_path, canonical)

    assert preflight["safe_to_continue_now"] is True
    assert preflight["batch_size_days"] == 30
    assert "micro_batches_30_days" in preflight["storage_warning"]


def test_decision_storage_blocker_when_no_collection_v9_25_1() -> None:
    decision = decide_v9_25_1(
        {"days_attempted_total": 0, "days_complete_total": 0, "complete_collection_reached": False},
        {"state_reconciled": True},
        {"safe_to_continue_now": False},
        {"type": "storage"},
    )

    assert decision["decision"] == "resume_collection_not_executed_storage_blocker"
    assert "Storage Cleanup" in decision["next_recommendation"]


def test_safety_flags_disable_trading_and_deletion_v9_25_1() -> None:
    flags = safety_flags_v9_25_1({"days_attempted_total": 1, "days_downloaded_total": 1, "days_normalized_total": 1})

    assert flags["network_scope"] == "public_archive_read_only"
    assert flags["new_data_download_scope"] == "public_historical_aggtrades_resume_only"
    assert flags["ingestion_scope"] == "public_aggtrades_bronze_silver_resume_only"
    assert flags["api_key_used"] is False
    assert flags["private_endpoint_used"] is False
    assert flags["exchange_auth_used"] is False
    assert flags["websocket_live_used"] is False
    assert flags["no_data_deletion"] is True
    assert flags["no_destructive_cleanup"] is True
    assert flags["no_backtest"] is True
    assert flags["no_walk_forward"] is True


def test_v9_25_1_tests_do_not_use_placeholder_bodies() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    pass_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Pass)]

    assert pass_nodes == []
