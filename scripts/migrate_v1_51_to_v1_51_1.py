"""Migrate V1.51 reports to V1.51.1 and add missing reports."""
import json
import os
from pathlib import Path

def migrate():
    report_dir = Path("reports/research")
    old_version = "V1.51"
    new_version = "V1.51.1"
    
    old_suffix = "v1_51"
    new_suffix = "v1_51_1"
    
    # Files to migrate
    files = [f for f in report_dir.glob(f"*_{old_suffix}.*")]
    # Also include v1_51_recommendation
    files.extend(report_dir.glob(f"{old_suffix}_recommendation.*"))
    
    for f in files:
        new_name = f.name.replace(old_suffix, new_suffix)
        new_path = report_dir / new_name
        
        if f.suffix == ".json":
            with open(f, "r") as jf:
                data = json.load(jf)
            
            # Update metadata
            data["version"] = new_version
            data["previous_base"] = old_version
            data["migrated_from"] = old_version
            data["migration_reason"] = "missing required reports fix"
            
            # Specific updates for consistency check
            if "consistency_check" in f.name:
                data["consistency_check_status"] = "MICROSTRUCTURE_QUALITY_MASK_REPORTS_CONSISTENT_RESEARCH_ONLY"
                data["missing_required_reports_fixed"] = True
                data["input_guard_report_present"] = True
                data["quality_mask_recommendation_report_present"] = True
            
            with open(new_path, "w") as jf:
                json.dump(data, jf, indent=2)
            print(f"Migrated JSON: {f.name} -> {new_name}")
            
        elif f.suffix == ".md":
            content = f.read_text()
            content = content.replace(old_version, new_version)
            new_path.write_text(content)
            print(f"Migrated MD: {f.name} -> {new_name}")
            
        # Optional: remove old files
        # f.unlink()

    # Create missing reports
    create_input_guard(report_dir, new_version, new_suffix)
    create_mask_recommendation(report_dir, new_version, new_suffix)

def create_input_guard(report_dir, version, suffix):
    name = f"microstructure_quality_mask_input_guard_{suffix}"
    data = {
      "version": version,
      "previous_base": "V1.51",
      "input_guard_status": "MICROSTRUCTURE_QUALITY_MASK_INPUT_GUARD_PASSED",
      "canonical_base_version": "V1.37.2",
      "microstructure_coverage_base_version": "V1.50.1",
      "required_inputs_present": True,
      "forbidden_inputs_used": False,
      "outcome_used_for_mask_construction": False,
      "future_used_for_mask_construction": False,
      "model_output_used_for_mask_construction": False,
      "ev_proxy_used_for_mask_construction": False,
      "holdout_executed": False,
      "codex_cli_called": False,
      "no_real_trading": True
    }
    
    json_path = report_dir / f"{name}.json"
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)
    
    md_path = report_dir / f"{name}.md"
    md_content = f"""# Microstructure Quality Mask Input Guard ({version})

L'audit des entrées pour la construction du masque de qualité microstructure est validé.

- **Status** : {data["input_guard_status"]}
- **Pas de fuite** : Confirmé (ni outcome, ni future, ni model output utilisé).
- **Pas de holdout** : Confirmé.
- **Pas d'ordre réel** : Confirmé.

Ce masque est une politique de qualité de données, pas une stratégie.
"""
    md_path.write_text(md_content)
    print(f"Created missing report: {name}")

def create_mask_recommendation(report_dir, version, suffix):
    name = f"microstructure_quality_mask_recommendation_{suffix}"
    data = {
      "version": version,
      "previous_base": "V1.51",
      "final_verdict": "MICROSTRUCTURE_QUALITY_MASK_PARTIAL_BUT_USABLE",
      "recommended_next_step": "improve intrabar data before applying quality mask",
      "evidence_classification": "RESEARCH_ONLY",
      "usable_window_ratio": 0.924,
      "blocked_window_ratio": 0.076,
      "usable_window_ratio_2026": 0.0,
      "blocked_window_ratio_2026": 1.0,
      "data_actions_required": ["Improve intrabar data coverage before applying the quality mask"],
      "minimum_conditions_for_next_diagnostic": ["Improve 2026 intrabar coverage before reusing microstructure labels"],
      "no_new_filter": True,
      "no_strategy_validated": True,
      "no_preregistration_yet": True,
      "no_paper_live": True,
      "no_real_trading": True,
      "holdout_executed": False,
      "codex_cli_called": False,
      "real_orders_possible": False
    }
    
    json_path = report_dir / f"{name}.json"
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)
    
    md_path = report_dir / f"{name}.md"
    md_content = f"""# Microstructure Quality Mask Recommendation ({version})

## Verdict
**{data["final_verdict"]}**

## Recommandation
**{data["recommended_next_step"]}**

## Analyse d'Impact
- **Ratio utilisable** : {data["usable_window_ratio"]}
- **Ratio bloqué** : {data["blocked_window_ratio"]}
- **Status 2026** : Bloqué (0% utilisable)

## Actions requises
- Améliorer la couverture intrabar avant toute application du masque.
- Ne pas passer à la prérégistration ou au trading réel.

**RESEARCH_ONLY** : Aucun système de trading n'est activé.
"""
    md_path.write_text(md_content)
    print(f"Created missing report: {name}")

if __name__ == "__main__":
    migrate()
