"""Analysis of coverage during 2026 and other failure periods."""
from __future__ import annotations

import pandas as pd
from typing import Any

class CoverageVsFailureAnalysis:
    """Analyzes coverage in relation to model failure periods."""
    
    def run(self, dataset: pd.DataFrame) -> dict[str, Any]:
        """Compares coverage in 2026 vs previous years."""
        if not pd.api.types.is_datetime64_any_dtype(dataset.index):
            dataset.index = pd.to_datetime(dataset.index)
            
        dataset_2026 = dataset[dataset.index.year == 2026]
        dataset_prev = dataset[dataset.index.year < 2026]
        
        missing_2026 = dataset_2026.isnull().mean().mean() if not dataset_2026.empty else 0.0
        missing_prev = dataset_prev.isnull().mean().mean() if not dataset_prev.empty else 0.0
        
        failure_2026_related_to_coverage = False
        if missing_2026 > missing_prev * 1.5:
            failure_2026_related_to_coverage = True
            
        return {
            "status": "COMPLETED",
            "missingness_2026": float(missing_2026),
            "missingness_baseline": float(missing_prev),
            "failure_2026_related_to_coverage": failure_2026_related_to_coverage,
            "coverage_vs_failure_status": "MICROSTRUCTURE_COVERAGE_VS_FAILURE_COMPLETED"
        }
