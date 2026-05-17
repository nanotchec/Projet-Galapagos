import json
from pathlib import Path
import sys
import pytest

# Mock bootstrap
def mock_bootstrap():
    sys.path.append('scripts')

mock_bootstrap()
from validate_regime_feature_diagnostic_reports import validate_reports

def setup_mock_reports(tmp_path, version="v1.43.2"):
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
        if "scorecard" in r:
            (research_dir / r).write_text(json.dumps({
                "model_outputs_excluded_from_raw_feature_recommendations": True,
                "recommended_raw_feature_families_for_v1_44": ["volatility"]
            }))
        elif "inventory" in r:
            (research_dir / r).write_text(json.dumps({
                "usable_raw_features": [],
                "model_output_features": [],
                "model_output_feature_count": 0
            }))
        else:
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
        "payoff_target_base_version": "V1.42.3",
        "canonical_base_version": "V1.37.2",
        "purpose": "Regime-aware feature failure diagnostic",
        "consistency_check_status": "REGIME_FEATURE_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY",
        "legacy_context": {}
    }
    (tmp_path / "reports" / "PROJECT_STATE.json").write_text(json.dumps(ps))
    
    lm = {
        "consistency_check_status": "REGIME_FEATURE_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY"
    }
    (current_dir / "latest_metrics.json").write_text(json.dumps(lm))
    
    return research_dir, summary

def test_validator_rejects_null_canonical_base(tmp_path, monkeypatch):
    setup_mock_reports(tmp_path)
    ps_path = tmp_path / "reports" / "PROJECT_STATE.json"
    ps = json.loads(ps_path.read_text())
    ps["canonical_base_version"] = None
    ps_path.write_text(json.dumps(ps))
    
    monkeypatch.chdir(tmp_path)
    assert validate_reports("v1.43.2") is False

def test_validator_rejects_wrong_canonical_base(tmp_path, monkeypatch):
    setup_mock_reports(tmp_path)
    ps_path = tmp_path / "reports" / "PROJECT_STATE.json"
    ps = json.loads(ps_path.read_text())
    ps["canonical_base_version"] = "V1.37.1"
    ps_path.write_text(json.dumps(ps))
    
    monkeypatch.chdir(tmp_path)
    assert validate_reports("v1.43.2") is False

def test_validator_rejects_legacy_root_fields(tmp_path, monkeypatch):
    setup_mock_reports(tmp_path)
    ps_path = tmp_path / "reports" / "PROJECT_STATE.json"
    ps = json.loads(ps_path.read_text())
    ps["best_target_observed"] = "some_target"
    ps_path.write_text(json.dumps(ps))
    
    monkeypatch.chdir(tmp_path)
    assert validate_reports("v1.43.2") is False

def test_validator_rejects_model_outputs_in_raw_features(tmp_path, monkeypatch):
    setup_mock_reports(tmp_path)
    inv_file = tmp_path / "reports" / "research" / "regime_feature_inventory_v1_43_2.json"
    inv_file.write_text(json.dumps({
        "usable_raw_features": ["predicted_probability"],
        "model_output_features": ["predicted_probability"],
        "model_output_feature_count": 1
    }))
    
    monkeypatch.chdir(tmp_path)
    assert validate_reports("v1.43.2") is False

def test_validator_accepts_valid_v1_43_2(tmp_path, monkeypatch):
    setup_mock_reports(tmp_path)
    inv_file = tmp_path / "reports" / "research" / "regime_feature_inventory_v1_43_2.json"
    inv_file.write_text(json.dumps({
        "usable_raw_features": ["ohlc_vol"],
        "model_output_features": ["predicted_probability"],
        "model_output_feature_count": 1
    }))
    
    monkeypatch.chdir(tmp_path)
    assert validate_reports("v1.43.2") is True
