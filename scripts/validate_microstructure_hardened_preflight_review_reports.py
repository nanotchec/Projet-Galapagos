import json
import argparse
from pathlib import Path

def validate_hardened_review(version: str):
    v_suffix = version.lower().replace(".", "_")
    reports_dir = Path("reports/research")
    
    # 1. Required Reports
    stems = [
        "microstructure_hardened_preflight_review_input_guard",
        "microstructure_hardened_preflight_evidence_review",
        "microstructure_hardened_preflight_action_review",
        "microstructure_hardened_preflight_residual_risk_review",
        "microstructure_hardened_preflight_boundary_review",
        "microstructure_hardened_preflight_decision",
        "microstructure_hardened_preflight_next_phase_policy",
        "microstructure_hardened_preflight_recommendation",
        "microstructure_hardened_preflight_review_summary",
        "microstructure_hardened_preflight_review_consistency_check"
    ]
    
    for stem in stems:
        p_json = reports_dir / f"{stem}_{v_suffix}.json"
        p_md = reports_dir / f"{stem}_{v_suffix}.md"
        if not p_json.exists(): raise FileNotFoundError(f"Missing {p_json}")
        if not p_md.exists(): raise FileNotFoundError(f"Missing {p_md}")

    rec_json_name = f"{v_suffix}_recommendation.json"
    rec_md_name = f"{v_suffix}_recommendation.md"
    if not (reports_dir / rec_json_name).exists(): raise FileNotFoundError(f"Missing {rec_json_name}")
    if not (reports_dir / rec_md_name).exists(): raise FileNotFoundError(f"Missing {rec_md_name}")
    
    if not Path(f"docs/microstructure_hardened_preflight_review_{v_suffix}.md").exists():
        raise FileNotFoundError(f"Missing docs/microstructure_hardened_preflight_review_{v_suffix}.md")

    # 2. Alignment Check
    summary_path = reports_dir / f"microstructure_hardened_preflight_review_summary_{v_suffix}.json"
    cc_path = reports_dir / f"microstructure_hardened_preflight_review_consistency_check_{v_suffix}.json"
    rec_path = reports_dir / rec_json_name
    state_path = Path("reports/PROJECT_STATE.json")
    metrics_path = Path("reports/current/latest_metrics.json")
    
    with open(summary_path, "r") as f: summary = json.load(f)
    with open(cc_path, "r") as f: cc = json.load(f)
    with open(rec_path, "r") as f: rec = json.load(f)
    with open(state_path, "r") as f: state = json.load(f)
    with open(metrics_path, "r") as f: metrics = json.load(f)

    # Version hierarchy
    if version == "V1.62.1":
        prev_v = "V1.62"
    else:
        prev_v = "V1.61"

    for doc_name, doc in [("summary", summary), ("consistency_check", cc), ("recommendation", rec), ("state", state), ("metrics", metrics)]:
        if doc.get("version") != version:
            raise ValueError(f"version mismatch in {doc_name}: {doc.get('version')} vs {version}")
        
        if doc.get("previous_version") != prev_v and doc.get("previous_base") != prev_v:
             if doc_name != "summary": # Summary might have more complex lineage
                raise ValueError(f"previous_version mismatch in {doc_name}: {doc.get('previous_version')} vs {prev_v}")

        if doc.get("final_verdict") != summary.get("final_verdict"):
            raise ValueError(f"final_verdict mismatch in {doc_name}: {doc.get('final_verdict')} vs {summary.get('final_verdict')}")
        if doc.get("hardened_preflight_review_passed") != summary.get("hardened_preflight_review_passed"):
            raise ValueError(f"hardened_preflight_review_passed mismatch in {doc_name}")
        if doc.get("recommended_next_step") != summary.get("recommended_next_step"):
            raise ValueError(f"recommended_next_step mismatch in {doc_name}")
        if doc.get("next_allowed_phase") != summary.get("next_allowed_phase"):
            raise ValueError(f"next_allowed_phase mismatch in {doc_name}")
        
        # Security verifications
        if doc.get("network_enabled") is not False: raise ValueError(f"network_enabled MUST be False in {doc_name}")
        if doc.get("real_collection_approved") is not False: raise ValueError(f"real_collection_approved MUST be False in {doc_name}")
        if doc.get("real_collection_executed") is True: raise ValueError(f"real_collection_executed MUST be False in {doc_name}")
        if doc.get("requests_executed_count", 0) != 0: raise ValueError(f"requests_executed_count MUST be 0 in {doc_name}")

        # Phase alignment (V1.62.1 Specific Hardening)
        if doc.get("controlled_local_preflight_executed") is True:
             raise ValueError(f"controlled_local_preflight_executed MUST be False in {doc_name} for review phase")
        if doc.get("previous_preflight_dryrun_passed") is False:
             raise ValueError(f"previous_preflight_dryrun_passed MUST be True in {doc_name}")
        if doc.get("hardened_preflight_review_only") is not True:
             raise ValueError(f"hardened_preflight_review_only MUST be True in {doc_name}")
        if doc.get("review_executed") is not True:
             raise ValueError(f"review_executed MUST be True in {doc_name}")

        # Review fields (V1.62.1 Specific Hardening)
        review_fields = [
            "manifest_preview_reviewed",
            "timestamp_causality_reviewed",
            "no_lookahead_reviewed",
            "stop_conditions_reviewed",
            "cleanup_reviewed"
        ]
        for field in review_fields:
            if doc.get(field) is not True:
                raise ValueError(f"Missing or False review field {field} in {doc_name}")

    if cc.get("verdict_alignment_status") != "HARDENED_PREFLIGHT_REVIEW_VERDICT_ALIGNED":
         raise ValueError(f"Invalid verdict_alignment_status: {cc.get('verdict_alignment_status')}")
    
    if state.get("verdict_alignment_status") != "HARDENED_PREFLIGHT_REVIEW_VERDICT_ALIGNED":
         raise ValueError(f"State verdict_alignment_status mismatch")

    print(f"Validation for {version} PASSED.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="V1.62.1")
    args = parser.parse_args()
    validate_hardened_review(args.version)
