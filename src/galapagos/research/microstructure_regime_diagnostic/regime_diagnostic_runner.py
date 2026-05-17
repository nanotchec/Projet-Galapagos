"""Orchestrate microstructure regime diagnostics V1.49."""
from __future__ import annotations

import pandas as pd
from typing import Any

from galapagos.research.microstructure_regime_diagnostic.regime_slice_builder import (
    build_regime_slices,
    get_regime_statistics
)
from galapagos.research.microstructure_regime_diagnostic.regime_loss_decomposition import (
    analyze_regime_losses
)
from galapagos.research.microstructure_regime_diagnostic.regime_2026_failure_explanation import (
    explain_2026_failures
)

def run_diagnostics(
    analysis_frame: pd.DataFrame,
    labels: list[str],
    outcome_col: str = "target_4h_bin"
) -> dict[str, Any]:
    """Run all diagnostic modules for V1.49."""
    
    # 1. Build slices
    frame_with_slices = build_regime_slices(analysis_frame, labels)
    
    # 2. Basic stats
    stats = get_regime_statistics(frame_with_slices)
    
    # 3. Loss decomposition
    losses = analyze_regime_losses(frame_with_slices, outcome_col)
    
    # 4. 2026 explanation
    failure_explanation = explain_2026_failures(frame_with_slices, outcome_col)
    
    return {
        "status": "COMPLETED",
        "regime_stats": stats,
        "loss_analysis": losses,
        "failure_2026_analysis": failure_explanation,
        "labels_used": labels,
        "frame_with_slices": frame_with_slices
    }
