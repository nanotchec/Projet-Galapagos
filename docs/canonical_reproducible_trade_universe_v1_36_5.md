# Canonical Reproducible Trade Universe - V1.36.5

This document finalizes the V1.36 infrastructure freeze by enforcing a complete cleanup of the project state and securing the canonical schema source code.

## State Cleanup and Schema Integrity (v1.36.5_explicit)

V1.36.5 removes all legacy artifacts from the previous diagnostic phases (V1.33 to V1.35) to focus strictly on the reproducible infrastructure foundation.

### 1. PROJECT_STATE Sanitization
- **Action**: All heritage fields related to reversal diagnostics, model mismatches, or old filter performance have been moved to `legacy_context` or removed from the root of `PROJECT_STATE.json`.
- **Result**: The project state now exposes only the canonical counts, readiness metrics, and infrastructure verdicts relevant to the future of the project.

### 2. Schema Source Correction (`universe_schema.py`)
- **Correction**: The source code for policy definitions has been updated to match the research audits.
- **EV/Cost Policy**: Now explicitly defined as `NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE` within the codebase itself.
- **Safety**: Operational formulas for EV calculation have been removed from the schema to prevent accidental use in canonical contexts.

### 3. Verdict Maintenance
- **Verdict**: `CANONICAL_UNIVERSE_DEFINED_WITH_WARNINGS`.
- **Note**: The warnings regarding future outcomes in the raw data are preserved as a permanent "Honesty Flag", even though causal separation is strictly enforced in the selection frame.

## Summary of Aligned Metrics
- **Warmup Context**: ~168k rows (Ready).
- **EV/Cost Features**: 0 (Not Included).
- **Recommended Next Step**: "rerun EV-net research on canonical opportunity universe with explicit EV/cost feature rebuild and reference-count checks".

## Infrastructure Status
- **Infrastructure Classification**: INFRASTRUCTURE_ONLY
- **Legacy Fields Root Cleanup**: COMPLETE
- **Real Trading**: PROHIBITED

**Transition to V1.36.6**: V1.36.6 mandates the inclusion of the official recommendation artifact (`v1_36_6_recommendation`) and hardens the release verification pipeline to ensure all required documentation and status fields are present in the final package.
