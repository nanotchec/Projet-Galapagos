# Canonical Reproducible Trade Universe - V1.36.1

This document refines the V1.36 infrastructure freeze by introducing explicit three-level count semantics and complete audit documentation for the BTC/4h model research.

## Count Semantics (v1.36.1_explicit)

To avoid ambiguity between raw data, research opportunities, and filtered trades, V1.36.1 defines three distinct levels:

### 1. Raw Prediction Universe (`raw_prediction_rows`)
- **Definition**: All prediction signals available from the source ML models.
- **Count 2026**: ~24,360 rows.
- **Purpose**: Baseline for the total available signal pool.

### 2. Canonical Opportunity Universe (`canonical_opportunity_rows`)
- **Definition**: The full research universe after joining with the feature dataset, deduplication, and warmup, but **WITHOUT** any trading filter applied.
- **Count 2026**: Should match raw predictions if no rows are dropped during join/dedup.
- **Purpose**: Official reproducible foundation for all future research.

### 3. EV-Filter Reference Selected Universe (`ev_filter_reference_selected_rows`)
- **Definition**: A historical reference of trades selected by the `filter_ev_gt_cost_buffer` logic (approx. `predicted_probability > 0.65`).
- **Count 2026**: ~8,939 rows (Rebuild Reference).
- **Purpose**: Reference point for comparing new research against historical findings.

## Explicit Policies

### Dataset Join Policy
- **Keys**: `timestamp` (mandatory), `model_name`, `feature_set`, `target`.
- **Type**: Inner Join.
- **Purpose**: Alignment with causal feature dataset.

### Outcome Alignment Policy
- **Keys**: `timestamp`, `model_name`, `feature_set`, `target`.
- **Type**: Inner Join.
- **Purpose**: Alignment with future realized outcomes for evaluation.

### Canonical Key Policy
- **Columns**: `timestamp`, `model_name`, `feature_set`, `target`, `split_name`.
- **Null Policy**: Strict No Nulls.
- **Duplicate Policy**: Keep first occurrence of exact key duplicates.

## Safety & Audit Coverage

V1.36.1 introduces three mandatory audit reports:
1. **Selection Frame Audit**: Verifies zero forbidden outcome columns in the causal frame.
2. **EV Feature Audit**: Verifies causal rebuild of probability, payoff, and cost proxies.
3. **Cost Policy Audit**: Documents the explicit proxies and their limitations.

## Status
- **Evidence Classification**: INFRASTRUCTURE_ONLY
- **Strategy Validated**: FALSE
- **Filter Applied to Opportunity Universe**: FALSE
**Transition to V1.36.2**: V1.36.2 completes this refinement by ensuring honest readiness reporting (separating warmup from EV features) and importing validated historical reference counts from V1.35.3.
