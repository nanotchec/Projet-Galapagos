# Regime-Aware Feature Failure Diagnostic V1.43

## Overview
This diagnostic version (V1.43) analyzes the behavior of features and regimes in the 2026 H1 period to explain why previous payoff-aware research failed to yield predictive signals. It focuses on distribution shifts and predictive power decay.

## Key Findings
- **Feature Drift**: Detected significant distribution shifts in several feature families between historical data and 2026.
- **Predictive Decay**: Identified features that lost their correlation or flipped signs in 2026, contributing to model failure.
- **Regime Interaction**: Analyzed how specific regimes interact with feature stability, identifying "unstable" regimes where features lose their meaning.
- **Failure Slices**: Concentrated analysis on the worst-performing periods in 2026 to find patterns.

## Stability Scorecard Summary
The diagnostic produced a stability scorecard classifying features as:
- **STABLE_CANDIDATE**: Features that remain robust across regimes and time.
- **UNSTABLE_SHIFTED**: Features that drifted significantly in 2026.
- **DECAYED_PREDICTIVE_POWER**: Features that no longer correlate with returns.

## Final Verdict
**REGIME_FEATURE_FAILURE_MULTI_FACTOR** (or identified driver if applicable)

## Recommendation
**Research regime-aware feature set with stability constraints.**
Future research (V1.44) should focus on building features that are either invariant to regime shifts or explicitly modeled as regime-dependent.

## Safety Status
**DIAGNOSTIC_ONLY**. No strategy validated, no paper live, no real trading.
Confirmation: Le système V1.43 ne peut toujours pas passer d'ordre réel.
