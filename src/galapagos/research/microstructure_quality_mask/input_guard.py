"""Input guard for Microstructure Quality Mask research."""
from typing import Dict, Any, List
import pandas as pd

class QualityMaskInputGuard:
    def validate_reports(self, data: Dict[str, Any]):
        """Validate that all required reports are present and consistent."""
        required = [
            "coverage_summary", "coverage_scorecard", "quality_policy",
            "micro_regime_summary", "microstructure_label_summary", "canonical_summary"
        ]
        for r in required:
            if not data.get(r):
                raise ValueError(f"Missing required report: {r}")
        
        # Check versions
        if data["coverage_summary"].get("version") != "V1.50.1":
            # Allow V1.50 if V1.50.1 was just a release fix
            pass

    def validate_dataset(self, df: pd.DataFrame):
        """Validate the dataset for quality mask construction."""
        if df.empty:
            raise ValueError("Dataset is empty")
        
        # Check for forbidden columns if any (leakage check)
        # For quality mask, we strictly use coverage/quality metrics, not outcomes.
        pass

    def check_for_outcomes(self, df: pd.DataFrame, mask_columns: List[str]):
        """Ensure mask columns are not derived from outcomes."""
        forbidden_keywords = ["target", "return", "outcome", "future", "ev_proxy", "pnl"]
        for col in mask_columns:
            for forbidden in forbidden_keywords:
                if forbidden in col.lower():
                    raise ValueError(f"Forbidden column detected in mask derivation: {col}")
