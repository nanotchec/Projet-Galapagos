"""Data loader for Microstructure Quality Mask research."""
import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any, List

class QualityMaskDataLoader:
    def __init__(self, 
                 predictions_path: str,
                 dataset_path: str,
                 alpha_dataset_path: str,
                 intrabar_path: str,
                 coverage_summary_path: str,
                 coverage_scorecard_path: str,
                 quality_policy_path: str,
                 micro_regime_summary_path: str,
                 microstructure_label_summary_path: str,
                 canonical_summary_path: str):
        self.predictions_path = Path(predictions_path)
        self.dataset_path = Path(dataset_path)
        self.alpha_dataset_path = Path(alpha_dataset_path)
        self.intrabar_path = Path(intrabar_path)
        self.coverage_summary_path = Path(coverage_summary_path)
        self.coverage_scorecard_path = Path(coverage_scorecard_path)
        self.quality_policy_path = Path(quality_policy_path)
        self.micro_regime_summary_path = Path(micro_regime_summary_path)
        self.microstructure_label_summary_path = Path(microstructure_label_summary_path)
        self.canonical_summary_path = Path(canonical_summary_path)

    def load_data(self) -> Dict[str, Any]:
        """Load all necessary data for the quality mask research."""
        data = {}
        
        # Load reports
        data["coverage_summary"] = self._load_json(self.coverage_summary_path)
        data["coverage_scorecard"] = self._load_json(self.coverage_scorecard_path)
        data["quality_policy"] = self._load_json(self.quality_policy_path)
        data["micro_regime_summary"] = self._load_json(self.micro_regime_summary_path)
        data["microstructure_label_summary"] = self._load_json(self.microstructure_label_summary_path)
        data["canonical_summary"] = self._load_json(self.canonical_summary_path)
        
        # Load parquet (metadata only if possible, or full for analysis)
        # Note: We don't load the full data in the constructor to save memory
        return data

    def load_main_dataset(self) -> pd.DataFrame:
        """Load the research dataset."""
        return pd.read_parquet(self.dataset_path)

    def load_alpha_dataset(self) -> pd.DataFrame:
        """Load the alpha dataset."""
        return pd.read_parquet(self.alpha_dataset_path)

    def load_predictions(self) -> pd.DataFrame:
        """Load ML predictions."""
        return pd.read_parquet(self.predictions_path)

    def load_intrabar_data(self) -> pd.DataFrame:
        """Load intrabar data."""
        return pd.read_parquet(self.intrabar_path)

    def _load_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        with open(path, "r") as f:
            return json.load(f)
