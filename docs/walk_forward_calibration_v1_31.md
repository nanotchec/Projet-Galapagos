# Walk-Forward Probability Calibration Research - V1.31

## Context
V1.31 investigates the potential of walk-forward probability calibration to improve the reliability of ML scores. The goal is to correct systematic biases in the raw probabilities produced by the model (Brier Score, ECE) before they are used in any Expected Value (EV) calculations.

## Methodology
- **Walk-Forward splits**: 
    - 2024 H1 (Train) -> 2024 H2 (Test)
    - 2024 (Train) -> 2025 H1 (Test)
    - 2024 - 2025 H1 (Train) -> 2025 H2 (Test)
    - 2024 - 2025 (Train) -> 2026 H1 (Test)
- **Calibration Methods**:
    - Platt Scaling (Logistic Regression on scores).
    - Isotonic Regression (Non-parametric piecewise constant).
    - Bin Calibration (Empirical win rates).
- **Validation**: Strict temporal separation. Calibrators are fitted on past windows and evaluated on future windows.

## Success Metrics
- Reduction in **Expected Calibration Error (ECE)**.
- Improvement in **Brier Score**.
- Stability of calibration parameters over time.

## Safety Constraints
- **Diagnostic Only**: No trading strategy or filters are selected in this version.
- **No Holdout**: All evaluation is done on walk-forward test sets.
- **Zero Real Trading**: No orders or money deployment.
