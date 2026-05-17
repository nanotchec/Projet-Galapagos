# Canonical Source Path Reconstruction - V1.35.3

This document summarizes the findings of the V1.35.3 diagnostic regarding the refined reconstruction of the V1.32.4 selection path.

## Hypothesis Diversity Audit
V1.35.3 confirms a significant lack of discrimination between the tested hypotheses:
1. **Count Collapse**: The diversity diagnostic identifies `HYPOTHESES_COLLAPSE_TO_REBUILD_COUNT`.
2. **Dominant Result**: 4 out of 6 valid hypotheses (including with/without warmup and different join policies) converge to exactly 8,939 trades in 2026.
3. **Conclusion**: The available artifacts do not allow for identifying the specific configuration that produced the historical 12,691 count.

## State Alignment
All project metadata, including `latest_metrics.json` and `latest_summary.md`, are now synchronized with the V1.35.3 diagnostic findings.

## Final Findings
- **Target Count (V1.32.4)**: 12,691
- **Rebuild Count**: 8,939
- **Gap**: -3,752
- **Diversity Status**: `HYPOTHESES_COLLAPSE_TO_REBUILD_COUNT`

## Recommendation
Retire V1.32.4 as canonical source unless historical selected-trade artifacts are recovered; define a new reproducible canonical universe from the EV-strict rebuild path.

**Transition to V1.36**: V1.36 officially defines this new canonical universe.
