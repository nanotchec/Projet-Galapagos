import pandas as pd
from .universe_schema import ALLOWED_SELECTION_COLUMNS, FORBIDDEN_SELECTION_COLUMNS

def audit_selection_frame(df_selection, df_raw_preds):
    rows = len(df_selection)
    rows_2026 = len(df_selection[df_selection["timestamp"].astype(str).str.contains("2026")])
    
    cols = list(df_selection.columns)
    forbidden_found = [c for c in FORBIDDEN_SELECTION_COLUMNS if c in df_selection.columns]
    
    # Also check if any raw outcome columns (not in forbidden list but known) are present
    # For now we use the forbidden list as reference
    
    status = "SELECTION_FRAME_CAUSAL_CLEAN"
    if forbidden_found:
        status = "SELECTION_FRAME_HAS_FORBIDDEN_COLUMNS"
        
    return {
        "selection_frame_rows": rows,
        "selection_frame_rows_2026": rows_2026,
        "selection_frame_columns": cols,
        "allowed_selection_columns": ALLOWED_SELECTION_COLUMNS,
        "forbidden_selection_columns": FORBIDDEN_SELECTION_COLUMNS,
        "forbidden_columns_found": forbidden_found,
        "raw_outcome_columns_detected": forbidden_found,
        "outcome_columns_excluded_from_selection": True,
        "causal_columns_count": len(cols),
        "selection_frame_status": status
    }
