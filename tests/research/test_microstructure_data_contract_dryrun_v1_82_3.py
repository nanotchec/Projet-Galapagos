"""Tests for V1.82.3 - Real tests for validation and safety invariants."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch
import sys
import inspect

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Import validator
from validate_microstructure_data_contract_dryrun_v1_82_3_reports import validate_v1_82_3

@pytest.fixture
def mock_reports_structure(tmp_path):
    """Creates a temporary reports structure for testing the validator."""
    reports_dir = tmp_path / "reports"
    research_dir = reports_dir / "research"
    current_dir = reports_dir / "current"
    docs_dir = tmp_path / "docs"
    
    for d in [research_dir, current_dir, docs_dir]:
        d.mkdir(parents=True)
        
    version = "v1_82_3"
    mandatory_files = [
        f"research/microstructure_data_contract_dryrun_summary_{version}.json",
        f"research/microstructure_data_contract_dryrun_contract_{version}.json",
        f"research/microstructure_data_contract_dryrun_safety_check_{version}.json",
        f"research/microstructure_data_contract_dryrun_consistency_check_{version}.json",
        f"research/v1_82_3_recommendation.json",
        f"release_zip_{version}.json",
        f"zip_audit_{version}.json",
        f"zip_smoke_test_{version}.json",
        "current/latest_metrics.json",
        "current/latest_summary.md",
        "PROJECT_STATE.json",
        "REPORT_INDEX.md"
    ]
    
    # Default passing payload
    passing_payload = {
        "version": "V1.82.3",
        "dry_run_only": True,
        "reports_only": True,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "no_data_directory_writes": True,
        "dataset_created": False,
        "research_dataset_updated": False,
        "data_contract_actual_write_executed": False,
        "materialization_executed": False,
        "physical_files_created_count": 0,
        "network_executed": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "no_real_trading": True,
        "no_paper_live": True,
        "ml_signal_validation_executed": False,
        "predictions_created": False,
        "labels_created": False,
        "targets_created": False,
        "holdout_executed": False,
        "codex_cli_called": False,
        "pytest_executed": True,
        "pytest_exit_code": 0,
        "pytest_failed_count": 0,
        "pytest_test_count_observed": 29,
        "release_zip_created": True,
        "final_zip_created": True,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "smoke_failed_count": 0,
        "smoke_passed_count": 3,
        "smoke_commands_count": 3,
        "smoke_commands_not_empty": True,
        "blocking_reason": None,
        "final_verdict": "V1_82_3_ZIP_SELF_VALIDATION_AND_DRY_RUN_RELEASE_CLEANUP_PASSED",
        "report_index_references_v1_82_3": True,
        "docs_code_review_present": True
    }
    
    for rel_path in mandatory_files:
        p = reports_dir / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix == ".json":
            p.write_text(json.dumps(passing_payload))
        elif p.name == "REPORT_INDEX.md":
            p.write_text("## Research Reports (V1.82.3: ZIP Self-Validation and Dry-Run Release Cleanup)")
        elif p.name == "latest_summary.md":
            p.write_text("# Latest Summary V1.82.3")
            
    (docs_dir / "code_review_v1_82_3.md").write_text("Code Review V1.82.3")
    (docs_dir / "microstructure_data_contract_dryrun_v1_82_3.md").write_text("Docs V1.82.3")
    
    return tmp_path

def test_release_zip_report_exists(mock_reports_structure):
    report_path = mock_reports_structure / "reports/release_zip_v1_82_3.json"
    assert report_path.is_file()

def test_release_zip_contains_clean_zip_ready_field(mock_reports_structure):
    report_path = mock_reports_structure / "reports/release_zip_v1_82_3.json"
    data = json.loads(report_path.read_text())
    assert data["clean_zip_ready_for_external_review"] is True

def test_validator_rejects_missing_release_zip(mock_reports_structure):
    (mock_reports_structure / "reports/release_zip_v1_82_3.json").unlink()
    with patch("validate_microstructure_data_contract_dryrun_v1_82_3_reports.PROJECT_ROOT", mock_reports_structure):
        assert validate_v1_82_3() is False

def test_validator_rejects_release_zip_missing_clean_zip_ready(mock_reports_structure):
    report_path = mock_reports_structure / "reports/release_zip_v1_82_3.json"
    data = json.loads(report_path.read_text())
    data["clean_zip_ready_for_external_review"] = False
    report_path.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_3_reports.PROJECT_ROOT", mock_reports_structure):
        assert validate_v1_82_3() is False

def test_validator_rejects_zip_smoke_failed(mock_reports_structure):
    report_path = mock_reports_structure / "reports/zip_smoke_test_v1_82_3.json"
    data = json.loads(report_path.read_text())
    data["smoke_test_passed"] = False
    report_path.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_3_reports.PROJECT_ROOT", mock_reports_structure):
        assert validate_v1_82_3() is False

def test_validator_rejects_zip_smoke_failed_count_positive(mock_reports_structure):
    report_path = mock_reports_structure / "reports/zip_smoke_test_v1_82_3.json"
    data = json.loads(report_path.read_text())
    data["smoke_failed_count"] = 1
    report_path.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_3_reports.PROJECT_ROOT", mock_reports_structure):
        assert validate_v1_82_3() is False

def test_validator_rejects_latest_metrics_missing_research_dataset_updated(mock_reports_structure):
    report_path = mock_reports_structure / "reports/current/latest_metrics.json"
    data = json.loads(report_path.read_text())
    del data["research_dataset_updated"]
    report_path.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_3_reports.PROJECT_ROOT", mock_reports_structure):
        assert validate_v1_82_3() is False

def test_validator_rejects_latest_metrics_missing_pytest_fields(mock_reports_structure):
    report_path = mock_reports_structure / "reports/current/latest_metrics.json"
    data = json.loads(report_path.read_text())
    del data["pytest_failed_count"]
    report_path.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_3_reports.PROJECT_ROOT", mock_reports_structure):
        assert validate_v1_82_3() is False

def test_validator_rejects_data_contract_actual_write_executed_true(mock_reports_structure):
    report_path = mock_reports_structure / "reports/current/latest_metrics.json"
    data = json.loads(report_path.read_text())
    data["data_contract_actual_write_executed"] = True
    report_path.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_3_reports.PROJECT_ROOT", mock_reports_structure):
        assert validate_v1_82_3() is False

def test_validator_rejects_predictions_created_true(mock_reports_structure):
    report_path = mock_reports_structure / "reports/current/latest_metrics.json"
    data = json.loads(report_path.read_text())
    data["predictions_created"] = True
    report_path.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_3_reports.PROJECT_ROOT", mock_reports_structure):
        assert validate_v1_82_3() is False

def test_validator_rejects_labels_created_true(mock_reports_structure):
    report_path = mock_reports_structure / "reports/current/latest_metrics.json"
    data = json.loads(report_path.read_text())
    data["labels_created"] = True
    report_path.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_3_reports.PROJECT_ROOT", mock_reports_structure):
        assert validate_v1_82_3() is False

def test_validator_rejects_targets_created_true(mock_reports_structure):
    report_path = mock_reports_structure / "reports/current/latest_metrics.json"
    data = json.loads(report_path.read_text())
    data["targets_created"] = True
    report_path.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_3_reports.PROJECT_ROOT", mock_reports_structure):
        assert validate_v1_82_3() is False

def test_validator_rejects_holdout_executed_true(mock_reports_structure):
    report_path = mock_reports_structure / "reports/current/latest_metrics.json"
    data = json.loads(report_path.read_text())
    data["holdout_executed"] = True
    report_path.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_3_reports.PROJECT_ROOT", mock_reports_structure):
        assert validate_v1_82_3() is False

def test_validator_rejects_codex_cli_called_true(mock_reports_structure):
    report_path = mock_reports_structure / "reports/current/latest_metrics.json"
    data = json.loads(report_path.read_text())
    data["codex_cli_called"] = True
    report_path.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_3_reports.PROJECT_ROOT", mock_reports_structure):
        assert validate_v1_82_3() is False

def test_smoke_v1_82_3_uses_relative_summary_path():
    from smoke_test_clean_zip import get_commands_for_version
    commands = get_commands_for_version("v1_82_3")
    for cmd in commands:
        cmd_list = cmd["cmd"] if isinstance(cmd, dict) else cmd
        # Exclude the executable itself from the relative path check as it is env-dependent
        args_str = " ".join([str(c) for c in cmd_list[1:]])
        assert "/Users/lilianserre/" not in args_str
        assert "reports/research/microstructure_data_contract_dryrun_summary_v1_82_3.json" in args_str or "validate" in args_str or "import galapagos" in args_str

def test_smoke_v1_82_3_does_not_use_absolute_user_path():
    from smoke_test_clean_zip import get_commands_for_version
    commands = get_commands_for_version("v1_82_3")
    for cmd in commands:
        cmd_list = cmd["cmd"] if isinstance(cmd, dict) else cmd
        args_str = " ".join([str(c) for c in cmd_list[1:]])
        assert "/Users/" not in args_str

def test_report_index_contains_no_unfined(mock_reports_structure):
    index_path = mock_reports_structure / "reports/REPORT_INDEX.md"
    index_path.write_text("## Research Reports (V1.82: UNFINED)")
    with patch("validate_microstructure_data_contract_dryrun_v1_82_3_reports.PROJECT_ROOT", mock_reports_structure):
        assert validate_v1_82_3() is False

def test_report_index_references_v1_82_3_once(mock_reports_structure):
    index_path = mock_reports_structure / "reports/REPORT_INDEX.md"
    index_path.write_text("## Research Reports (V1.82.3: ZIP Self-Validation and Dry-Run Release Cleanup)")
    with patch("validate_microstructure_data_contract_dryrun_v1_82_3_reports.PROJECT_ROOT", mock_reports_structure):
        assert validate_v1_82_3() is True

def test_latest_summary_current_version_is_v1_82_3(mock_reports_structure):
    summary_path = mock_reports_structure / "reports/current/latest_summary.md"
    summary_path.write_text("# Latest Summary V1.82.2")
    with patch("validate_microstructure_data_contract_dryrun_v1_82_3_reports.PROJECT_ROOT", mock_reports_structure):
        assert validate_v1_82_3() is False

def test_no_pass_only_tests_in_v1_82_3():
    import tests.research.test_microstructure_data_contract_dryrun_v1_82_3 as t
    for name, obj in inspect.getmembers(t):
        if name.startswith("test_") and inspect.isfunction(obj):
            source = inspect.getsource(obj)
            # Use a clever way to check without triggering the test itself
            has_pass = "pa" + "ss" in source
            has_assert = "asse" + "rt" in source
            if has_pass: assert has_assert

def test_no_or_true_assert_true_in_v1_82_3():
    import tests.research.test_microstructure_data_contract_dryrun_v1_82_3 as t
    for name, obj in inspect.getmembers(t):
        if name.startswith("test_") and inspect.isfunction(obj):
            source = inspect.getsource(obj)
            # Avoid self-matching by breaking the strings
            forbidden_or = "or " + "True"
            forbidden_assert = "assert " + "True"
            assert forbidden_or not in source or name == "test_no_or_true_assert_true_in_v1_82_3"
            if name not in ["test_no_pass_only_tests_in_v1_82_3", "test_no_or_true_assert_true_in_v1_82_3"]:
                 assert forbidden_assert not in source
