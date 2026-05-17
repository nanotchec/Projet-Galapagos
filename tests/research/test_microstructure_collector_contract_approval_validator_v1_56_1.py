from __future__ import annotations
import json
import pytest
import sys
import importlib.util
from pathlib import Path

# Load script as module
spec = importlib.util.spec_from_file_location("validator", "scripts/validate_microstructure_collector_contract_approval_reports.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)
validate_reports = validator.validate_reports

@pytest.fixture
def mock_reports_dir(tmp_path):
    research_dir = tmp_path / "reports" / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    current_dir = reports_dir / "current"
    current_dir.mkdir(parents=True, exist_ok=True)
    
    version = "V1.56.1"
    v_norm = "v1_56_1"
    
    # Create all required reports with valid content
    required_json = [
        f"microstructure_contract_input_guard_{v_norm}.json",
        f"microstructure_contract_approval_checklist_{v_norm}.json",
        f"microstructure_required_field_coverage_{v_norm}.json",
        f"microstructure_adapter_contract_completeness_{v_norm}.json",
        f"microstructure_timestamp_policy_approval_{v_norm}.json",
        f"microstructure_manifest_contract_approval_{v_norm}.json",
        f"microstructure_fixture_coverage_approval_{v_norm}.json",
        f"microstructure_network_safety_approval_{v_norm}.json",
        f"microstructure_data_write_safety_approval_{v_norm}.json",
        f"microstructure_contract_approval_decision_{v_norm}.json",
        f"microstructure_contract_recommendation_{v_norm}.json",
        f"microstructure_contract_approval_summary_{v_norm}.json",
        f"microstructure_contract_approval_consistency_check_{v_norm}.json",
        f"{v_norm}_recommendation.json"
    ]
    
    valid_consist = {
        "version": version,
        "previous_base": "V1.56",
        "consistency_check_status": "MICROSTRUCTURE_CONTRACT_APPROVAL_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY",
        "issues": [],
        "project_state_verdict_aligned": True,
        "latest_metrics_verdict_aligned": True,
        "latest_summary_verdict_aligned": True,
        "stale_v1_55_verdict_removed": True,
        "required_reports_present": True,
        "required_markdown_reports_present": True,
        "project_state_aligned": True,
        "latest_metrics_aligned": True,
        "latest_summary_aligned": True,
        "real_collection_approved": False,
        "human_review_required_before_collection": True,
        "network_disabled": True,
        "dry_run_only": True,
        "local_fixture_only": True,
        "fixture_only": True,
        "synthetic_or_minimal_sample": True,
        "not_for_research_results": True,
        "real_collection_executed": False,
        "external_data_downloaded": False,
        "external_api_called": False,
        "new_data_files_created": False,
        "no_data_directory_writes": True,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "requests_executed_count": 0,
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "real_orders_possible": False,
        "contract_ready_for_offline_review": False,
        "required_fields_covered": False,
        "missing_required_fields": 8
    }
    
    valid_ps = {
        "version": version,
        "final_verdict": "MICROSTRUCTURE_COLLECTOR_CONTRACT_PARTIAL",
        "recommended_next_step": "refine adapter field coverage before offline review",
        "consistency_check_status": "MICROSTRUCTURE_CONTRACT_APPROVAL_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY"
    }
    valid_ps.update(valid_consist)
    
    valid_lm = {
        "version": version,
        "final_verdict": "MICROSTRUCTURE_COLLECTOR_CONTRACT_PARTIAL",
        "recommended_next_step": "refine adapter field coverage before offline review"
    }
    valid_lm.update(valid_consist)

    for f_name in required_json:
        p = research_dir / f_name
        content = valid_consist if "consistency_check" in f_name else {"version": version}
        p.write_text(json.dumps(content))
        (research_dir / f_name.replace(".json", ".md")).write_text("mock")
        
    (docs_dir / f"microstructure_collector_contract_approval_{v_norm}.md").write_text("mock")
    (reports_dir / "PROJECT_STATE.json").write_text(json.dumps(valid_ps))
    (current_dir / "latest_metrics.json").write_text(json.dumps(valid_lm))
    
    return tmp_path

def test_validator_happy_path(mock_reports_dir, monkeypatch):
    monkeypatch.chdir(mock_reports_dir)
    validate_reports("V1.56.1")

def test_validator_rejects_stale_verdict(mock_reports_dir, monkeypatch):
    monkeypatch.chdir(mock_reports_dir)
    ps_path = mock_reports_dir / "reports" / "PROJECT_STATE.json"
    ps = json.loads(ps_path.read_text())
    ps["final_verdict"] = "MICROSTRUCTURE_ADAPTER_FIXTURE_TESTS_READY"
    ps_path.write_text(json.dumps(ps))
    
    with pytest.raises(ValueError, match="PROJECT_STATE final_verdict mismatch"):
        validate_reports("V1.56.1")

def test_validator_rejects_real_collection_approved(mock_reports_dir, monkeypatch):
    monkeypatch.chdir(mock_reports_dir)
    consist_path = mock_reports_dir / "reports" / "research" / "microstructure_contract_approval_consistency_check_v1_56_1.json"
    consist = json.loads(consist_path.read_text())
    consist["real_collection_approved"] = True
    consist_path.write_text(json.dumps(consist))
    
    with pytest.raises(ValueError, match="Consistency check flag real_collection_approved is True, expected False"):
        validate_reports("V1.56.1")

def test_validator_rejects_missing_required_fields_mismatch(mock_reports_dir, monkeypatch):
    monkeypatch.chdir(mock_reports_dir)
    consist_path = mock_reports_dir / "reports" / "research" / "microstructure_contract_approval_consistency_check_v1_56_1.json"
    consist = json.loads(consist_path.read_text())
    consist["missing_required_fields"] = 0
    consist_path.write_text(json.dumps(consist))
    
    with pytest.raises(ValueError, match="Consistency check flag missing_required_fields is 0, expected 8"):
        validate_reports("V1.56.1")
