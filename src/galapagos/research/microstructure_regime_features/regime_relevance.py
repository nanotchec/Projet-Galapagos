import pandas as pd

class MicrostructureRegimeRelevance:
    def __init__(self):
        pass

    def audit(self, features_df: pd.DataFrame, regimes_df: pd.DataFrame) -> dict:
        # Simple correlation-based relevance for research only
        relevance_metrics = {}
        if not regimes_df.empty and not features_df.empty:
            common_idx = features_df.index.intersection(regimes_df.index)
            f_sub = features_df.loc[common_idx]
            r_sub = regimes_df.loc[common_idx]
            
            for f_col in f_sub.columns:
                relevance_metrics[f_col] = {}
                for r_col in r_sub.columns:
                    if r_sub[r_col].dtype in ['float64', 'int64']:
                        corr = f_sub[f_col].corr(r_sub[r_col])
                        relevance_metrics[f_col][r_col] = float(corr) if not pd.isna(corr) else 0.0
        
        return {
            "status": "MICROSTRUCTURE_RELEVANCE_COMPLETED",
            "relevance_metrics": relevance_metrics
        }
