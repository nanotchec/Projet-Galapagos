import pandas as pd

def audit_outcome_availability(df: pd.DataFrame):
    outcome_cols = ["outcome_forward_return", "actual_target", "forward_return_12bar"]
    found_cols = [c for c in outcome_cols if c in df.columns]
    
    results = {}
    for col in found_cols:
        missing_total = df[col].isna().sum()
        df_2026 = df[df.index >= "2026-01-01"]
        missing_2026 = df_2026[col].isna().sum() if not df_2026.empty else 0
        
        results[col] = {
            "missing_total": int(missing_total),
            "missing_2026": int(missing_2026)
        }
        
    return {
        "outcomes_found": found_cols,
        "availability": results,
        "outcome_filtering_status": "OUTCOME_AVAILABILITY_MATCHES" if not results else "OUTCOME_FILTERING_PARTIAL_EXPLANATION"
    }
