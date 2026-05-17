import pandas as pd
from .universe_schema import CANONICAL_KEYS
from .universe_fingerprint import generate_universe_fingerprint

def audit_opportunity_index(df_index):
    rows = len(df_index)
    rows_2026 = len(df_index[df_index["timestamp"].astype(str).str.contains("2026")]) if "timestamp" in df_index.columns else 0
    
    # Check for duplicates on canonical keys
    duplicate_count = df_index.duplicated(subset=CANONICAL_KEYS).sum()
    
    # Generate a local fingerprint for this split
    fingerprint = generate_universe_fingerprint(df_index, {"split": "index"}, "v1.37")["universe_fingerprint"]
    
    return {
        "opportunity_index_rows": rows,
        "opportunity_index_rows_2026": rows_2026,
        "index_columns": list(df_index.columns),
        "duplicate_index_count": int(duplicate_count),
        "opportunity_index_fingerprint": fingerprint,
        "opportunity_index_status": "CANONICAL_OPPORTUNITY_INDEX_DEFINED"
    }
