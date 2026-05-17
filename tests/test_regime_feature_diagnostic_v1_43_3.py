import json
from pathlib import Path
import sys
import pytest

# Mock bootstrap
def mock_bootstrap():
    sys.path.append('scripts')

mock_bootstrap()
from validate_regime_feature_diagnostic_reports import validate_reports

def setup_mock_reports(tmp_path, version="v1.43.3"):
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
        f"regime_feature_consistency_check_{version_norm}.json",
        f"{version_norm}_recommendation.json"
    ]
    
    for r in required:
        if "scorecard" in r:
            (research_dir / r).write_text(json.dumps({
                "model_outputs_excluded_from_raw_feature_recommendations": True,
                "ev_proxies_excluded_from_raw_feature_recommendations": True,
                "recommended_raw_feature_families_for_v1_44": ["volatility"]
            }))
        elif "inventory" in r:
            (research_dir / r).write_text(json.dumps({
                "raw_market_features": ["open", "high"],
                "metadata_features": ["model_name"],
                "model_output_features": ["predicted_probability"],
                "ev_proxy_features": ["ev_calibrated_proxy"],
                "outcome_forbidden_features": ["forward_return"],
                "raw_market_feature_count": 2,
                "metadata_feature_count": 1,
                "model_output_feature_count": 1,
                "ev_proxy_feature_count": 1
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
        "final_verdict": "REGIME_FEATURE_FAILURE_DRIVER_IDENTIFIED"
    }
    (research_dir / f"regime_feature_diagnostic_summary_{version_norm}.json").write_text(json.dumps(summary))
    
    ps = {
        "version": version.upper(),
        "payoff_target_base_version": "V1.42.3",
        "canonical_base_version": "V1.37.2",
        "purpose": "Regime-aware feature failure diagnostic",
        "consistency_check_status": "REGIME_FEATURE_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY",
        "model_outputs_separated_from_raw_features": True,
        "ev_proxies_separated_from_raw_features": True,
        "legacy_context": {}
    }
    (tmp_path / "reports" / "PROJECT_STATE.json").write_text(json.dumps(ps))
    
    lm = {
        "consistency_check_status": "REGIME_FEATURE_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY"
    }
    (current_dir / "latest_metrics.json").write_text(json.dumps(lm))
    
    return research_dir

def test_validator_rejects_metadata_in_raw(tmp_path, monkeypatch):
    setup_mock_reports(tmp_path)
    inv_file = tmp_path / "reports" / "research" / "regime_feature_inventory_v1_43_3.json"
    data = json.loads(inv_file.read_text())
    data["raw_market_features"].append("model_name")
    inv_file.write_text(json.dumps(data))
    
    monkeypatch.chdir(tmp_path)
    assert validate_reports("v1.43.3") is False

def test_validator_rejects_model_output_in_raw(tmp_path, monkeypatch):
    setup_mock_reports(tmp_path)
    inv_file = tmp_path / "reports" / "research" / "regime_feature_inventory_v1_43_3.json"
    data = json.loads(inv_file.read_text())
    data["raw_market_features"].append("predicted_probability")
    inv_file.write_text(json.dumps(data))
    
    monkeypatch.chdir(tmp_path)
    assert validate_reports("v1.43.3") is False

def test_validator_rejects_proxy_in_raw(tmp_path, monkeypatch):
    setup_mock_reports(tmp_path)
    inv_file = tmp_path / "reports" / "research" / "regime_feature_inventory_v1_43_3.json"
    data = json.loads(inv_file.read_text())
    data["raw_market_features"].append("cost_proxy")
    inv_file.write_text(json.dumps(data))
    
    monkeypatch.chdir(tmp_path)
    assert validate_reports("v1.43.3") is False

def test_validator_rejects_forbidden_rec_family(tmp_path, monkeypatch):
    setup_mock_reports(tmp_path)
    sc_file = tmp_path / "reports" / "research" / "regime_feature_stability_scorecard_v1_43_3.json"
    data = json.loads(sc_file.read_text())
    data["recommended_raw_feature_families_for_v1_44"].append("alpha_score_or_model_output")
    sc_file.write_text(json.dumps(data))
    
    monkeypatch.chdir(tmp_path)
    assert validate_reports("v1.43.3") is False

def test_validator_accepts_valid_v1_43_3(tmp_path, monkeypatch):
    setup_mock_reports(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert validate_reports("v1.43.3") is True
