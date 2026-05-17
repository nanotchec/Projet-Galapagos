import json
import subprocess
from pathlib import Path
import pytest
import sys

def get_root_dir():
    # tests/research/test_...py -> tests/research -> tests -> root
    return Path(__file__).resolve().parent.parent.parent

def run_validator(version, root_dir):
    cmd = [
        sys.executable,
        str(root_dir / "scripts/validate_microstructure_pending_tiny_preflight_reports.py"),
        "--version",
        version
    ]
    # We pass PYTHONPATH to ensure scripts can import from src
    env = dict(subprocess.os.environ)
    env["PYTHONPATH"] = str(root_dir)
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(root_dir), env=env)

@pytest.fixture
def mock_env(tmp_path):
    # Create a portable mock environment
    reports_dir = tmp_path / "reports"
    research_dir = reports_dir / "research"
    current_dir = reports_dir / "current"
    docs_dir = tmp_path / "docs"
    
    research_dir.mkdir(parents=True)
    current_dir.mkdir(parents=True)
    docs_dir.mkdir(parents=True)
    
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    
    # Copy validator to scripts_dir (from real project)
    root_dir = get_root_dir()
    orig_validator = root_dir / "scripts/validate_microstructure_pending_tiny_preflight_reports.py"
    if not orig_validator.exists():
        # Fallback if running in a different structure
        orig_validator = Path("scripts/validate_microstructure_pending_tiny_preflight_reports.py")
        
    with open(orig_validator) as f:
        with open(scripts_dir / "validate_microstructure_pending_tiny_preflight_reports.py", "w") as f2:
            f2.write(f.read())
            
    version = "v1.69.5"
    v_norm = "v1_69_5"
    
    base_data = {
        "version": version.upper(),
        "current_version": version.upper(),
        "previous_version": "V1.69.4",
        "previous_base": "V1.69.4",
        "path_portability_hardened": True,
        "scanned_patterns_redacted": True,
        "machine_specific_paths_scan_command_label": "MACHINE_SPECIFIC_PATH_SCAN_REDACTED",
        "final_verdict": "MICROSTRUCTURE_TINY_NETWORK_PREFLIGHT_COMMAND_PREPARED_PENDING_APPROVAL",
        "recommended_next_step": "provide exact approval phrase only if you want one-request network preflight",
        "next_allowed_phase": "provide_explicit_human_approval_phrase_for_one_request_preflight",
        "evidence_classification": "INFRASTRUCTURE_ONLY",
        "consistency_check_status": "MICROSTRUCTURE_PENDING_TINY_PREFLIGHT_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY",
        "verdict_alignment_status": "PENDING_TINY_PREFLIGHT_VERDICT_ALIGNED",
        "human_approval_granted": False,
        "approval_phrase_provided": False,
        "approval_phrase_not_provided": True,
        "approval_phrase_validated": False,
        "approval_phrase_required": True,
        "required_approval_phrase": "I explicitly approve a one-request tiny network preflight with no data directory writes and no trading.",
        "pending_human_approval_mode": True,
        "pending_human_approval_mode_ready": True,
        "tiny_network_preflight_command_prepared": True,
        "tiny_network_preflight_command_executed": False,
        "tiny_network_preflight_runner_blocked_without_approval": True,
        "blocked_runner_test_passed": True,
        "no_network_runtime_assertions_passed": True,
        "no_write_runtime_assertions_passed": True,
        "future_execution_protocol_defined": True,
        "network_enabled": False,
        "network_disabled": True,
        "future_network_activation_requires_separate_approval": True,
        "requests_executed_count": 0,
        "external_api_called": False,
        "external_data_downloaded": False,
        "tiny_network_collection_executed": False,
        "controlled_collection_executed": False,
        "real_collection_executed": False,
        "real_collection_approved": False,
        "real_collection_approval_status": "NOT_APPROVED",
        "new_data_files_created": False,
        "no_data_directory_writes": True,
        "data_directory_writes_allowed": False,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "jsonl_created": False,
        "db_created": False,
        "trading_allowed": False,
        "strategy_link_allowed": False,
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "real_orders_possible": False,
        "validator_hardened": True,
        "negative_tests_added": True,
        "negative_tests_passed": True,
        "absolute_paths_removed_from_repo": True,
        "external_validation_hardened": True,
        "machine_specific_paths_scan_passed": True,
        "audit_zip_version_inference_fixed": True,
        "audit_zip_infers_v1_69_5": True,
        "audit_zip_no_v1_12_2_fallback": True,
        "path_portability_hardened": True,
        "scanned_patterns_redacted": True,
        "machine_specific_paths_scan_command_label": "MACHINE_SPECIFIC_PATH_SCAN_REDACTED",
        "reports_grep_results_removed": True,
        "report_index_paths_are_relative": True,
        "smoke_reports_paths_are_portable": True,
        "release_reports_paths_are_portable": True,
        "audit_reports_paths_are_portable": True,
        "validator_passes_in_clean_extraction": True,
        "audit_passes_in_clean_extraction": True,
        "smoke_passes_in_clean_extraction": True,
        "portable_tests_passed": True,
        "absolute_paths_removed_from_tests": True,
        "structure_hardened": True,
        "expected_modules_present": True,
        "missing_expected_modules": [],
        "package_init_present": True,
        "release_report_final": True,
        "preliminary_release_report_absent": True,
        "max_request_count": 1,
        "output_scope": "reports_only",
        "project_state_verdict_aligned": True,
        "latest_metrics_verdict_aligned": True,
        "recommendation_verdict_aligned": True,
        "project_state_aligned": True,
        "latest_metrics_aligned": True,
        "latest_summary_aligned": True,
        "all_json_values_finite": True,
        "all_json_files_parseable": True,
        "invalid_json_files": [],
        "required_reports_present": True,
        "required_markdown_reports_present": True,
        "safety_flags_aligned": True,
        "recommendation_aligned": True,
        "release_reports_present": True,
        "issues": []
    }
    
    # Write files
    with open(research_dir / f"microstructure_pending_tiny_preflight_summary_{v_norm}.json", "w") as f:
        json.dump(base_data, f)
    with open(reports_dir / "PROJECT_STATE.json", "w") as f:
        json.dump(base_data, f)
    with open(current_dir / "latest_metrics.json", "w") as f:
        json.dump(base_data, f)
    with open(research_dir / f"{v_norm}_recommendation.json", "w") as f:
        json.dump(base_data, f)
        
    # Write empty MD for all required
    required_stems = [
        "microstructure_pending_tiny_preflight_input_guard",
        "microstructure_approval_phrase_gate",
        "microstructure_pending_approval_mode",
        "microstructure_tiny_preflight_command_builder",
        "microstructure_blocked_runner",
        "microstructure_no_network_runtime_assertions",
        "microstructure_no_write_runtime_assertions",
        "microstructure_future_execution_protocol",
        "microstructure_pending_tiny_preflight_structure_audit",
        "microstructure_pending_tiny_preflight_negative_tests",
        "microstructure_pending_tiny_preflight_validator_hardening",
        "microstructure_pending_tiny_preflight_external_validation_audit",
        "microstructure_pending_tiny_preflight_decision",
        "microstructure_pending_tiny_preflight_path_portability_audit",
        "microstructure_pending_tiny_preflight_recommendation",
        "microstructure_pending_tiny_preflight_summary",
        "microstructure_pending_tiny_preflight_consistency_check"
    ]
    for stem in required_stems:
        p = research_dir / f"{stem}_{v_norm}.json"
        if not p.exists():
            with open(p, "w") as f:
                f.write("{}")
        (research_dir / f"{stem}_{v_norm}.md").touch()
        if stem == "microstructure_pending_tiny_preflight_path_portability_audit":
             with open(research_dir / f"{stem}_{v_norm}.json", "w") as f:
                json.dump({
                    "machine_specific_paths_scan_command_label": "MACHINE_SPECIFIC_PATH_SCAN_REDACTED",
                    "scanned_patterns_redacted": True
                }, f)
        if stem == "microstructure_pending_tiny_preflight_consistency_check":
             with open(research_dir / f"{stem}_{v_norm}.json", "w") as f:
                json.dump(base_data, f)

    (docs_dir / f"microstructure_pending_tiny_preflight_{v_norm}.md").touch()

    # Create dummy release reports to satisfy validator
    (reports_dir / f"release_zip_{v_norm}.json").touch()
    with open(reports_dir / f"release_zip_{v_norm}.json", "w") as f:
        json.dump({
            "version": version.upper(),
            "release_ready_for_external_review": True,
            "final_audit_passed": True,
            "final_smoke_passed": True,
            "final_consistency_passed": True,
            "final_missing_required_files": [],
            "final_forbidden_count": 0,
            "final_secret_hits": []
        }, f)

    return tmp_path, version, v_norm, base_data

def test_validator_success_portable(mock_env):
    root_dir, version, v_norm, base_data = mock_env
    res = run_validator(version, root_dir)
    assert res.returncode == 0
    assert "SUCCESS" in res.stdout

def test_reject_approval_granted_portable(mock_env):
    root_dir, version, v_norm, base_data = mock_env
    data = base_data.copy()
    data["human_approval_granted"] = True
    
    # Sync all 4 pivots
    for p in [
        root_dir / f"reports/research/microstructure_pending_tiny_preflight_summary_{v_norm}.json",
        root_dir / "reports/PROJECT_STATE.json",
        root_dir / "reports/current/latest_metrics.json",
        root_dir / f"reports/research/{v_norm}_recommendation.json"
    ]:
        with open(p, "w") as f:
            json.dump(data, f)

    res = run_validator(version, root_dir)
    assert res.returncode != 0
    assert "human_approval_granted must be False" in res.stdout

def test_reject_network_enabled_portable(mock_env):
    root_dir, version, v_norm, base_data = mock_env
    data = base_data.copy()
    data["network_enabled"] = True
    
    for p in [
        root_dir / f"reports/research/microstructure_pending_tiny_preflight_summary_{v_norm}.json",
        root_dir / "reports/PROJECT_STATE.json",
        root_dir / "reports/current/latest_metrics.json",
        root_dir / f"reports/research/{v_norm}_recommendation.json"
    ]:
        with open(p, "w") as f:
            json.dump(data, f)
    
    res = run_validator(version, root_dir)
    assert res.returncode != 0
    assert "network_enabled must be False" in res.stdout

def test_reject_forbidden_verdict_portable(mock_env):
    root_dir, version, v_norm, base_data = mock_env
    data = base_data.copy()
    data["final_verdict"] = "NETWORK_ENABLED_SUCCESS"
    
    for p in [
        root_dir / f"reports/research/microstructure_pending_tiny_preflight_summary_{v_norm}.json",
        root_dir / "reports/PROJECT_STATE.json",
        root_dir / "reports/current/latest_metrics.json",
        root_dir / f"reports/research/{v_norm}_recommendation.json"
    ]:
        with open(p, "w") as f:
            json.dump(data, f)
    
    res = run_validator(version, root_dir)
    assert res.returncode != 0
    assert "Forbidden term 'NETWORK_ENABLED'" in res.stdout

def test_reject_nan_json_portable(mock_env):
    root_dir, version, v_norm, base_data = mock_env
    summary_path = root_dir / f"reports/research/microstructure_pending_tiny_preflight_summary_{v_norm}.json"
    with open(summary_path, "w") as f:
        f.write('{"version": "V1.69.2", "value": NaN}')
    
    res = run_validator(version, root_dir)
    assert res.returncode != 0
    assert "Forbidden term 'NaN'" in res.stdout
