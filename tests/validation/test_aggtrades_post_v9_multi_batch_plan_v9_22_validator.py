from __future__ import annotations

import copy
import json
from pathlib import Path

from galapagos.data.aggtrades_post_v9_collection_v9_18 import raw_zip_path_for_date_v9_18, silver_path_for_date_v9_18
from galapagos.data.aggtrades_post_v9_multi_batch_plan_v9_22 import (
    date_range_v9_22,
    run_aggtrades_post_v9_multi_batch_plan_v9_22,
)
from galapagos.data.aggtrades_post_v9_multi_batch_plan_v9_22_validation import (
    validate_markdown_v9_22,
    validate_report_payload_v9_22,
    validate_aggtrades_post_v9_multi_batch_plan_v9_22,
)


def test_v9_22_validator_accepts_generated_plan(tmp_path: Path) -> None:
    _prepare_valid_plan(tmp_path)

    errors = validate_aggtrades_post_v9_multi_batch_plan_v9_22(tmp_path)

    assert errors == []


def test_v9_22_validator_rejects_invalid_decision(tmp_path: Path) -> None:
    report = _prepare_valid_plan(tmp_path)
    report["v9_22_decision"]["decision"] = "limited_research_backtest_candidate"

    errors = validate_report_payload_v9_22(report)

    assert "V9.22 decision is not allowed" in errors
    assert errors.count("V9.22 decision is not allowed") == 1


def test_v9_22_validator_rejects_network_or_ingestion(tmp_path: Path) -> None:
    report = _prepare_valid_plan(tmp_path)
    report["network_used"] = True
    report["safety_flags"]["network_used"] = True
    report["safety_flags"]["no_new_data_download"] = False
    report["ingestion_executed"] = True

    errors = validate_report_payload_v9_22(report)

    assert "V9.22 must keep network_used=false" in errors
    assert "V9.22 must keep ingestion_executed=false" in errors
    assert "V9.22 safety flag mismatch: network_used" in errors
    assert "V9.22 safety flag mismatch: no_new_data_download" in errors


def test_v9_22_validator_rejects_gap_claim(tmp_path: Path) -> None:
    report = _prepare_valid_plan(tmp_path)
    report["current_coverage"]["gaps_detected"] = ["2024-06-01"]

    errors = validate_report_payload_v9_22(report)

    assert "V9.22 expected no gaps after validated V9.19/V9.20/V9.21 batches" in errors


def test_v9_22_validator_rejects_oversized_or_non_contiguous_batch(tmp_path: Path) -> None:
    report = _prepare_valid_plan(tmp_path)
    report["proposed_batches"][0]["expected_days"] = 61
    report["proposed_batches"][1]["start_date"] = "2024-10-10"

    errors = validate_report_payload_v9_22(report)

    assert "V9.22 proposed batches must not exceed 60 days" in errors
    assert "V9.22 proposed batches must be contiguous" in errors


def test_v9_22_validator_rejects_forbidden_markdown_terms() -> None:
    errors = validate_markdown_v9_22("Aucun trading. Sharpe et equity curve.")

    assert any("sharpe" in error for error in errors)
    assert any("equity curve" in error for error in errors)


def test_v9_22_validator_rejects_sidecar_zip_field(tmp_path: Path) -> None:
    report = _prepare_valid_plan(tmp_path)
    report["zip_sha256"] = "forbidden"

    errors = validate_report_payload_v9_22(report)

    assert "V9.22 report must not contain sidecar or ZIP hash fields" in errors


def _prepare_valid_plan(tmp_path: Path) -> dict[str, object]:
    _write_minimal_inputs(tmp_path)
    _write_complete_days(tmp_path)
    report = run_aggtrades_post_v9_multi_batch_plan_v9_22(tmp_path)
    return copy.deepcopy(report)


def _write_complete_days(tmp_path: Path) -> None:
    for day_value in date_range_v9_22("2024-05-05", "2024-08-09"):
        raw_path = tmp_path / raw_zip_path_for_date_v9_18(day_value)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(b"raw")
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
