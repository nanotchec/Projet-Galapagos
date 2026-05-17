# Regime-Aware Feature Failure Diagnostic - V1.43.2

## Context
V1.43.2 corrects and hardens the diagnostic state established in V1.43.1. It focuses on canonical alignment and source semantics to ensure a clean base for future feature engineering.

## Key Changes
- **Canonical Base Guard**: Strict enforcement of `canonical_base_version = V1.37.2`. The pipeline now fails if this version is missing or mismatched.
- **Feature Source Semantics**:
    - **Raw Market Features**: Traditional OHLCV, volume, and funding data.
    - **Alpha Score Features**: Combined signals used for selection.
    - **Model Output Features**: `predicted_probability`, `calibrated_probability`, etc. These are now explicitly separated from raw features and excluded from raw engineering recommendations.
- **Project State Cleanup**:
    - Removed legacy V1.42 fields (`best_target_observed`, etc.) from the root.
    - Moved legacy context to the `legacy_context` field.
    - Added comprehensive diagnostic status fields to the root.

## Safety and Constraints
- **Evidence Classification**: `DIAGNOSTIC_ONLY`.
- **Strategy Validation**: `None`.
- **Safety Flags**: `no_real_trading`, `no_paper_live`, `no_new_filter` are all `true`.

## Conclusion
The diagnostic re-confirms that the 2026 failure is driven by predictive power decay and regime distribution shifts, even when model outputs are properly isolated from raw features.
