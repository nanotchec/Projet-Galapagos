# Regime-Aware Feature Failure Diagnostic - V1.43.1

## Context
V1.43.1 is a maintenance release correcting the feature inventory and state alignment issues identified in V1.43.

## Outcome Feature Exclusion
The following feature types have been formally excluded from the `usable_features` set:
- **MFE / MAE**: Max Favorable/Adverse Excursion columns.
- **Forward Returns**: All future return windows.
- **Outcome Targets**: Any column containing actual trade results or payoff raw data.

These columns were detected in V1.43 and removed in V1.43.1 to ensure zero future-data leakage in the diagnostic analysis.

## Diagnostic Recalibration
After excluding these features, the diagnostic was re-executed.

### Primary Findings
- **Feature Drift**: The primary driver of failure remains a massive distribution shift in the trend-momentum family during 2026 H1.
- **Predictive Power Decay**: Even after removing outcome-like features, the remaining alpha features show a correlation collapse on the most recent data window.
- **Stability Scorecard**: Features are now ranked based on a "clean" inventory. Most technical indicators show high instability in the 2026 regimes.

## Verdict
**REGIME_FEATURE_FAILURE_MULTI_FACTOR**

The failure is driven by:
1. Feature distribution drift (z-score > 2.0).
2. Predictive power decay (sign-flip on correlation).
3. Regime-feature interaction breakdown.

## Safety and Constraints
- **Evidence Classification**: DIAGNOSTIC_ONLY.
- **No real trading**.
- **No paper live**.
- **No strategy validated**.
- **No money deployment**.

Le système V1.43.1 ne peut toujours pas passer d’ordre réel.
