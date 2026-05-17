# Canonical Reproducible Trade Universe - V1.36.6

This document finalizes the V1.36 infrastructure freeze by enforcing the presence of the official recommendation artifact and ensuring that all release metrics are complete.

## Recommendation Artifact Integrity (v1.36.6_explicit)

V1.36.6 mandates the inclusion of `v1_36_6_recommendation.json` and its markdown equivalent in every release package.

### 1. Mandatory Recommendation Artifact
- **Requirement**: The validator now fails if the recommendation files are missing.
- **Goal**: Ensure that the next steps of the project are explicitly documented and machine-readable for the research pipeline.
- **Flag**: `recommendation_artifact_present: true`.

### 2. Metric Completeness
- **Consistency Status**: `latest_metrics` now includes `consistency_check_status` as a top-level field to ensure that the infrastructure validation status is immediately visible.
- **Alignment**: All Project State files (`PROJECT_STATE.json/md`) and metrics are strictly aligned with the canonical summary.

### 3. Verdict Maintenance
- **Verdict**: `CANONICAL_UNIVERSE_DEFINED_WITH_WARNINGS`.
- **Constraint**: These warnings regarding raw data outcomes are acknowledged but do not prevent the definition of a causal research universe.

## Official Recommendation
- **Recommended Next Step**: "resolve universe definition warnings before rerunning EV-net research".
- **Context**: While the infrastructure is ready, resolving the source dataset warnings is recommended before proceeding to large-scale strategy optimization.

## Infrastructure Status
- **Infrastructure Classification**: INFRASTRUCTURE_ONLY
- **Recommendation Artifact**: INCLUDED
- **Real Trading**: PROHIBITED

**Transition to V1.36.7**: V1.36.7 enforces the physical inclusion of the recommendation artifacts via strict filesystem checks, correcting previous packaging omissions and ensuring the release is truly ready for audit.
