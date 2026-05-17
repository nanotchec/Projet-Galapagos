# Canonical Reproducible Trade Universe - V1.36.2

This document completes the V1.36 infrastructure freeze by ensuring honest readiness reporting and validated historical reference counts for the BTC/4h model.

## Explicit Three-Level Semantics (v1.36.2_explicit)

### 1. Raw Prediction Universe (`raw_prediction_rows`)
- **Count**: 171,648 (Total) / 24,360 (2026).
- **Definition**: Baseline signal pool from ML models.

### 2. Canonical Opportunity Universe (`canonical_opportunity_rows`)
- **Count**: 171,648 (Total) / 24,360 (2026).
- **Definition**: The full research foundation after canonical join/dedup/warmup, without trading filters.
- **EV/Cost Readiness**: Currently NOT included. Future research must rebuild features explicitly on this base.

### 3. EV-Filter Reference Universe (`ev_filter_reference_selected_rows`)
- **Count**: 74,742 (Total) / 8,939 (2026).
- **Status**: `EV_FILTER_REFERENCE_IMPORTED_FROM_V1_35_3`.
- **Definition**: Historical diagnostic reference for the `filter_ev_gt_cost_buffer` logic.
- **Note**: This reference is diagnostic only and is NOT equivalent to any raw probability threshold (e.g., 0.65).

## Infrastructure Readiness

V1.36.2 enforces strict separation between warmup and feature readiness:
- **Warmup Readiness**: High (~168k rows) indicating sufficient historical context for evaluation.
- **Feature Availability**: Currently FALSE for EV/Cost in the opportunity universe.
- **Proxy Readiness**: 0 (until features are rebuilt).

## Policy Updates

### Cost Policy
- **Status**: `COST_POLICY_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE`.
- **Constraint**: Future EV research must integrate a validated cost proxy before strategy evaluation.

### EV Feature Policy
- **Status**: `EV_FEATURES_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE`.

## Safety Flags
- **Strategy Validated**: FALSE
- **Filter Applied to Opportunity Universe**: FALSE
**Transition to V1.36.3**: V1.36.3 enforces strict semantic separation between `warmup_ready_rows` (historical context) and `ev_feature_ready_rows` (effective feature presence), ensuring absolute honesty in the opportunity universe definition.
