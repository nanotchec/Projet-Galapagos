from __future__ import annotations

import ast
import json
from pathlib import Path

from galapagos.data.aggtrades_post_v9_collection_v9_18 import raw_zip_path_for_date_v9_18, silver_path_for_date_v9_18
from galapagos.data.aggtrades_post_v9_multi_batch_plan_v9_22 import (
    BASE_SAFETY_FLAGS,
    build_aggtrades_post_v9_multi_batch_plan_v9_22,
    build_current_coverage_v9_22,
    date_range_v9_22,
    run_aggtrades_post_v9_multi_batch_plan_v9_22,
)


def test_v9_22_builds_plan_without_network_or_ingestion(tmp_path: Path) -> None:
    _write_minimal_inputs(tmp_path)
    _write_complete_days(tmp_path, "2024-05-05", "2024-08-09")

    report = build_aggtrades_post_v9_multi_batch_plan_v9_22(tmp_path)

    assert report["status"] == "PASS"
    assert report["mode"] == "plan-only"
    assert report["collection_executed"] is False
    assert report["network_used"] is False
    assert report["new_data_downloaded"] is False
    assert report["ingestion_executed"] is False
    assert report["v9_22_decision"]["decision"] == "multi_batch_completion_plan_ready_with_disk_warning"
    assert report["current_coverage"]["current_coverage_start"] == "2024-05-05"
    assert report["current_coverage"]["current_coverage_end"] == "2024-08-09"
    assert report["current_coverage"]["days_covered"] == 97
    assert report["current_coverage"]["days_remaining"] == 634
    assert report["current_coverage"]["gaps_detected"] == []
    assert len(report["proposed_batches"]) == 11
    assert report["proposed_batches"][0]["start_date"] == "2024-08-10"
    assert report["proposed_batches"][0]["end_date"] == "2024-10-08"
    assert report["proposed_batches"][-1]["end_date"] == "2026-05-05"


def test_v9_22_uses_v9_19_v9_20_v9_21_metrics_for_estimates(tmp_path: Path) -> None:
    _write_minimal_inputs(tmp_path)
    _write_complete_days(tmp_path, "2024-05-05", "2024-08-09")

    report = build_aggtrades_post_v9_multi_batch_plan_v9_22(tmp_path)
    metrics = report["cumulative_metrics"]
    estimates = report["estimated_remaining_volume"]

    assert metrics["days_collected_total"] == 97
    assert metrics["rows_collected_total"] == 113_642_941
    assert metrics["raw_bytes_collected_total"] == 1_454_563_943
    assert metrics["silver_bytes_collected_total"] == 2_859_488_631
    assert estimates["days_remaining"] == 634
    assert estimates["estimated_remaining_rows"] == metrics["average_rows_per_day"] * 634
    assert estimates["estimated_remaining_raw_bytes"] == metrics["average_raw_bytes_per_day"] * 634
    assert estimates["estimated_remaining_silver_bytes"] == metrics["average_silver_bytes_per_day"] * 634


def test_v9_22_detects_local_gap_in_existing_coverage(tmp_path: Path) -> None:
    _write_minimal_inputs(tmp_path)
    _write_complete_days(tmp_path, "2024-05-05", "2024-08-09", omit_silver_date="2024-06-01")

    coverage = build_current_coverage_v9_22(tmp_path)
    report = build_aggtrades_post_v9_multi_batch_plan_v9_22(tmp_path)

    assert "2024-06-01" in coverage["gaps_detected"]
    assert coverage["current_coverage_end"] == "2024-05-31"
    assert report["v9_22_decision"]["decision"] == "multi_batch_completion_plan_not_ready_need_coverage_repair"
    assert report["blockers"] == ["current coverage has local raw/silver gaps"]


def test_v9_22_run_writes_report_manifest_docs_and_state(tmp_path: Path) -> None:
    _write_minimal_inputs(tmp_path)
    _write_complete_days(tmp_path, "2024-05-05", "2024-08-09")

    report = run_aggtrades_post_v9_multi_batch_plan_v9_22(tmp_path)

    expected_files = [
        "reports/data/aggtrades_post_v9_multi_batch_plan_v9_22.json",
        "reports/data/aggtrades_post_v9_multi_batch_plan_v9_22.md",
        "reports/manifests/aggtrades_post_v9_multi_batch_plan_v9_22_manifest.json",
        "docs/aggtrades_post_v9_multi_batch_plan_v9_22.md",
        "reports/current/latest_metrics.json",
        "reports/current/latest_summary.md",
        "reports/PROJECT_STATE.json",
        "README.md",
    ]
    for relative_path in expected_files:
        assert (tmp_path / relative_path).is_file(), relative_path
    state = json.loads((tmp_path / "reports/PROJECT_STATE.json").read_text())
    assert state["candidate_version"] == "V9.22"
    assert state["last_validated_version"] == "V9.21"
    assert state["network_used"] is False
    assert state["no_new_data_download"] is True
    assert state["no_ingestion_executed"] is True
    assert report["safety_flags"] == BASE_SAFETY_FLAGS


def test_v9_22_test_file_has_no_placeholder_bodies() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    pass_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Pass)]
    assert pass_nodes == []


def _write_complete_days(tmp_path: Path, start: str, end: str, omit_silver_date: str | None = None) -> None:
    for day_value in date_range_v9_22(start, end):
        raw_path = tmp_path / raw_zip_path_for_date_v9_18(day_value)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(b"raw")
        if day_value != omit_silver_date:
            silver_path = tmp_path / silver_path_for_date_v9_18(day_value)
            silver_path.parent.mkdir(parents=True, exist_ok=True)
            silver_path.write_bytes(b"silver")


def _write_minimal_inputs(tmp_path: Path) -> None:
    reports = {
        "reports/data/aggtrades_post_v9_pilot_collection_v9_19.json": _collection_report("V9.19", "pilot_validation", 7, 6_827_579, 92_848_715, 178_259_093, 69.524),
        "reports/data/aggtrades_post_v9_batch_collection_v9_20.json": _collection_report("V9.20", "batch_validation", 30, 27_668_612, 365_946_254, 718_259_780, 282.14),
        "reports/data/aggtrades_post_v9_batch_expansion_v9_21.json": _collection_report("V9.21", "batch_validation", 60, 79_146_750, 995_768_974, 1_962_969_758, 710.887),
        "reports/manifests/aggtrades_post_v9_batch_expansion_v9_21_manifest.json": {"version": "V9.21", "status": "PASS"},
        "reports/manifests/aggtrades_post_v9_batch_collection_v9_20_manifest.json": {"version": "V9.20", "status": "PASS"},
        "reports/manifests/aggtrades_post_v9_pilot_collection_v9_19_manifest.json": {"version": "V9.19", "status": "PASS"},
        "reports/data/aggtrades_post_v9_collection_v9_18.json": {"version": "V9.18", "status": "PASS"},
        "reports/manifests/aggtrades_post_v9_collection_v9_18_manifest.json": {"version": "V9.18", "status": "PASS"},
        "reports/research_decisions/derivatives_history_collection_plan_v9_17.json": {"version": "V9.17", "status": "PASS"},
        "reports/research_decisions/derivatives_window_extension_v9_16.json": {"version": "V9.16", "status": "PASS"},
        "reports/current/latest_metrics.json": {"candidate_version": "V9.21"},
        "reports/PROJECT_STATE.json": {"candidate_version": "V9.21"},
    }
    texts = {
        "reports/current/latest_summary.md": "# V9.21\n",
        "reports/PROJECT_STATE.md": "# V9.21\n",
    }
    for relative_path, payload in reports.items():
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
    for relative_path, text in texts.items():
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _collection_report(version: str, summary_key: str, days: int, rows: int, raw_bytes: int, silver_bytes: int, runtime: float) -> dict[str, object]:
    return {
        "version": version,
        "status": "PASS",
        summary_key: {
            "summary": {
                "days_complete": days,
                "total_rows": rows,
                "raw_bytes_total": raw_bytes,
                "silver_bytes_total": silver_bytes,
                "runtime_seconds": runtime,
            }
        },
    }
