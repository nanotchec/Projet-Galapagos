import json
from pathlib import Path
import sys
import pytest

# Mock bootstrap to avoid path issues in tests
def mock_bootstrap():
    sys.path.append('scripts')

mock_bootstrap()
from validate_regime_feature_diagnostic_reports import validate_reports

def setup_mock_reports(tmp_path, version="v1.43.1"):
    version_norm = version.lower().replace(".", "_")
    research_dir = tmp_path / "reports" / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    current_dir = tmp_path / "reports" / "current"
    current_dir.mkdir(parents=True, exist_ok=True)
    
    required = [
        f"regime_feature_input_guard_{version_norm}.json",
        f"regime_feature_inventory_{version_norm}.json",
        f"regime_feature_shift_analysis_{version_norm}.json",
        f"regime_feature_predictive_power_{version_norm}.json",
        f"regime_definition_audit_{version_norm}.json",
        f"regime_coverage_analysis_{version_norm}.json",
        f"regime_feature_interaction_{version_norm}.json",
        f"regime_feature_2026_failure_slice_{version_norm}.json",
        f"regime_feature_stability_scorecard_{version_norm}.json",
        f"regime_feature_diagnostic_summary_{version_norm}.json",
        f"regime_feature_state_alignment_{version_norm}.json",
        f"{version_norm}_recommendation.json"
    ]
    
    for r in required:
        (research_dir / r).write_text("{}")
        
    summary = {
        "version": version.upper(),
        "payoff_target_base_version": "V1.42.3",
        "payoff_failure_base_version": "V1.41",
        "ev_degradation_base_version": "V1.39",
        "canonical_base_version": "V1.37.2",
        "evidence_classification": "DIAGNOSTIC_ONLY",
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "final_verdict": "REGIME_FEATURE_FAILURE_MULTI_FACTOR"
    }
    (research_dir / f"regime_feature_diagnostic_summary_{version_norm}.json").write_text(json.dumps(summary))
    
    ps = {
        "version": version.upper(),
        "purpose": "Regime-aware feature failure diagnostic",
        "consistency_check_status": "REGIME_FEATURE_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY"
    }
    (tmp_path / "reports" / "PROJECT_STATE.json").write_text(json.dumps(ps))
    
    lm = {
        "consistency_check_status": "REGIME_FEATURE_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY"
    }
    (current_dir / "latest_metrics.json").write_text(json.dumps(lm))
    
    return research_dir, summary

def test_validator_accepts_valid_v1_43_1(tmp_path, monkeypatch):
    setup_mock_reports(tmp_path)
    # Set inventory to valid state
    inv_file = tmp_path / "reports" / "research" / "regime_feature_inventory_v1_43_1.json"
    inv_file.write_text(json.dumps({
        "usable_features": ["feat_1", "feat_2"],
        "outcome_like_features_excluded": True
    }))
    
    monkeypatch.chdir(tmp_path)
    assert validate_reports("v1.43.1") is True

def test_validator_rejects_leakage_in_inventory(tmp_path, monkeypatch):
    setup_mock_reports(tmp_path)
    inv_file = tmp_path / "reports" / "research" / "regime_feature_inventory_v1_43_1.json"
    inv_file.write_text(json.dumps({
        "usable_features": ["feat_1", "max_favorable_excursion_1bar"],
        "outcome_like_features_excluded": True
    }))
    
    monkeypatch.chdir(tmp_path)
    assert validate_reports("v1.43.1") is False

def test_validator_rejects_missing_exclusion_flag(tmp_path, monkeypatch):
    setup_mock_reports(tmp_path)
    inv_file = tmp_path / "reports" / "research" / "regime_feature_inventory_v1_43_1.json"
    inv_file.write_text(json.dumps({
        "usable_features": ["feat_1"],
        "outcome_like_features_excluded": False
    }))
    
    monkeypatch.chdir(tmp_path)
    assert validate_reports("v1.43.1") is False

def test_validator_rejects_legacy_project_state_purpose(tmp_path, monkeypatch):
    setup_mock_reports(tmp_path)
    ps_path = tmp_path / "reports" / "PROJECT_STATE.json"
    ps = json.loads(ps_path.read_text())
    ps["purpose"] = "Payoff target research state alignment"
    ps_path.write_text(json.dumps(ps))
    
    # Still need valid inventory
    inv_file = tmp_path / "reports" / "research" / "regime_feature_inventory_v1_43_1.json"
    inv_file.write_text(json.dumps({"usable_features": [], "outcome_like_features_excluded": True}))
    
    monkeypatch.chdir(tmp_path)
    assert validate_reports("v1.43.1") is False

def test_validator_rejects_legacy_consistency_status(tmp_path, monkeypatch):
    setup_mock_reports(tmp_path)
    ps_path = tmp_path / "reports" / "PROJECT_STATE.json"
    ps = json.loads(ps_path.read_text())
    ps["consistency_check_status"] = "PAYOFF_TARGET_RESEARCH_REPORTS_CONSISTENT_STATE_ALIGNED_EXPLORATORY_ONLY"
    ps_path.write_text(json.dumps(ps))
    
    inv_file = tmp_path / "reports" / "research" / "regime_feature_inventory_v1_43_1.json"
    inv_file.write_text(json.dumps({"usable_features": [], "outcome_like_features_excluded": True}))
    
    monkeypatch.chdir(tmp_path)
    assert validate_reports("v1.43.1") is False

def test_validator_rejects_nan_in_reports(tmp_path, monkeypatch):
    setup_mock_reports(tmp_path)
    scorecard_path = tmp_path / "reports" / "research" / "regime_feature_stability_scorecard_v1_43_1.json"
    scorecard_path.write_text(json.dumps({"drift": float('nan')}))
    
    inv_file = tmp_path / "reports" / "research" / "regime_feature_inventory_v1_43_1.json"
    inv_file.write_text(json.dumps({"usable_features": [], "outcome_like_features_excluded": True}))
    
    monkeypatch.chdir(tmp_path)
    assert validate_reports("v1.43.1") is False

def test_validator_rejects_unsafe_classification(tmp_path, monkeypatch):
    setup_mock_reports(tmp_path)
    summary_path = tmp_path / "reports" / "research" / "regime_feature_diagnostic_summary_v1_43_1.json"
    summary = json.loads(summary_path.read_text())
    summary["evidence_classification"] = "STRATEGY_VALIDATED"
    summary_path.write_text(json.dumps(summary))
    
    inv_file = tmp_path / "reports" / "research" / "regime_feature_inventory_v1_43_1.json"
    inv_file.write_text(json.dumps({"usable_features": [], "outcome_like_features_excluded": True}))
    
    monkeypatch.chdir(tmp_path)
    assert validate_reports("v1.43.1") is False
