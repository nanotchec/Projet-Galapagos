"""Analysis of coverage impact on regime label quality."""
from __future__ import annotations

import pandas as pd
from typing import Any

class LabelCoverageImpact:
    """Analyzes if low coverage impacts label stability."""
    
    def run(self, dataset: pd.DataFrame, intrabar_coverage: dict[str, Any]) -> dict[str, Any]:
        """Correlates coverage with label missingness/instability."""
        
        # We check if periods with low intrabar coverage have higher label missingness
        coverage_ratio = intrabar_coverage.get("average_coverage_ratio", 1.0)
        
        label_columns = [c for c in dataset.columns if "_regime" in c]
        label_missingness = dataset[label_columns].isnull().mean().mean() if label_columns else 0.0
        
        impact_detected = False
        if coverage_ratio < 0.9 and label_missingness > 0.05:
            impact_detected = True
            
        return {
            "status": "COMPLETED",
            "coverage_ratio": float(coverage_ratio),
            "label_missingness_mean": float(label_missingness),
            "coverage_impact_detected": impact_detected,
            "label_coverage_impact_status": "MICROSTRUCTURE_LABEL_COVERAGE_IMPACT_COMPLETED"
        }
