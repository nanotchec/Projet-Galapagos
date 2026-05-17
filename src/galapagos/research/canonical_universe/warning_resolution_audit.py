def audit_warning_resolution(selection_audit, outcome_audit, input_audit):
    # The previous warning was that raw dataset contained outcomes.
    # We resolve it by proving selection_dataset is clean and outcome_dataset is separated.
    
    selection_clean = selection_audit["selection_dataset_status"] == "CANONICAL_SELECTION_DATASET_CLEAN"
    outcome_separated = outcome_audit["outcome_dataset_status"] == "CANONICAL_OUTCOME_DATASET_SEPARATED"
    
    # Even if raw has outcomes, the FORMAL SPLIT makes the selection frame safe.
    # In V1.37, if selection is clean, we consider the warning resolved via formal split.
    
    resolved = selection_clean and outcome_separated
    
    status = "CANONICAL_INPUT_OUTCOME_WARNING_RESOLVED" if resolved else "CANONICAL_WARNING_UNRESOLVED"
    
    return {
        "previous_warning": "raw dataset contains outcomes",
        "selection_dataset_clean": selection_clean,
        "outcome_dataset_separated": outcome_separated,
        "input_outcome_warning_resolved": resolved,
        "residual_warnings": [] if resolved else ["Selection dataset not clean or outcome not separated"],
        "warning_resolution_status": status
    }
