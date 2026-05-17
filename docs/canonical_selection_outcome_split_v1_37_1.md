# Canonical Selection/Outcome Split - Galapagos V1.37.1 (Real Data Enforcement)

## Context
Galapagos V1.37 was invalidated because it was executed using mock/scratch-sized datasets (100 rows), failing to reflect the true canonical universe of 171,648 rows.

## Resolution (V1.37.1)
V1.37.1 strictly enforces the use of REAL canonical datasets through new automated guards:

1.  **Input Path Guard**: Rejects any input path containing `mock`, `scratch`, `dev/null`, or `tmp`. Only paths within the sanctioned `data/gold` and `data/silver` hierarchies are allowed.
2.  **Count Sanity Guard**: Verifies that row counts match the historical V1.36.8 baseline (171,648 rows). Any count below 100,000 or exactly 100 triggers an immediate failure.
3.  **Formal Split Re-execution**: The selection/outcome split logic is re-executed on the full-scale canonical data.

## Audit Results
- **Input Path Guard**: PASSED (All data sources are official Gold/Silver parquets).
- **Count Sanity Guard**: PASSED (Full 171,648 row universe recovered).
- **Selection Dataset**: CLEAN (0 forbidden outcome columns present).
- **Outcome Dataset**: SEPARATED (Physically distinct from causal frame).

## Status
Final Verdict: **CANONICAL_UNIVERSE_DEFINED_WITH_REAL_DATA_SELECTION_OUTCOME_SPLIT**
Warning Status: **CANONICAL_INPUT_OUTCOME_WARNING_RESOLVED**

This release confirms that the formal separation of selection and outcome data is now robustly implemented on the actual research universe.

This project remains **INFRASTRUCTURE ONLY**. No trading strategy has been validated.
