"""Input guard for microstructure coverage quality audit."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd

class CoverageInputGuard:
    """Validates inputs for microstructure coverage audit."""
    
    def validate(self, data: dict[str, pd.DataFrame]) -> dict[str, Any]:
        """Validates the loaded dataframes."""
        status = "PASSED"
        issues = []
        
        for key, df in data.items():
            if df.empty:
                status = "FAILED"
                issues.append(f"Dataframe '{key}' is empty.")
                
        # Basic column checks if needed
        if "intrabar" in data:
            if "timestamp" not in data["intrabar"].columns:
                status = "FAILED"
                issues.append("Intrabar data missing 'timestamp' column.")
                
        return {
            "status": status,
            "issues": issues,
            "input_guard_status": f"MICROSTRUCTURE_COVERAGE_INPUT_GUARD_{status}"
        }
