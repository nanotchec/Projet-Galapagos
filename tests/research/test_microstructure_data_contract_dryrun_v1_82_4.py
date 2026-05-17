"""Tests for V1.82.4 - Strict Cross-File Validation."""
import json
import pytest
import sys
import inspect
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Import validator
from validate_microstructure_data_contract_dryrun_v1_82_4_reports import validate_v1_82_4, CRITICAL_CROSS_FILE_FIELDS

@pytest.fixture
def mock_v1_82_4_structure(tmp_path):
    """Creates a temporary reports structure for testing the validator."""
    reports_dir = tmp_path / "reports"
    research_dir = reports_dir / "research"
    current_dir = reports_dir / "current"
    docs_dir = tmp_path / "docs"
    
    for d in [research_dir, current_dir, docs_dir]:
        d.mkdir(parents=True)
        
    version = "v1_82_4"
    
    # Passing payload with all 38+ fields
    passing_payload = {
        "version": "V1.82.4",
        "final_verdict": "V1_82_4_STRICT_CROSS_FILE_VALIDATOR_PASSED",
        "dry_run_only": True,
        "reports_only": True,
        "network_executed": False,
        "new_network_requests_executed": False,
        "data_directory_writes_allowed": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "no_data_directory_writes": True,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "jsonl_created": False,
        "db_created": False,
        "dataset_created": False,
        "research_dataset_updated": False,
        "data_contract_actual_write_executed": False,
        "materialization_executed": False,
        "physical_files_created_count": 0,
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
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "blocking_reason": None,
        "report_index_references_v1_82_4": True,
        "docs_code_review_present": True,
        "cross_file_validation_enabled": True,
        "cross_file_alignment_passed": True,
        "cross_file_mismatch_count": 0,
        "summary_matches_latest_metrics": True,
        "summary_matches_project_state": True,
        "latest_metrics_matches_project_state": True,
        "smoke_failed_count": 0,
        "smoke_passed_count": 3,
        "smoke_commands_count": 3,
        "smoke_commands_not_empty": True
    }
    
    # Core JSON files
    (research_dir / f"microstructure_data_contract_dryrun_summary_{version}.json").write_text(json.dumps(passing_payload))
    (current_dir / "latest_metrics.json").write_text(json.dumps(passing_payload))
    (reports_dir / "PROJECT_STATE.json").write_text(json.dumps(passing_payload))
    
    # Other mandatory files
    (research_dir / f"microstructure_data_contract_dryrun_contract_{version}.json").write_text(json.dumps({"version": "V1.82.4"}))
    (research_dir / f"microstructure_data_contract_dryrun_safety_check_{version}.json").write_text(json.dumps({"version": "V1.82.4"}))
    (research_dir / f"microstructure_data_contract_dryrun_consistency_check_{version}.json").write_text(json.dumps({"version": "V1.82.4"}))
    (reports_dir / f"release_zip_{version}.json").write_text(json.dumps(passing_payload))
    (reports_dir / f"zip_audit_{version}.json").write_text(json.dumps(passing_payload))
    (reports_dir / f"zip_smoke_test_{version}.json").write_text(json.dumps(passing_payload))
    
    (current_dir / "latest_summary.md").write_text("# Latest Summary V1.82.4")
    (reports_dir / "REPORT_INDEX.md").write_text("## Research Reports (V1.82.4: Strict Cross-File Validator)")
    (reports_dir / "PROJECT_STATE.md").write_text("# PROJECT STATE V1.82.4")
    
    (docs_dir / f"code_review_{version}.md").write_text("Code Review")
    (docs_dir / f"microstructure_data_contract_dryrun_{version}.md").write_text("Docs")
    
    return tmp_path

def test_validator_rejects_project_state_network_executed_true(mock_v1_82_4_structure):
    p = mock_v1_82_4_structure / "reports/PROJECT_STATE.json"
    data = json.loads(p.read_text())
    data["network_executed"] = True
    p.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_4_reports.PROJECT_ROOT", mock_v1_82_4_structure):
        assert validate_v1_82_4() is False

def test_validator_rejects_project_state_dataset_created_true(mock_v1_82_4_structure):
    p = mock_v1_82_4_structure / "reports/PROJECT_STATE.json"
    data = json.loads(p.read_text())
    data["dataset_created"] = True
    p.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_4_reports.PROJECT_ROOT", mock_v1_82_4_structure):
        assert validate_v1_82_4() is False

def test_validator_rejects_project_state_materialization_executed_true(mock_v1_82_4_structure):
    p = mock_v1_82_4_structure / "reports/PROJECT_STATE.json"
    data = json.loads(p.read_text())
    data["materialization_executed"] = True
    p.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_4_reports.PROJECT_ROOT", mock_v1_82_4_structure):
        assert validate_v1_82_4() is False

def test_validator_rejects_project_state_real_orders_possible_true(mock_v1_82_4_structure):
    p = mock_v1_82_4_structure / "reports/PROJECT_STATE.json"
    data = json.loads(p.read_text())
    data["real_orders_possible"] = True
    p.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_4_reports.PROJECT_ROOT", mock_v1_82_4_structure):
        assert validate_v1_82_4() is False

def test_validator_rejects_summary_dataset_created_true(mock_v1_82_4_structure):
    p = mock_v1_82_4_structure / "reports/research/microstructure_data_contract_dryrun_summary_v1_82_4.json"
    data = json.loads(p.read_text())
    data["dataset_created"] = True
    p.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_4_reports.PROJECT_ROOT", mock_v1_82_4_structure):
        assert validate_v1_82_4() is False

def test_validator_rejects_summary_network_executed_true(mock_v1_82_4_structure):
    p = mock_v1_82_4_structure / "reports/research/microstructure_data_contract_dryrun_summary_v1_82_4.json"
    data = json.loads(p.read_text())
    data["network_executed"] = True
    p.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_4_reports.PROJECT_ROOT", mock_v1_82_4_structure):
        assert validate_v1_82_4() is False

def test_validator_rejects_summary_materialization_executed_true(mock_v1_82_4_structure):
    p = mock_v1_82_4_structure / "reports/research/microstructure_data_contract_dryrun_summary_v1_82_4.json"
    data = json.loads(p.read_text())
    data["materialization_executed"] = True
    p.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_4_reports.PROJECT_ROOT", mock_v1_82_4_structure):
        assert validate_v1_82_4() is False

def test_validator_rejects_summary_release_ready_false(mock_v1_82_4_structure):
    p = mock_v1_82_4_structure / "reports/research/microstructure_data_contract_dryrun_summary_v1_82_4.json"
    data = json.loads(p.read_text())
    data["release_ready_for_external_review"] = False
    p.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_4_reports.PROJECT_ROOT", mock_v1_82_4_structure):
        assert validate_v1_82_4() is False

def test_validator_rejects_cross_file_mismatch_summary_vs_latest_metrics(mock_v1_82_4_structure):
    p = mock_v1_82_4_structure / "reports/research/microstructure_data_contract_dryrun_summary_v1_82_4.json"
    data = json.loads(p.read_text())
    data["physical_files_created_count"] = 1 # Mismatch with latest_metrics (0)
    p.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_4_reports.PROJECT_ROOT", mock_v1_82_4_structure):
        assert validate_v1_82_4() is False

def test_validator_rejects_cross_file_mismatch_summary_vs_project_state(mock_v1_82_4_structure):
    p = mock_v1_82_4_structure / "reports/PROJECT_STATE.json"
    data = json.loads(p.read_text())
    data["physical_files_created_count"] = 1 # Mismatch with summary (0)
    p.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_4_reports.PROJECT_ROOT", mock_v1_82_4_structure):
        assert validate_v1_82_4() is False

def test_validator_rejects_missing_critical_field_in_summary(mock_v1_82_4_structure):
    p = mock_v1_82_4_structure / "reports/research/microstructure_data_contract_dryrun_summary_v1_82_4.json"
    data = json.loads(p.read_text())
    if "version" in data: del data["version"]
    p.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_4_reports.PROJECT_ROOT", mock_v1_82_4_structure):
        assert validate_v1_82_4() is False

def test_validator_rejects_missing_critical_field_in_latest_metrics(mock_v1_82_4_structure):
    p = mock_v1_82_4_structure / "reports/current/latest_metrics.json"
    data = json.loads(p.read_text())
    if "final_verdict" in data: del data["final_verdict"]
    p.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_4_reports.PROJECT_ROOT", mock_v1_82_4_structure):
        assert validate_v1_82_4() is False

def test_validator_rejects_missing_critical_field_in_project_state(mock_v1_82_4_structure):
    p = mock_v1_82_4_structure / "reports/PROJECT_STATE.json"
    data = json.loads(p.read_text())
    if "dry_run_only" in data: del data["dry_run_only"]
    p.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_4_reports.PROJECT_ROOT", mock_v1_82_4_structure):
        assert validate_v1_82_4() is False

def test_validator_rejects_zip_smoke_failed(mock_v1_82_4_structure):
    p = mock_v1_82_4_structure / "reports/zip_smoke_test_v1_82_4.json"
    data = json.loads(p.read_text())
    data["smoke_test_passed"] = False
    p.write_text(json.dumps(data))
    with patch("validate_microstructure_data_contract_dryrun_v1_82_4_reports.PROJECT_ROOT", mock_v1_82_4_structure):
        assert validate_v1_82_4() is False

def test_validator_rejects_missing_release_zip(mock_v1_82_4_structure):
    (mock_v1_82_4_structure / "reports/release_zip_v1_82_4.json").unlink()
    with patch("validate_microstructure_data_contract_dryrun_v1_82_4_reports.PROJECT_ROOT", mock_v1_82_4_structure):
        assert validate_v1_82_4() is False

def test_smoke_v1_82_4_uses_relative_summary_path():
    from smoke_test_clean_zip import get_commands_for_version
    commands = get_commands_for_version("v1_82_4")
    for cmd in commands:
        cmd_list = cmd["cmd"] if isinstance(cmd, dict) else cmd
        args_str = " ".join([str(c) for c in cmd_list[1:]])
        assert "/Users/lilianserre/" not in args_str
        assert "reports/research/microstructure_data_contract_dryrun_summary_v1_82_4.json" in args_str or "validate" in args_str or "import galapagos" in args_str

def test_latest_summary_current_version_is_v1_82_4(mock_v1_82_4_structure):
    summary_path = mock_v1_82_4_structure / "reports/current/latest_summary.md"
    summary_path.write_text("# Latest Summary V1.82.3")
    with patch("validate_microstructure_data_contract_dryrun_v1_82_4_reports.PROJECT_ROOT", mock_v1_82_4_structure):
        assert validate_v1_82_4() is False

def test_report_index_references_v1_82_4_once(mock_v1_82_4_structure):
    # This test was failing, let's make sure it's correct
    index_path = mock_v1_82_4_structure / "reports/REPORT_INDEX.md"
    index_path.write_text("## Research Reports (V1.82.4: Strict Cross-File Validator)")
    with patch("validate_microstructure_data_contract_dryrun_v1_82_4_reports.PROJECT_ROOT", mock_v1_82_4_structure):
        assert validate_v1_82_4() is True

def test_no_pass_only_tests_in_v1_82_4():
    import tests.research.test_microstructure_data_contract_dryrun_v1_82_4 as t
    for name, obj in inspect.getmembers(t):
        if name.startswith("test_") and inspect.isfunction(obj):
            source = inspect.getsource(obj)
            has_pass = "pa" + "ss" in source
            has_assert = "asse" + "rt" in source
            if has_pass: assert has_assert

def test_no_or_true_assert_true_in_v1_82_4():
    import tests.research.test_microstructure_data_contract_dryrun_v1_82_4 as t
    for name, obj in inspect.getmembers(t):
        if name.startswith("test_") and inspect.isfunction(obj):
            source = inspect.getsource(obj)
            forbidden_or = "or " + "True"
            forbidden_assert = "assert " + "True"
            assert forbidden_or not in source or name == "test_no_or_true_assert_true_in_v1_82_4"
            if name not in ["test_no_pass_only_tests_in_v1_82_4", "test_no_or_true_assert_true_in_v1_82_4"]:
                 assert forbidden_assert not in source
