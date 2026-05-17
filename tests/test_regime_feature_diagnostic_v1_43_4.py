import pytest
import json
from pathlib import Path
from scripts.validate_regime_feature_diagnostic_reports import validate_reports

def test_v1_43_4_validator_semantics(tmp_path):
    """Test that the validator correctly rejects forbidden families and count mismatches in V1.43.4."""
    version = "v1.43.4"
    version_norm = "v1_43_4"
    reports_dir = Path("reports/research")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Create a summary that should fail (forbidden family in recommendations)
    summary_path = reports_dir / f"regime_feature_diagnostic_summary_{version_norm}.json"
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
        "input_guard_status": "REGIME_FEATURE_INPUT_GUARD_PASSED"
    }
    summary_path.write_text(json.dumps(summary))
    
    # 2. Create scorecard with forbidden family
    sc_path = reports_dir / f"regime_feature_stability_scorecard_{version_norm}.json"
    sc = {
        "recommended_raw_feature_families_for_v1_44": ["alpha_score_or_model_output"],
        "recommended_alpha_feature_families_for_v1_44": ["model_output_family"],
        "model_outputs_excluded_from_raw_feature_recommendations": True,
        "ev_proxies_excluded_from_raw_feature_recommendations": True,
        "alpha_score_or_model_output_removed": True
    }
    sc_path.write_text(json.dumps(sc))
    
    # 3. Create inventory with count mismatch
    inv_path = reports_dir / f"regime_feature_inventory_{version_norm}.json"
    inv = {
        "usable_raw_features": ["feat1"],
        "usable_raw_feature_count": 2, # Mismatch
        "diagnostic_only_model_output_features": [],
        "model_output_feature_count": 1 # Mismatch
    }
    inv_path.write_text(json.dumps(inv))
    
    # All other required reports (placeholders)
    required = [
        f"regime_feature_input_guard_{version_norm}.json",
        f"regime_feature_shift_analysis_{version_norm}.json",
        f"regime_feature_predictive_power_{version_norm}.json",
        f"regime_definition_audit_{version_norm}.json",
        f"regime_coverage_analysis_{version_norm}.json",
        f"regime_feature_interaction_{version_norm}.json",
        f"regime_feature_2026_failure_slice_{version_norm}.json",
        f"regime_feature_state_alignment_{version_norm}.json",
        f"regime_feature_consistency_check_{version_norm}.json",
        f"{version_norm}_recommendation.json"
    ]
    for r in required:
        (reports_dir / r).write_text(json.dumps({"status": "OK"}))

    # Validator should fail
    assert validate_reports(version) is False
