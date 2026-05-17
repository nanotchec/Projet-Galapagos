# Canonical Source Path Reconstruction - V1.35.2

This document summarizes the findings of the V1.35.2 diagnostic regarding the refined reconstruction of the V1.32.4 selection path.

## Semantic Refinement
V1.35.2 clarifies the nature of the non-reproducibility:
1. **Source Artifacts Insufficient**: The diagnostic concludes that available artifacts (missing selected trade IDs, timestamps, and serialized EV values) are insufficient to uniquely recover the historical selection path.
2. **Not a Mathematical Impossibility**: The status `SOURCE_PATH_NOT_RECOVERED_FROM_AVAILABLE_ARTIFACTS` is used to reflect that the discrepancy is likely due to missing metadata rather than a proof of logic failure.
3. **Hypothesis Diversity**: A diversity diagnostic confirmed that multiple configurations (H1, H2, H3, H6) collapse to the same rebuild count of 8,939 trades in 2026, indicating that current hypotheses do not provide enough discrimination to bridge the -3,752 gap.

## Final Findings
- **Target Count (V1.32.4)**: 12,691
- **Rebuild Count**: 8,939
- **Gap**: -3,752
- **Driver**: `SOURCE_ARTIFACTS_INSUFFICIENT`

## Recommendation
Retire V1.32.4 as canonical source **unless historical selected-trade artifacts are recovered**. Define a new reproducible canonical universe from the EV-strict rebuild path.
