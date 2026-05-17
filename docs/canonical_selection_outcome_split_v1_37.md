# Canonical Selection/Outcome Split - Galapagos V1.37

## Context
The Galapagos V1.36 universe definition was marked with warnings due to the presence of outcome-related columns (e.g., `future_return`, `outcome_next_4h`) in the raw prediction dataset. While these columns were not used for selection, their presence in the primary causal frame presented a methodology risk and an audit warning.

## Resolution
V1.37 formally resolves this warning by implementing a strict physical separation of datasets:

1.  **Canonical Opportunity Index**: A unique identifier for every research opportunity (timestamp, model, feature set, target, split).
2.  **Canonical Selection Dataset**: Contains only causal features allowed by the `DatasetSplitPolicy`. All outcome-related columns are physically removed.
3.  **Canonical Outcome Dataset**: Contains only the target outcomes and associated identifiers.

## Audit Results
- **Selection Dataset**: Clean (0 forbidden columns found).
- **Outcome Dataset**: Separated (physically distinct from selection).
- **Index Integrity**: Validated (unique keys, no duplicates).

## Status
Final Verdict: **CANONICAL_UNIVERSE_DEFINED_WITH_FORMAL_SELECTION_OUTCOME_SPLIT**
Warning Status: **CANONICAL_INPUT_OUTCOME_WARNING_RESOLVED**

This project remains **INFRASTRUCTURE ONLY**. No trading strategy has been validated using these datasets.
