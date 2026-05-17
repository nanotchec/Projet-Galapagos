# Canonical Source Path Reconstruction - V1.35

This document summarizes the findings of the V1.35 diagnostic regarding the reconstruction of the V1.32.4 selection path (12,691 trades in 2026).

## Problem Statement
The V1.32.4 report documented a trade count that the current rebuild pipeline could not reproduce (8,939 trades). V1.35 systematically explores historical configurations to identify the exact path or certify the source as non-reproducible.

## Methodology
We generated 15 hypotheses covering variations in:
- **Join Policies**: Inner vs Left vs None.
- **Warmup Policies**: 0 vs 100 bars.
- **Dedup Policies**: None vs First per timestamp.
- **Outcome Policies**: All rows vs Outcome-present only.

## Findings
The best match hypothesis and its delta to the target count (12,691) are documented in the match analysis report.

## Conclusion
The reproducibility status of V1.32.4 is determined based on whether an exact count match was achieved across the tested hypotheses.

## Recommendation
Refer to the `v1_35_recommendation.json` for specific next steps regarding the canonical status of V1.32.4.
