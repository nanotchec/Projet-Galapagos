# Canonical Reproducible Trade Universe - V1.36.4

This document finalizes the V1.36 infrastructure freeze by ensuring a consistent and honest definition of the canonical opportunity universe, including the explicit exclusion of EV/cost features and the alignment of final verdicts with audit results.

## Final Canonical Definition (v1.36.4_explicit)

The canonical opportunity universe is defined as the full research signal pool after canonical join, deduplication, and warmup, but **without any trading filters applied**.

### 1. EV/Cost Semantics
- **Status**: `NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE`.
- **Constraint**: No executable EV features (calibrated probabilities, payoff estimates, cost proxies) are embedded in this universe.
- **Rationale**: The canonical universe provides the *data foundation*. Any future research involving EV-net strategies must explicitly rebuild these features using the provided causal methodology before filtering.

### 2. EV-Filter Reference (Diagnostic Only)
- **Status**: `EV_FILTER_REFERENCE_IMPORTED_FROM_V1_35_3`.
- **Definition**: The trades identified by `filter_ev_gt_cost_buffer` are provided as a historical diagnostic reference only. This reference is **not part** of the canonical opportunity universe selection and must not be used for live inference.

### 3. Verdict and Warnings
- **Final Verdict**: `CANONICAL_UNIVERSE_DEFINED_WITH_WARNINGS`.
- **Context**: Input audits detect "future" outcomes in the source dataset. While these are strictly excluded from the canonical selection frame (ensuring causal integrity), their presence in the raw data warrants a permanent warning status for transparency.

## Readiness Metrics

V1.36.4 provides honest readiness metrics in all reports (`latest_metrics`, `PROJECT_STATE`):
- **Warmup Readiness**: High (~168k rows) indicating sufficient historical data.
- **EV Feature Readiness**: 0 (Features not included).
- **EV Proxy Readiness**: 0.

## Safety Flags
- **Infrastructure Classification**: INFRASTRUCTURE_ONLY
- **Strategy Validated**: FALSE
- **Filter Applied to Opportunity Universe**: FALSE
- **Real Trading**: PROHIBITED

**Transition to V1.36.5**: V1.36.5 performs a full sanitization of the project state (root-level cleanup) and aligns the `universe_schema.py` source code with the "Not Included" status of EV/Cost features, ensuring a clean and secure foundation for future research.
