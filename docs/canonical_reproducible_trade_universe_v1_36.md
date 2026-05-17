# Canonical Reproducible Trade Universe - V1.36

This document defines the canonical reproducible trade universe for the BTC/4h model research. 
V1.36 freezes the infrastructure to ensure all future research (EV-net, Reversal Diagnostic, Payoff-Aware) starts from the same strictly causal and reproducible foundation.

## Trade Unit Definition
A trade unit is defined as one unique opportunity per prediction row after the canonical join between ML predictions and the research dataset.

## Join Policy
- **Type**: Inner Join
- **Keys**: `timestamp` (mandatory), `model_name`, `feature_set`, `target` (if available).
- **Rationale**: Ensure perfect alignment between selection signals and outcome data.

## Deduplication Policy
- **Rule**: Exact duplicates of the canonical key are removed (keeping the first occurrence).
- **No Optimization**: No selection of "best model" or "highest score" at this stage. 

## Warmup Policy
- **Rule**: 100 periods of historical signals are required for payoff/EV estimation.
- **Implementation**: Rows are flagged with `ev_proxy_ready = false` during the warmup phase but are NOT dropped from the universe.

## Causal Safety & Leakage
- **Selection Frame**: Strictly limited to causal columns (`predicted_probability`, `cost_proxy`, etc.).
- **Outcome Frame**: Isolated future columns (`pnl`, `actual_target`, `exit_reason`).
- **Audit**: Zero selection leakage is a mandatory requirement for V1.36 validation.

## Reproducibility
- **Fingerprint**: A stable hash is generated based on the sorted canonical keys and the universe definition.
- **Versioning**: All future research must reference the V1.36 fingerprint to ensure comparability.

## Status
- **Evidence Classification**: INFRASTRUCTURE_ONLY
- **Strategy Validated**: FALSE
- **Real Trading**: PROHIBITED

**Transition to V1.36.1**: V1.36.1 refines this definition with explicit three-level count semantics and additional audit reports.
