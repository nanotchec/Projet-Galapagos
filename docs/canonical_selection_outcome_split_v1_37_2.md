# Canonical Selection/Outcome Split - Galapagos V1.37.2 (Alignment & Cleanup)

## Context
Galapagos V1.37.1 successfully enforced the use of real datasets and resolved the outcome column warning. However, some documentary inconsistencies and legacy metadata remained:
- `consistency_check_status` was still marked as `PENDING_VALIDATION` in some reports.
- `PROJECT_STATE.json` contained many legacy root fields from previous diagnostic versions.

## Resolution (V1.37.2)
V1.37.2 focuses on aligning the project state and metrics for a clean canonical baseline:

1.  **Consistency Alignment**: `consistency_check_status` is now set to `CANONICAL_UNIVERSE_REPORTS_CONSISTENT_REAL_DATA_FORMAL_SPLIT` across all reports, summary files, and the global project state.
2.  **Root Cleanup**: Legacy diagnostic fields (e.g., `source_count_match`, `confidence_level`) have been removed from the root of `PROJECT_STATE.json` and moved to `legacy_context`.
3.  **Hardened Validation**: The automated validator now enforces these clean criteria, ensuring no "PENDING" status or legacy root contamination.

## Audit Results
- **Consistency Check**: PASSED (`CANONICAL_UNIVERSE_REPORTS_CONSISTENT_REAL_DATA_FORMAL_SPLIT`).
- **Root Cleanup**: PASSED (All forbidden legacy fields moved to `legacy_context`).
- **Row Counts**: STABLE (171,648 rows maintained).

## Status
Final Verdict: **CANONICAL_UNIVERSE_DEFINED_WITH_REAL_DATA_SELECTION_OUTCOME_SPLIT**
Consistency: **CANONICAL_UNIVERSE_REPORTS_CONSISTENT_REAL_DATA_FORMAL_SPLIT**

This release provides the final, clean, and fully consistent infrastructure-only documentation for the canonical trade universe.

This project remains **INFRASTRUCTURE ONLY**. No trading strategy has been validated.
