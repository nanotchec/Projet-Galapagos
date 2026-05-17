# Canonical Reproducible Trade Universe - V1.36.7

This document finalizes the V1.36 infrastructure freeze by enforcing the physical inclusion and filesystem verification of the recommendation artifact.

## Physical Artifact Integrity (v1.36.7_explicit)

V1.36.7 corrects a major release failure where recommendation artifacts were referenced in metadata but physically omitted from the release package.

### 1. Physical Filesystem Verification
- **New Constraint**: The validator now performs a direct `Path.exists()` check on the recommendation files (`.json` and `.md`).
- **Release Block**: The release pipeline is now hard-coded to fail if these physical files are missing, regardless of metadata flags.
- **Paths**:
  - `reports/research/v1_36_7_recommendation.json`
  - `reports/research/v1_36_7_recommendation.md`

### 2. Metadata Alignment
- **Path Fields**: `latest_metrics` and `PROJECT_STATE` now include explicit `recommendation_artifact_json_path` and `recommendation_artifact_md_path` to facilitate automated discovery.
- **Verification Flags**: `recommendation_json_exists` and `recommendation_md_exists` are now part of the official consistency check.

### 3. Verdict Maintenance
- **Verdict**: `CANONICAL_UNIVERSE_DEFINED_WITH_WARNINGS`.
- **Note**: Causal integrity is secured. The infrastructure is now physically complete and ready for external audit.

## Official Recommendation
- **Recommended Next Step**: "resolve universe definition warnings before rerunning EV-net research".
- **Safety**: No real trading allowed. No strategy validated.

## Infrastructure Status
- **Infrastructure Classification**: INFRASTRUCTURE_ONLY
- **Physical Inclusion Status**: VERIFIED OBLIGATORY
- **Real Trading**: PROHIBITED

**Transition to V1.36.8**: V1.36.8 adds explicit evidence fields in the audit and release reports to prove the inclusion of the recommendation artifacts, ensuring full traceability for external review.
