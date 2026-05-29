from __future__ import annotations

import ast
import json
from pathlib import Path

from galapagos.data.aggtrades_5y_extension_plan_v9_30 import (
    SAFETY_FLAGS_V9_30,
    build_aggtrades_5y_extension_plan_v9_30,
    build_collection_plan_v9_31,
    build_target_5y_window_v9_30,
    date_range_v9_30,
    run_aggtrades_5y_extension_plan_v9_30,
)


def test_v9_30_5y_window_and_extension_days_are_exact() -> None:
    target = build_target_5y_window_v9_30()

    assert target["target_5y_days_expected"] == 1827
    assert target["already_validated_days"] == 731
    assert target["extension_days_needed"] == 1096
    assert date_range_v9_30("2021-05-05", "2021-05-07") == ["2021-05-05", "2021-05-06", "2021-05-07"]


def test_v9_30_builds_plan_without_network_or_ingestion(tmp_path: Path) -> None:
    _write_minimal_inputs(tmp_path)

    report = build_aggtrades_5y_extension_plan_v9_30(tmp_path)

    assert report["mode"] == "plan-only"
    assert report["network_used"] is False
    assert report["new_data_downloaded"] is False
    assert report["ingestion_executed"] is False
    assert report["extension_window_start"] == "2021-05-05"
    assert report["extension_window_end"] == "2024-05-04"
    assert report["extension_days_needed"] == 1096
    assert report["estimated_extension_rows"] > 0
    assert report["source_availability_assessment"]["availability_needs_confirmation"] is True
    assert report["collection_plan_v9_31"][0]["start_date"] == "2021-05-05"
    assert report["collection_plan_v9_31"][-1]["end_date"] == "2024-05-04"


def test_v9_31_collection_plan_caps_batches_at_ninety_days(tmp_path: Path) -> None:
    _write_minimal_inputs(tmp_path)
    report = build_aggtrades_5y_extension_plan_v9_30(tmp_path)

    batches = report["collection_plan_v9_31"]

    assert max(batch["expected_days"] for batch in batches) <= 90
    assert sum(batch["expected_days"] for batch in batches) == 1096
    assert len(batches) >= 13
    assert all(batch["checkpoint_required"] is True for batch in batches)
    assert all(batch["overwrite_complete_days"] is False for batch in batches)


def test_v9_30_safety_flags_are_plan_only() -> None:
    assert SAFETY_FLAGS_V9_30["network_used"] is False
    assert SAFETY_FLAGS_V9_30["no_new_data_download"] is True
    assert SAFETY_FLAGS_V9_30["no_ingestion_executed"] is True
    assert SAFETY_FLAGS_V9_30["no_ml"] is True
    assert SAFETY_FLAGS_V9_30["no_dataset_supervised"] is True


def test_v9_30_run_writes_report_manifest_docs_and_state(tmp_path: Path) -> None:
    _write_minimal_inputs(tmp_path)

    report = run_aggtrades_5y_extension_plan_v9_30(tmp_path)

    expected = [
        "reports/data/aggtrades_5y_extension_plan_v9_30.json",
        "reports/data/aggtrades_5y_extension_plan_v9_30.md",
        "reports/manifests/aggtrades_5y_extension_plan_v9_30_manifest.json",
        "docs/aggtrades_5y_extension_plan_v9_30.md",
        "reports/current/latest_metrics.json",
        "reports/current/latest_summary.md",
        "reports/PROJECT_STATE.json",
        "README.md",
    ]
    for relative in expected:
        assert (tmp_path / relative).is_file(), relative
    state = json.loads((tmp_path / "reports/PROJECT_STATE.json").read_text(encoding="utf-8"))
    assert state["candidate_version"] == "V9.30"
    assert state["last_validated_version"] == "V9.29"
    assert state["network_used"] is False
    assert report["safety_flags"] == SAFETY_FLAGS_V9_30


def test_v9_30_tests_do_not_use_placeholder_bodies() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert not any(isinstance(node, ast.Pass) for node in ast.walk(tree))
    assert ("assert" + " True") not in source
    assert ("or" + " True") not in source


def _write_minimal_inputs(tmp_path: Path) -> None:
    v9_29 = {
        "version": "V9.29",
        "status": "PASS",
        "decision": "aggtrades_full_coverage_validated_with_non_blocking_warnings",
        "days_expected": 731,
        "days_complete": 731,
        "total_rows_cumulative": 954_304_111,
        "raw_bytes_cumulative": 13_304_131_326,
        "silver_bytes_cumulative": 25_876_022_841,
        "quality_status": "PASS",
        "coverage_status": "target_window_validated",
        "complete_collection_reached": True,
        "future_full_coverage_complete": True,
        "quarantine_active_count": 0,
        "quarantine_stale_count": 19,
        "quarantine_blocking": False,
    }
    reports = {
        "reports/data/aggtrades_post_v9_full_coverage_validation_v9_29.json": v9_29,
        "reports/manifests/aggtrades_post_v9_full_coverage_validation_v9_29_manifest.json": {"version": "V9.29", "status": "PASS"},
        "reports/data/aggtrades_post_v9_bad_day_repair_v9_28.json": {"version": "V9.28", "status": "PASS"},
        "reports/data/aggtrades_post_v9_storage_recheck_resume_v9_27.json": {"version": "V9.27", "status": "PASS"},
        "reports/data/aggtrades_post_v9_storage_resume_campaign_v9_26.json": {"version": "V9.26", "status": "PASS"},
        "reports/data/aggtrades_post_v9_resume_campaign_v9_25_1.json": {"version": "V9.25.1", "status": "PASS"},
        "reports/data/aggtrades_post_v9_batch3_collection_v9_24.json": {"version": "V9.24", "status": "PASS"},
        "reports/data/aggtrades_post_v9_batch2_collection_v9_23.json": {"version": "V9.23", "status": "PASS"},
        "reports/data/aggtrades_post_v9_batch_expansion_v9_21.json": {"version": "V9.21", "status": "PASS"},
        "reports/data/aggtrades_post_v9_batch_collection_v9_20.json": {"version": "V9.20", "status": "PASS"},
        "reports/data/aggtrades_post_v9_pilot_collection_v9_19.json": {"version": "V9.19", "status": "PASS"},
        "reports/manifests/public_trades_1y_window_v8_2_manifest.json": {"version": "V8.2", "status": "PASS"},
        "reports/manifests/max_history_public_market_data_v5_0_manifest.json": {"version": "V5.0", "status": "PASS"},
        "reports/current/latest_metrics.json": {"candidate_version": "V9.29"},
        "reports/PROJECT_STATE.json": {"candidate_version": "V9.29"},
    }
    texts = {
        "reports/data/aggtrades_post_v9_full_coverage_validation_v9_29.md": "# V9.29\n",
        "reports/current/latest_summary.md": "# V9.29\n",
        "reports/PROJECT_STATE.md": "# V9.29\n",
    }
    for relative, payload in reports.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
    for relative, text in texts.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
