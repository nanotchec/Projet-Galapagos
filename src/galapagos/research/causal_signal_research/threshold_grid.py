from __future__ import annotations

from galapagos.research.causal_signal_research.causal_filter_rules import (
    ProbabilityThreshold,
    FirstAboveThresholdPerPeriod,
    CausalRunningTopScore,
    CooldownFilter
)

def build_causal_research_grid() -> list:
    """Return a list of causal filter instances to test."""
    thresholds = [0.55, 0.60, 0.65, 0.70]
    
    grid = []
    
    # A. Probability Thresholds
    for t in thresholds:
        grid.append(ProbabilityThreshold(t))
        
    # B. First per Period
    for t in thresholds:
        grid.append(FirstAboveThresholdPerPeriod(t, "7D"))
        grid.append(FirstAboveThresholdPerPeriod(t, "1D"))
        
    # C. Causal Running Top
    for t in thresholds:
        grid.append(CausalRunningTopScore(t, "7D"))
        
    # D. Cooldown
    for t in [0.60, 0.65]:
        for h in [24, 72, 168]:
            grid.append(CooldownFilter(t, h))
            
    return grid
