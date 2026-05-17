import pandas as pd
from .universe_schema import ALLOWED_SELECTION_COLUMNS, FORBIDDEN_SELECTION_COLUMNS
from .universe_fingerprint import generate_universe_fingerprint

def audit_selection_dataset(df_selection, df_preds):
    forbidden_found = [c for c in FORBIDDEN_SELECTION_COLUMNS if c in df_selection.columns]
    
    rows = len(df_selection)
    rows_2026 = len(df_selection[df_selection["timestamp"].astype(str).str.contains("2026")]) if "timestamp" in df_selection.columns else 0
    
    status = "CANONICAL_SELECTION_DATASET_CLEAN"
    if forbidden_found:
        status = "CANONICAL_SELECTION_DATASET_HAS_FORBIDDEN_COLUMNS"
        
    # Generate a local fingerprint for this split
    fingerprint = generate_universe_fingerprint(df_selection, {"split": "selection"}, "v1.37")["universe_fingerprint"]
    
    return {
        "selection_dataset_rows": rows,
        "selection_dataset_rows_2026": rows_2026,
        "selection_dataset_columns": list(df_selection.columns),
        "forbidden_columns_found": forbidden_found,
        "selection_dataset_fingerprint": fingerprint,
        "selection_dataset_status": status
    }
