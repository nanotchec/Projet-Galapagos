# Canonical Reproducible Trade Universe - V1.36.3

This document finalizes the V1.36 infrastructure freeze by enforcing strict semantic separation between historical context (warmup) and feature readiness (EV/cost).

## Explicit Readiness Semantics (v1.36.3_explicit)

V1.36.3 clarifies that an opportunity universe can provide sufficient historical context for evaluation without necessarily including the executable EV/cost features.

### 1. Warmup Readiness (`warmup_ready_rows`)
- **Count**: 168,048 (Total) / 24,360 (2026).
- **Definition**: Indicates that 168,048 rows have enough preceding historical data to support causal feature calculation or outcome evaluation.
- **Status**: HIGH. The universe is ready for research.

### 2. EV Feature Readiness (`ev_feature_ready_rows`)
- **Count**: 0 (Total) / 0 (2026).
- **Definition**: Indicates whether EV-related features (probabilities, payoffs) are effectively populated in the current universe file.
- **Status**: `EV_FEATURES_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE`.
- **Note**: The canonical opportunity universe provides the *data foundation* for research but requires an explicit feature rebuild step before filtering.

### 3. EV Proxy Readiness (`ev_proxy_ready_rows`)
- **Count**: 0 (Total) / 0 (2026).
- **Definition**: Indicates availability of `ev_calibrated_proxy`.
- **Status**: 0. Requires both EV features and a cost proxy.

## Validation Hardening

V1.36.3 introduces a strict "Honesty Validator" that blocks any build where:
- Feature readiness counts are > 0 while features are declared missing.
- Warmup readiness is confused with feature readiness.

## Infrastructure Status
**Transition to V1.36.4**: V1.36.4 finalizes this definition by aligning the final verdict with input warnings (`CANONICAL_UNIVERSE_DEFINED_WITH_WARNINGS`) and explicitly reformulating the EV/Cost policy to reflect their total exclusion from the canonical opportunity universe foundation.
