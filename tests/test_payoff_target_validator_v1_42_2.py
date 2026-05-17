import json
from pathlib import Path
import sys
import pytest
sys.path.append('scripts')
from validate_payoff_target_research_reports import validate_reports

def test_validator_rejects_short_consistency_status(tmp_path, monkeypatch):
    research_dir = tmp_path / "reports" / "research"
    research_dir.mkdir(parents=True)
    current_dir = tmp_path / "reports" / "current"
    current_dir.mkdir(parents=True)
    
    version = "v1.42.3"
    version_norm = "v1_42_3"
    
    summary = {
        "version": "V1.42.3",
        "failure_diagnostic_base": "V1.41",
        "payoff_objective_base_version": "V1.40.1",
        "diagnostic_base": "V1.39",
        "canonical_base_version": "V1.37.2",
        "evidence_classification": "EXPLORATORY_ONLY",
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "final_verdict": "PAYOFF_TARGET_RESEARCH_RECENT_WINDOW_WEAK",
        "best_target_observed": None,
        "beats_v1_40_1_target": False,
        "json_finiteness_status": "PAYOFF_TARGET_JSON_FINITE_PASSED"
    }
    
    summary_file = research_dir / f"payoff_target_research_summary_{version_norm}.json"
    summary_file.write_text(json.dumps(summary))
    
    # PROJECT_STATE with short status
    ps_file = tmp_path / "reports" / "PROJECT_STATE.json"
    ps_file.write_text(json.dumps({
        "version": "V1.42.3",
        "consistency_check_status": "PAYOFF_TARGET_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY"
    }))
    
    required = [
        f"payoff_target_input_guard_{version_norm}.json",
        f"payoff_target_count_semantics_{version_norm}.json",
        f"payoff_target_horizon_candidates_{version_norm}.json",
        f"payoff_target_definitions_{version_norm}.json",
        f"payoff_target_noise_analysis_{version_norm}.json",
        f"payoff_downside_label_analysis_{version_norm}.json",
        f"payoff_target_horizon_walk_forward_eval_{version_norm}.json",
        f"payoff_target_baseline_comparison_{version_norm}.json",
        f"payoff_target_temporal_robustness_{version_norm}.json",
        f"payoff_target_regime_breakdown_{version_norm}.json",
        f"payoff_target_overfit_guard_{version_norm}.json",
        f"payoff_target_json_finiteness_audit_{version_norm}.json",
        f"payoff_target_state_alignment_{version_norm}.json",
        f"{version_norm}_recommendation.json"
    ]
    for r in required:
        (research_dir / r).write_text("{}")
        
    monkeypatch.chdir(tmp_path)
    
    assert validate_reports(version) is False

def test_validator_accepts_valid_v1_42_3(tmp_path, monkeypatch):
    research_dir = tmp_path / "reports" / "research"
    research_dir.mkdir(parents=True)
    current_dir = tmp_path / "reports" / "current"
    current_dir.mkdir(parents=True)
    
    version = "v1.42.3"
    version_norm = "v1_42_3"
    full_status = "PAYOFF_TARGET_RESEARCH_REPORTS_CONSISTENT_STATE_ALIGNED_EXPLORATORY_ONLY"
    
    summary = {
        "version": "V1.42.3",
        "failure_diagnostic_base": "V1.41",
        "payoff_objective_base_version": "V1.40.1",
        "diagnostic_base": "V1.39",
        "canonical_base_version": "V1.37.2",
        "evidence_classification": "EXPLORATORY_ONLY",
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "final_verdict": "PAYOFF_TARGET_RESEARCH_RECENT_WINDOW_WEAK",
        "best_target_observed": None,
        "beats_v1_40_1_target": False,
        "json_finiteness_status": "PAYOFF_TARGET_JSON_FINITE_PASSED"
    }
    
    summary_file = research_dir / f"payoff_target_research_summary_{version_norm}.json"
    summary_file.write_text(json.dumps(summary))
    
    ps_file = tmp_path / "reports" / "PROJECT_STATE.json"
    ps_file.write_text(json.dumps({
        "version": "V1.42.3",
        "consistency_check_status": full_status,
        "diagnostic_base": "V1.39"
    }))
    
    lm_file = tmp_path / "reports" / "current" / "latest_metrics.json"
    lm_file.write_text(json.dumps({
        "version": "V1.42.3",
        "consistency_check_status": full_status
    }))

    required = [
        f"payoff_target_input_guard_{version_norm}.json",
        f"payoff_target_count_semantics_{version_norm}.json",
        f"payoff_target_horizon_candidates_{version_norm}.json",
        f"payoff_target_definitions_{version_norm}.json",
        f"payoff_target_noise_analysis_{version_norm}.json",
        f"payoff_downside_label_analysis_{version_norm}.json",
        f"payoff_target_horizon_walk_forward_eval_{version_norm}.json",
        f"payoff_target_baseline_comparison_{version_norm}.json",
        f"payoff_target_temporal_robustness_{version_norm}.json",
        f"payoff_target_regime_breakdown_{version_norm}.json",
        f"payoff_target_overfit_guard_{version_norm}.json",
        f"payoff_target_json_finiteness_audit_{version_norm}.json",
        f"payoff_target_state_alignment_{version_norm}.json",
        f"{version_norm}_recommendation.json"
    ]
    for r in required:
        if "walk_forward_eval" in r:
             (research_dir / r).write_text(json.dumps({
                 "raw_nan_values_remaining": 0,
                 "raw_infinity_values_remaining": 0,
                 "all_json_values_finite": True
             }))
        else:
            (research_dir / r).write_text("{}")
        
    monkeypatch.chdir(tmp_path)
    
    assert validate_reports(version) is True
