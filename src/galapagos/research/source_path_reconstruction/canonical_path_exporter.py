def export_canonical_path(analysis_results, hypotheses):
    if not analysis_results["any_exact_source_match"]:
        return {
            "canonical_path_status": "CANONICAL_SOURCE_PATH_NOT_RECOVERED",
            "reproducibility_status": "SOURCE_PATH_NOT_RECOVERED_FROM_AVAILABLE_ARTIFACTS"
        }
        
    best_hid = analysis_results["best_source_match_hypothesis"]
    best_h = next(h for h in hypotheses if h["id"] == best_hid)
    
    return {
        "canonical_path_status": "CANONICAL_SOURCE_PATH_RECOVERED",
        "canonical_hypothesis_id": best_hid,
        "path_definition": best_h,
        "reproducibility_status": "REPRODUCIBLE"
    }
