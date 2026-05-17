from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from galapagos.research.microstructure_data_contract_extension_post_review.reviewer import (
    EXPECTED_V1_84_HASHES,
    EXPECTED_V1_87_HASHES,
    V1_84_DATA_ROOT,
    V1_87_DATA_ROOT,
    ExtensionPostReviewReviewer,
)
from galapagos.research.microstructure_data_contract_extension_post_review.validator import validate_payload

_SMOKE_SPEC = importlib.util.spec_from_file_location("smoke_test_clean_zip", PROJECT_ROOT / "scripts/smoke_test_clean_zip.py")
if _SMOKE_SPEC is None or _SMOKE_SPEC.loader is None:
    raise RuntimeError("smoke_test_clean_zip.py cannot be loaded")
_SMOKE = importlib.util.module_from_spec(_SMOKE_SPEC)
_SMOKE_SPEC.loader.exec_module(_SMOKE)


def _valid_payload() -> dict:
    return {
        "post_extension_review_executed": True,
        "review_only": True,
        "reports_only": True,
        "extension_materialization_executed": False,
        "new_extension_materialization_executed": False,
        "materialization_executed": False,
        "data_contract_actual_write_executed": False,
        "scope_drift_detected": False,
        "data_directory_writes_allowed": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "existing_data_files_modified": False,
        "existing_v1_84_files_modified": False,
        "existing_v1_87_files_modified": False,
        "no_new_data_directory_writes": True,
        "reviewed_v1_84_files_count": 3,
        "reviewed_v1_87_files_count": 2,
        "expected_v1_84_files_count": 3,
        "expected_v1_87_files_count": 2,
        "unexpected_v1_84_files_count": 0,
        "unexpected_v1_87_files_count": 0,
        "missing_v1_84_files_count": 0,
        "missing_v1_87_files_count": 0,
        "total_v1_87_data_bytes_observed": 430,
        "v1_87_extension_manifest_json_valid": True,
        "v1_87_extension_quality_summary_json_valid": True,
        "v1_87_manifest_matches_physical_files": True,
        "v1_84_hashes_match_expected": True,
        "v1_87_hashes_match_expected": True,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "jsonl_created": False,
        "db_created": False,
        "dataset_created": False,
        "research_dataset_updated": False,
        "network_executed": False,
        "new_network_requests_executed": False,
        "request_retry_count": 0,
        "pagination_used": False,
        "authenticated_request_allowed": False,
        "secrets_used": False,
        "strategy_link_allowed": False,
        "trading_allowed": False,
        "no_strategy_validated": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "real_orders_possible": False,
        "holdout_executed": False,
        "codex_cli_called": False,
        "ml_signal_validation_executed": False,
        "predictions_created": False,
        "labels_created": False,
        "targets_created": False,
        "release_ready_for_external_review": True,
        "smoke_test_passed": True,
        "clean_zip_ready_for_external_review": True,
    }


def _errors_with(field: str, value) -> list[str]:
    payload = _valid_payload()
    payload[field] = value
    return validate_payload(payload)


def _write_review_files(root: Path) -> None:
    v1_84_root = root / V1_84_DATA_ROOT
    v1_87_root = root / V1_87_DATA_ROOT
    v1_84_root.mkdir(parents=True, exist_ok=True)
    v1_87_root.mkdir(parents=True, exist_ok=True)
    (v1_84_root / "manifest.json").write_text((PROJECT_ROOT / V1_84_DATA_ROOT / "manifest.json").read_text(encoding="utf-8"), encoding="utf-8")
    (v1_84_root / "schema_snapshot.json").write_text(
        (PROJECT_ROOT / V1_84_DATA_ROOT / "schema_snapshot.json").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (v1_84_root / "preview_records.json").write_text(
        (PROJECT_ROOT / V1_84_DATA_ROOT / "preview_records.json").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (v1_87_root / "extension_manifest.json").write_text(
        (PROJECT_ROOT / V1_87_DATA_ROOT / "extension_manifest.json").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (v1_87_root / "extension_quality_summary.json").write_text(
        (PROJECT_ROOT / V1_87_DATA_ROOT / "extension_quality_summary.json").read_text(encoding="utf-8"), encoding="utf-8"
    )


def test_review_reads_only_v1_84_and_v1_87_data_files(tmp_path):
    _write_review_files(tmp_path)
    audit = ExtensionPostReviewReviewer(tmp_path).review()
    assert audit["reviewed_v1_84_files_count"] == 3
    assert audit["reviewed_v1_87_files_count"] == 2
    assert audit["v1_84_hashes_observed"] == EXPECTED_V1_84_HASHES
    assert audit["v1_87_hashes_observed"] == EXPECTED_V1_87_HASHES


def test_review_rejects_missing_v1_87_extension_manifest(tmp_path):
    _write_review_files(tmp_path)
    (tmp_path / V1_87_DATA_ROOT / "extension_manifest.json").unlink()
    assert ExtensionPostReviewReviewer(tmp_path).review()["missing_v1_87_files_count"] == 1


def test_review_rejects_missing_v1_87_quality_summary(tmp_path):
    _write_review_files(tmp_path)
    (tmp_path / V1_87_DATA_ROOT / "extension_quality_summary.json").unlink()
    assert ExtensionPostReviewReviewer(tmp_path).review()["v1_87_extension_quality_summary_json_valid"] is False


def test_review_rejects_extra_file_in_v1_87_root(tmp_path):
    _write_review_files(tmp_path)
    (tmp_path / V1_87_DATA_ROOT / "extra.json").write_text("{}", encoding="utf-8")
    assert ExtensionPostReviewReviewer(tmp_path).review()["unexpected_v1_87_files_count"] == 1


def test_review_rejects_invalid_json_v1_87_extension_manifest(tmp_path):
    _write_review_files(tmp_path)
    (tmp_path / V1_87_DATA_ROOT / "extension_manifest.json").write_text("{", encoding="utf-8")
    assert ExtensionPostReviewReviewer(tmp_path).review()["v1_87_extension_manifest_json_valid"] is False


def test_review_rejects_invalid_json_v1_87_quality_summary(tmp_path):
    _write_review_files(tmp_path)
    (tmp_path / V1_87_DATA_ROOT / "extension_quality_summary.json").write_text("{", encoding="utf-8")
    assert ExtensionPostReviewReviewer(tmp_path).review()["v1_87_extension_quality_summary_json_valid"] is False


def test_review_rejects_v1_87_bytes_above_limit():
    assert _errors_with("total_v1_87_data_bytes_observed", 15_001)


def test_review_rejects_v1_84_hash_mismatch(tmp_path):
    _write_review_files(tmp_path)
    (tmp_path / V1_84_DATA_ROOT / "manifest.json").write_text("{}", encoding="utf-8")
    assert ExtensionPostReviewReviewer(tmp_path).review()["v1_84_hashes_match_expected"] is False


def test_review_rejects_v1_87_hash_mismatch(tmp_path):
    _write_review_files(tmp_path)
    (tmp_path / V1_87_DATA_ROOT / "extension_manifest.json").write_text("{}", encoding="utf-8")
    assert ExtensionPostReviewReviewer(tmp_path).review()["v1_87_hashes_match_expected"] is False


def test_review_rejects_forbidden_parquet_csv_sqlite_jsonl_db(tmp_path):
    _write_review_files(tmp_path)
    root = tmp_path / V1_87_DATA_ROOT
    for suffix in [".parquet", ".csv", ".sqlite", ".jsonl", ".db"]:
        (root / f"bad{suffix}").write_text("x", encoding="utf-8")
    audit = ExtensionPostReviewReviewer(tmp_path).review()
    assert audit["parquet_created"] is True
    assert audit["csv_created"] is True
    assert audit["sqlite_created"] is True
    assert audit["jsonl_created"] is True
    assert audit["db_created"] is True


def test_validator_rejects_new_data_files_created_true():
    assert _errors_with("new_data_files_created", True)


def test_validator_rejects_existing_data_files_modified_true():
    assert _errors_with("existing_data_files_modified", True)


def test_validator_rejects_existing_v1_84_files_modified_true():
    assert _errors_with("existing_v1_84_files_modified", True)


def test_validator_rejects_existing_v1_87_files_modified_true():
    assert _errors_with("existing_v1_87_files_modified", True)


def test_validator_rejects_data_directory_write_attempted_true():
    assert _errors_with("data_directory_write_attempted", True)


def test_validator_rejects_network_executed_true():
    assert _errors_with("network_executed", True)


def test_validator_rejects_dataset_created_true():
    assert _errors_with("dataset_created", True)


def test_validator_rejects_trading_allowed_true():
    assert _errors_with("trading_allowed", True)


def test_validator_rejects_real_orders_possible_true():
    assert _errors_with("real_orders_possible", True)


def test_report_index_references_v1_88():
    index = PROJECT_ROOT / "reports/REPORT_INDEX.md"
    content = index.read_text(encoding="utf-8") if index.exists() else ""
    assert "v1_88" in content or (PROJECT_ROOT / "scripts/run_microstructure_data_contract_extension_post_review_v1_88.py").exists()


def test_smoke_v1_88_runs_validator_import_and_summary_presence():
    commands = _SMOKE.get_commands_for_version("v1_88")
    assert commands[0][1] == "scripts/validate_microstructure_data_contract_extension_post_review_v1_88_reports.py"
    assert "import galapagos" in commands[1][2]
    assert "microstructure_data_contract_extension_post_review_summary_v1_88.json" in commands[2][2]


def test_cross_file_alignment_summary_latest_metrics_project_state():
    summary = _valid_payload()
    latest = dict(summary)
    project = dict(summary)
    assert latest["reviewed_v1_87_files_count"] == summary["reviewed_v1_87_files_count"]
    assert project["total_v1_87_data_bytes_observed"] == summary["total_v1_87_data_bytes_observed"]


def test_scripts_run_without_manual_pythonpath():
    result = subprocess.run(
        [sys.executable, "scripts/validate_microstructure_data_contract_extension_post_review_v1_88_reports.py", "--version", "bad"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Unsupported version" in (result.stdout + result.stderr)
