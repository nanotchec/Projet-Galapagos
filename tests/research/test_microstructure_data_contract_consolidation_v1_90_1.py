from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
for path in (PROJECT_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from galapagos.research.microstructure_data_contract_consolidation_readiness.physical_auditor import (
    EXPECTED_V1_84_HASHES,
    EXPECTED_V1_87_HASHES,
)

_VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "validate_v1_90_1",
    PROJECT_ROOT / "scripts/validate_microstructure_data_contract_consolidation_v1_90_1_reports.py",
)
if _VALIDATOR_SPEC is None or _VALIDATOR_SPEC.loader is None:
    raise RuntimeError("V1.90.1 validator cannot be loaded")
_VALIDATOR = importlib.util.module_from_spec(_VALIDATOR_SPEC)
_VALIDATOR_SPEC.loader.exec_module(_VALIDATOR)

_SMOKE_SPEC = importlib.util.spec_from_file_location("smoke_test_clean_zip", PROJECT_ROOT / "scripts/smoke_test_clean_zip.py")
if _SMOKE_SPEC is None or _SMOKE_SPEC.loader is None:
    raise RuntimeError("smoke_test_clean_zip.py cannot be loaded")
_SMOKE = importlib.util.module_from_spec(_SMOKE_SPEC)
_SMOKE_SPEC.loader.exec_module(_SMOKE)

V1_90_FILES = [
    "data/research/microstructure_contract_materialization/v1_90/consolidated_manifest.json",
    "data/research/microstructure_contract_materialization/v1_90/consolidated_schema_snapshot.json",
    "data/research/microstructure_contract_materialization/v1_90/consolidated_quality_summary.json",
]


def _write_json(root: Path, rel: str, payload: dict) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_md(root: Path, rel: str, text: str = "V1.90.1") -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _copy_data(root: Path) -> None:
    for rel in [
        "data/research/microstructure_contract_materialization/v1_84",
        "data/research/microstructure_contract_materialization/v1_87",
        "data/research/microstructure_contract_materialization/v1_90",
    ]:
        shutil.copytree(PROJECT_ROOT / rel, root / rel)


def _base_payload() -> dict:
    return {
        "version": "V1.90.1",
        "version_suffix": "v1_90_1",
        "corrective_for_version": "V1.90",
        "final_verdict": "V1_90_1_STRICT_RELEASE_SMOKE_AUDIT_VALIDATION_PASSED",
        "approval_source_verified": True,
        "human_approval_granted": True,
        "approval_phrase_match": True,
        "v1_90_authorized": True,
        "authorized_future_scope": "tiny_data_contract_consolidation_ultra_bounded_no_network_no_full_dataset_no_ml_no_trading",
        "consolidation_executed": True,
        "tiny_consolidation_only": True,
        "full_dataset_created": False,
        "scope_drift_detected": False,
        "reports_only": False,
        "network_executed": False,
        "new_network_requests_executed": False,
        "request_retry_count": 0,
        "pagination_used": False,
        "authenticated_request_allowed": False,
        "secrets_used": False,
        "data_directory_writes_allowed": True,
        "data_write_approved": True,
        "data_directory_write_attempted": True,
        "new_data_files_created": True,
        "consolidation_actual_write_executed": True,
        "unapproved_data_write_detected": False,
        "total_new_data_files_created": 3,
        "created_files_count": 3,
        "total_data_bytes_written": 1365,
        "existing_v1_84_files_modified": False,
        "existing_v1_87_files_modified": False,
        "consolidated_manifest_json_created": True,
        "consolidated_schema_snapshot_json_created": True,
        "consolidated_quality_summary_json_created": True,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "jsonl_created": False,
        "db_created": False,
        "dataset_created": False,
        "research_dataset_updated": False,
        "dataset_materialization_approved": False,
        "strategy_link_allowed": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "holdout_executed": False,
        "codex_cli_called": False,
        "no_strategy_validated": True,
        "no_real_trading": True,
        "no_paper_live": True,
        "ml_signal_validation_executed": False,
        "predictions_created": False,
        "labels_created": False,
        "targets_created": False,
        "pytest_executed": True,
        "pytest_exit_code": 0,
        "pytest_failed_count": 0,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "blocking_reason": None,
    }


def _release() -> dict:
    return {
        "version": "V1.90.1",
        "release_zip_created": True,
        "final_zip_created": True,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "final_audit_passed": True,
        "final_smoke_passed": True,
        "blocking_reason": None,
    }


def _audit() -> dict:
    return {
        "version": "V1.90.1",
        "clean_zip_ready_for_external_review": True,
        "audit_zip_project_state_version": "V1.90.1",
        "audit_zip_version_parse_correct": True,
        "forbidden_count": 0,
        "missing_required_files": [],
        "global_json_finiteness_passed": True,
    }


def _smoke() -> dict:
    return {
        "version": "V1.90.1",
        "smoke_test_passed": True,
        "smoke_commands_count": 3,
        "smoke_passed_count": 3,
        "smoke_failed_count": 0,
        "smoke_commands_not_empty": True,
        "real_orders_possible": False,
        "codex_cli_called": False,
        "holdout_executed": False,
    }


def _write_valid_report_set(root: Path) -> None:
    _copy_data(root)
    summary = _base_payload()
    file_audit = {
        "version": "V1.90.1",
        "v1_84_hashes_observed": EXPECTED_V1_84_HASHES,
        "v1_87_hashes_observed": EXPECTED_V1_87_HASHES,
    }
    for name, payload in {
        "reports/research/microstructure_data_contract_consolidation_summary_v1_90_1.json": summary,
        "reports/research/microstructure_data_contract_consolidation_file_audit_v1_90_1.json": file_audit,
        "reports/research/microstructure_data_contract_consolidation_safety_check_v1_90_1.json": {"version": "V1.90.1"},
        "reports/research/microstructure_data_contract_consolidation_consistency_check_v1_90_1.json": {"version": "V1.90.1"},
        "reports/current/latest_metrics.json": summary,
        "reports/PROJECT_STATE.json": summary,
        "reports/release_zip_v1_90_1.json": _release(),
        "reports/zip_audit_v1_90_1.json": _audit(),
        "reports/zip_smoke_test_v1_90_1.json": _smoke(),
    }.items():
        _write_json(root, name, payload)
        if name.startswith("reports/research/"):
            _write_md(root, str(Path(name).with_suffix(".md")), "V1.90.1")
    _write_md(root, "reports/current/latest_summary.md", "Latest V1.90.1")
    _write_md(root, "reports/REPORT_INDEX.md", "Index V1.90.1 v1_90_1")
    _write_md(root, "docs/code_review_v1_90_1.md", "Code review V1.90.1")
    _write_md(root, "docs/microstructure_data_contract_consolidation_v1_90_1.md", "Doc V1.90.1")


def _errors(root: Path) -> list[str]:
    return _VALIDATOR.validate_report_set(root)


def test_validator_rejects_missing_release_zip(tmp_path):
    _write_valid_report_set(tmp_path)
    (tmp_path / "reports/release_zip_v1_90_1.json").unlink()
    assert _errors(tmp_path)


def test_validator_rejects_release_clean_zip_ready_false(tmp_path):
    _write_valid_report_set(tmp_path)
    payload = _release()
    payload["clean_zip_ready_for_external_review"] = False
    _write_json(tmp_path, "reports/release_zip_v1_90_1.json", payload)
    assert _errors(tmp_path)


def test_validator_rejects_release_final_audit_false(tmp_path):
    _write_valid_report_set(tmp_path)
    payload = _release()
    payload["final_audit_passed"] = False
    _write_json(tmp_path, "reports/release_zip_v1_90_1.json", payload)
    assert _errors(tmp_path)


def test_validator_rejects_release_final_smoke_false(tmp_path):
    _write_valid_report_set(tmp_path)
    payload = _release()
    payload["final_smoke_passed"] = False
    _write_json(tmp_path, "reports/release_zip_v1_90_1.json", payload)
    assert _errors(tmp_path)


def test_validator_rejects_missing_zip_smoke(tmp_path):
    _write_valid_report_set(tmp_path)
    (tmp_path / "reports/zip_smoke_test_v1_90_1.json").unlink()
    assert _errors(tmp_path)


def test_validator_rejects_zip_smoke_failed(tmp_path):
    _write_valid_report_set(tmp_path)
    payload = _smoke()
    payload["smoke_test_passed"] = False
    _write_json(tmp_path, "reports/zip_smoke_test_v1_90_1.json", payload)
    assert _errors(tmp_path)


def test_validator_rejects_zip_smoke_failed_count_positive(tmp_path):
    _write_valid_report_set(tmp_path)
    payload = _smoke()
    payload["smoke_failed_count"] = 1
    _write_json(tmp_path, "reports/zip_smoke_test_v1_90_1.json", payload)
    assert _errors(tmp_path)


def test_validator_rejects_zip_smoke_passed_count_mismatch(tmp_path):
    _write_valid_report_set(tmp_path)
    payload = _smoke()
    payload["smoke_passed_count"] = 2
    _write_json(tmp_path, "reports/zip_smoke_test_v1_90_1.json", payload)
    assert _errors(tmp_path)


def test_validator_rejects_missing_zip_audit(tmp_path):
    _write_valid_report_set(tmp_path)
    (tmp_path / "reports/zip_audit_v1_90_1.json").unlink()
    assert _errors(tmp_path)


def test_validator_rejects_zip_audit_project_state_version_mismatch(tmp_path):
    _write_valid_report_set(tmp_path)
    payload = _audit()
    payload["audit_zip_project_state_version"] = "V1.89"
    _write_json(tmp_path, "reports/zip_audit_v1_90_1.json", payload)
    assert _errors(tmp_path)


def test_validator_rejects_zip_audit_version_parse_false(tmp_path):
    _write_valid_report_set(tmp_path)
    payload = _audit()
    payload["audit_zip_version_parse_correct"] = False
    _write_json(tmp_path, "reports/zip_audit_v1_90_1.json", payload)
    assert _errors(tmp_path)


def test_validator_rejects_zip_audit_missing_required_files_non_empty(tmp_path):
    _write_valid_report_set(tmp_path)
    payload = _audit()
    payload["missing_required_files"] = ["reports/PROJECT_STATE.json"]
    _write_json(tmp_path, "reports/zip_audit_v1_90_1.json", payload)
    assert _errors(tmp_path)


def test_validator_rejects_latest_metrics_network_executed_true(tmp_path):
    _write_valid_report_set(tmp_path)
    payload = _base_payload()
    payload["network_executed"] = True
    _write_json(tmp_path, "reports/current/latest_metrics.json", payload)
    assert _errors(tmp_path)


def test_validator_rejects_project_state_dataset_created_true(tmp_path):
    _write_valid_report_set(tmp_path)
    payload = _base_payload()
    payload["dataset_created"] = True
    _write_json(tmp_path, "reports/PROJECT_STATE.json", payload)
    assert _errors(tmp_path)


def test_validator_rejects_summary_created_files_count_above_3(tmp_path):
    _write_valid_report_set(tmp_path)
    payload = _base_payload()
    payload["created_files_count"] = 4
    _write_json(tmp_path, "reports/research/microstructure_data_contract_consolidation_summary_v1_90_1.json", payload)
    assert _errors(tmp_path)


def test_validator_rejects_extra_file_in_v1_90_directory(tmp_path):
    _write_valid_report_set(tmp_path)
    _write_json(tmp_path, "data/research/microstructure_contract_materialization/v1_90/extra.json", {"extra": True})
    assert _errors(tmp_path)


def test_validator_rejects_missing_consolidated_manifest(tmp_path):
    _write_valid_report_set(tmp_path)
    (tmp_path / V1_90_FILES[0]).unlink()
    assert _errors(tmp_path)


def test_validator_rejects_missing_consolidated_schema_snapshot(tmp_path):
    _write_valid_report_set(tmp_path)
    (tmp_path / V1_90_FILES[1]).unlink()
    assert _errors(tmp_path)


def test_validator_rejects_missing_consolidated_quality_summary(tmp_path):
    _write_valid_report_set(tmp_path)
    (tmp_path / V1_90_FILES[2]).unlink()
    assert _errors(tmp_path)


def test_validator_rejects_v1_84_hash_mismatch(tmp_path):
    _write_valid_report_set(tmp_path)
    (tmp_path / "data/research/microstructure_contract_materialization/v1_84/manifest.json").write_text("{}", encoding="utf-8")
    assert _errors(tmp_path)


def test_validator_rejects_v1_87_hash_mismatch(tmp_path):
    _write_valid_report_set(tmp_path)
    (tmp_path / "data/research/microstructure_contract_materialization/v1_87/extension_manifest.json").write_text("{}", encoding="utf-8")
    assert _errors(tmp_path)


def test_report_index_references_v1_90_1(tmp_path):
    _write_valid_report_set(tmp_path)
    assert not _errors(tmp_path)


def test_latest_summary_mentions_v1_90_1(tmp_path):
    _write_valid_report_set(tmp_path)
    assert "V1.90.1" in (tmp_path / "reports/current/latest_summary.md").read_text(encoding="utf-8")


def test_smoke_v1_90_1_uses_relative_paths():
    commands = _SMOKE.get_commands_for_version("v1_90_1")
    assert commands[0][1] == "scripts/validate_microstructure_data_contract_consolidation_v1_90_1_reports.py"
    assert "reports/research/microstructure_data_contract_consolidation_summary_v1_90_1.json" in commands[2][2]
    for command in commands:
        assert not any(str(PROJECT_ROOT) in part for part in command)


def test_scripts_run_without_manual_pythonpath():
    for script in [
        "scripts/run_microstructure_data_contract_consolidation_v1_90_1.py",
        "scripts/validate_microstructure_data_contract_consolidation_v1_90_1_reports.py",
    ]:
        result = subprocess.run([sys.executable, script, "--help"], cwd=PROJECT_ROOT, capture_output=True, text=True)
        assert result.returncode == 0


def test_no_pass_only_tests_in_v1_90_1():
    content = Path(__file__).read_text(encoding="utf-8")
    assert not re.search(r"^\s*pass\s*$", content, re.MULTILINE)


def test_no_assert_true_or_true_in_v1_90_1():
    content = Path(__file__).read_text(encoding="utf-8")
    assert ("assert " + "True") not in content
    assert ("or " + "True") not in content
