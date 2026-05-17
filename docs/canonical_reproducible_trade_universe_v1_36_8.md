# Canonical Reproducible Trade Universe - V1.36.8

This document finalizes the V1.36 infrastructure freeze by adding explicit evidence fields for the recommendation artifact inclusion in all release and audit reports.

## Explicit Evidence Fields (v1.36.8_explicit)

V1.36.8 addresses a lack of explicit traceability in the release reports by adding dedicated fields that prove the recommendation artifacts were checked and included.

### 1. Mandatory Evidence Fields
The following fields are now mandatory in `zip_audit_v1_36_8.json` and `release_zip_v1_36_8.json`:
- `recommendation_artifact_required`: **true**
- `recommendation_json_included`: **true**
- `recommendation_md_included`: **true**
- `recommendation_json_path`: `reports/research/v1_36_8_recommendation.json`
- `recommendation_md_path`: `reports/research/v1_36_8_recommendation.md`

### 2. Consistency Report Hardening
The `canonical_universe_consistency_check_v1_36_8.json` now includes explicit paths:
- `recommendation_json_path`
- `recommendation_md_path`

### 3. Physical Verification
- **Audit**: The `audit_zip` function now explicitly sets `reco_json_included` and `reco_md_included` by checking the zip content.
- **Release**: The `release_zip` payload reflects these values, ensuring that a "ready for external review" status is backed by explicit inclusion evidence.

## Official Recommendation
- **Recommended Next Step**: "resolve universe definition warnings before rerunning EV-net research".
- **Safety**: No real trading allowed. No strategy validated.

## Infrastructure Status
- **Infrastructure Classification**: INFRASTRUCTURE_ONLY
- **Evidence Fields Status**: EXPLICITLY INCLUDED
- **Physical Inclusion Status**: VERIFIED
- **Real Trading**: PROHIBITED
