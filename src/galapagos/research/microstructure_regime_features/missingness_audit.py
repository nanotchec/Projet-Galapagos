import pandas as pd

class MicrostructureMissingnessAudit:
    def __init__(self):
        pass

    def audit(self, df: pd.DataFrame) -> dict:
        missing_counts = df.isnull().sum().to_dict()
        missing_ratios = (df.isnull().sum() / len(df)).to_dict() if len(df) > 0 else {}
        
        return {
            "status": "MICROSTRUCTURE_MISSINGNESS_COMPLETED",
            "missing_counts": missing_counts,
            "missing_ratios": missing_ratios
        }
