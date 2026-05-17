from .universe_schema import FORBIDDEN_SELECTION_COLUMNS

def audit_leakage(df_selection, df_outcome):
    # Selection frame must NOT have forbidden columns
    leaked_selection = [c for c in FORBIDDEN_SELECTION_COLUMNS if c in df_selection.columns]
    
    # Selection frame should only have causal columns (mostly)
    # This is a bit subjective but we check against Forbidden list
    
    status = "CANONICAL_UNIVERSE_NO_SELECTION_LEAKAGE"
    if leaked_selection:
        status = "CANONICAL_UNIVERSE_LEAKAGE_DETECTED"
        
    return {
        "forbidden_columns_found_in_selection": leaked_selection,
        "selection_columns_count": len(df_selection.columns),
        "outcome_columns_count": len(df_outcome.columns),
        "leakage_status": status
    }
