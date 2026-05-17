import pandas as pd

class MicrostructureCausalAvailability:
    def __init__(self, forbidden_columns=None):
        self.forbidden_columns = forbidden_columns or ["target", "outcome", "future_return", "ev_proxy"]

    def audit(self, df: pd.DataFrame) -> dict:
        used_columns = df.columns.tolist()
        leaking_columns = [col for col in used_columns if any(f in col.lower() for f in self.forbidden_columns)]
        
        status = "MICROSTRUCTURE_CAUSAL_AVAILABILITY_PASSED"
        if leaking_columns:
            status = "MICROSTRUCTURE_CAUSAL_AVAILABILITY_FAILED"
            
        return {
            "status": status,
            "forbidden_columns_found": leaking_columns,
            "checked_columns": used_columns,
            "causal_availability_score": 1.0 if not leaking_columns else 0.0
        }
