def classify_non_reproducibility(analysis_results, code_inspection, artifact_audit):
    if analysis_results["any_exact_source_match"]:
        return {
            "status": "REPRODUCIBLE",
            "driver": "NONE"
        }
        
    drivers = []
    
    # Primary driver: Artifacts are insufficient to discriminate or recover the path
    if artifact_audit["status"] != "SOURCE_ARTIFACTS_FULLY_RECONSTRUCTABLE":
        primary_driver = "SOURCE_ARTIFACTS_INSUFFICIENT"
        drivers.append("HISTORICAL_EV_SELECTION_PATH_NOT_SERIALIZED")
    else:
        primary_driver = "UNKNOWN_HISTORICAL_SELECTION_POLICY"
        
    if "warmup_policy_addition" in code_inspection["potential_count_affecting_changes"]:
        drivers.append("UNKNOWN_HISTORICAL_WARMUP_POLICY")
    if "join_policy_modification" in code_inspection["potential_count_affecting_changes"]:
        drivers.append("UNKNOWN_HISTORICAL_JOIN_POLICY")
        
    return {
        "status": "SOURCE_PATH_NOT_RECOVERED_FROM_AVAILABLE_ARTIFACTS",
        "primary_non_reproducibility_driver": primary_driver,
        "secondary_drivers": drivers,
        "recommended_canonical_base": "V1.34.1_REBUILD"
    }
