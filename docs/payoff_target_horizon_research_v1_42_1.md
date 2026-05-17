# Payoff Target Horizon and Definition Research V1.42.1

## Overview
This research phase (V1.42.1) focuses on rectifying methodological integrity issues identified in V1.42. It enforces strict row count semantics, eliminates NaN values in evaluation, and implements a label-only diagnostic policy for targets without specific model scores.

## Key Integrity Improvements
- **Count Semantics**: Formally distinguished between the 171,648-row canonical universe and the ~9,500-row research dataset.
- **NaN Elimination**: Hardened evaluation functions to ensure all JSON outputs are finite.
- **Unbiased Evaluation**: Transitioned to a "label-only" policy for exploratory targets to avoid false performance comparisons using mismatched scores.

## Results
The research successfully identified that while new targets (like `downside_weighted_return` and `severe_loss_classifier`) capture relevant payoff characteristics, they do not currently provide a significant edge over the V1.40.1 baseline in the 2026 window due to persistent regime drift.

- **Best Horizon Observed**: `forward_return_12bar`
- **Integrity Audit**: PASSED (100% finite JSONs, valid input guard).
- **Consistency**: PASSED (V1.42.1 pipeline validation).

## Verdict
**PAYOFF_TARGET_RESEARCH_RECENT_WINDOW_WEAK**

The research is complete but indicates that additional feature engineering or regime-aware adjustments are needed before these targets can be successfully utilized for predictive modelling.

## Safety Status
**EXPLORATORY_ONLY**. No trading, no live deployment, no holdout execution.
