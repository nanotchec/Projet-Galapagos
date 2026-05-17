import pandas as pd
from pathlib import Path

def load_reversal_diagnostic_data(
    predictions_path: str,
    dataset_path: str,
    intrabar_path: str = None
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame | None]:
    """
    Load data for reversal diagnostic.
    """
    preds = pd.read_parquet(predictions_path)
    dataset = pd.read_parquet(dataset_path)
    
    intrabar = None
    if intrabar_path:
        intrabar = pd.read_parquet(intrabar_path)
        
    return preds, dataset, intrabar
