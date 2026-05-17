"""Tests for V1.82.2 - includes negative test cases for validator."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# We need to import the validator logic. 
# Since it's in a script, we can either import it or mock the file system it reads.
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from validate_microstructure_data_contract_dryrun_v1_82_2_reports import validate_v1_82_2

@pytest.fixture
def mock_metrics_file(tmp_path):
    metrics_file = tmp_path / "latest_metrics.json"
    data = {
        "version": "V1.82.2",
        "research_dataset_updated": False,
        "data_contract_actual_write_executed": False,
        "predictions_created": False,
        "labels_created": False,
        "targets_created": False,
        "holdout_executed": False,
        "codex_cli_called": False,
        "pytest_executed": True,
        "pytest_exit_code": 0,
        "pytest_failed_count": 0,
        "clean_zip_ready_for_external_review": True,
        "dry_run_only": True,
        "reports_only": True,
        "trading_allowed": False,
        "data_directory_write_attempted": False
    }
    metrics_file.write_text(json.dumps(data))
    return metrics_file

def test_validator_pass(mock_metrics_file):
    """Test that valid metrics pass."""
    with patch("validate_microstructure_data_contract_dryrun_v1_82_2_reports.PROJECT_ROOT", mock_metrics_file.parent.parent):
        # We need to structure the tmp_path to have reports/current/
        reports_dir = mock_metrics_file.parent / "reports/current"
        reports_dir.mkdir(parents=True)
        new_metrics_file = reports_dir / "latest_metrics.json"
        new_metrics_file.write_text(mock_metrics_file.read_text())
        
        with patch("validate_microstructure_data_contract_dryrun_v1_82_2_reports.PROJECT_ROOT", mock_metrics_file.parent):
            assert validate_v1_82_2() is True

def test_validator_fail_missing_field(mock_metrics_file):
    """Negative test: missing mandatory field."""
    reports_dir = mock_metrics_file.parent / "reports/current"
    reports_dir.mkdir(parents=True)
    new_metrics_file = reports_dir / "latest_metrics.json"
    
    data = json.loads(mock_metrics_file.read_text())
    del data["codex_cli_called"]
    new_metrics_file.write_text(json.dumps(data))
    
    with patch("validate_microstructure_data_contract_dryrun_v1_82_2_reports.PROJECT_ROOT", mock_metrics_file.parent):
        assert validate_v1_82_2() is False

def test_validator_fail_trading_allowed(mock_metrics_file):
    """Negative test: trading allowed."""
    reports_dir = mock_metrics_file.parent / "reports/current"
    reports_dir.mkdir(parents=True)
    new_metrics_file = reports_dir / "latest_metrics.json"
    
    data = json.loads(mock_metrics_file.read_text())
    data["trading_allowed"] = True
    new_metrics_file.write_text(json.dumps(data))
    
    with patch("validate_microstructure_data_contract_dryrun_v1_82_2_reports.PROJECT_ROOT", mock_metrics_file.parent):
        assert validate_v1_82_2() is False

def test_validator_fail_version_mismatch(mock_metrics_file):
    """Negative test: version mismatch."""
    reports_dir = mock_metrics_file.parent / "reports/current"
    reports_dir.mkdir(parents=True)
    new_metrics_file = reports_dir / "latest_metrics.json"
    
    data = json.loads(mock_metrics_file.read_text())
    data["version"] = "V1.82.1"
    new_metrics_file.write_text(json.dumps(data))
    
    with patch("validate_microstructure_data_contract_dryrun_v1_82_2_reports.PROJECT_ROOT", mock_metrics_file.parent):
        assert validate_v1_82_2() is False
