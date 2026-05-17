"""Data loader for microstructure coverage quality audit."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd

class CoverageDataLoader:
    """Loads data for microstructure coverage audit."""
    
    def __init__(self, predictions_path: str | Path, dataset_path: str | Path, 
                 alpha_dataset_path: str | Path, intrabar_path: str | Path):
        self.predictions_path = Path(predictions_path)
        self.dataset_path = Path(dataset_path)
        self.alpha_dataset_path = Path(alpha_dataset_path)
        self.intrabar_path = Path(intrabar_path)
        
    def load_all(self) -> dict[str, pd.DataFrame]:
        """Loads all required dataframes."""
        return {
            "predictions": pd.read_parquet(self.predictions_path),
            "dataset": pd.read_parquet(self.dataset_path),
            "alpha_dataset": pd.read_parquet(self.alpha_dataset_path),
            "intrabar": pd.read_parquet(self.intrabar_path)
        }
