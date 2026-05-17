import pandas as pd
from .universe_schema import ALLOWED_OUTCOME_COLUMNS
from .universe_fingerprint import generate_universe_fingerprint

def audit_outcome_dataset(df_outcome):
    rows = len(df_outcome)
    rows_2026 = len(df_outcome[df_outcome["timestamp"].astype(str).str.contains("2026")]) if "timestamp" in df_outcome.columns else 0
    
    # Generate a local fingerprint for this split
    fingerprint = generate_universe_fingerprint(df_outcome, {"split": "outcome"}, "v1.37")["universe_fingerprint"]
    
    return {
        "outcome_dataset_rows": rows,
        "outcome_dataset_rows_2026": rows_2026,
        "outcome_columns": list(df_outcome.columns),
        "outcome_dataset_fingerprint": fingerprint,
        "outcome_dataset_status": "CANONICAL_OUTCOME_DATASET_SEPARATED"
    }
