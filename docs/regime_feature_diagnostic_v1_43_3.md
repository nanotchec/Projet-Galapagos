# Regime-Aware Feature Failure Diagnostic - V1.43.3

## Context
V1.43.3 implements strict raw feature semantics. It addresses the issue of metadata and model proxies being mixed with raw market features, which could lead to misleading future research orientations.

## Key Changes
- **Strict Source Semantics**:
    - **Metadata**: `model_name`, `feature_set`, etc., are moved to `metadata_features`.
    - **Model Outputs**: `predicted_probability`, etc., are moved to `model_output_features`.
    - **EV Proxies**: `avg_win_past`, `cost_proxy`, `basis_proxy`, etc., are moved to `ev_proxy_features`.
    - **Outcome Forbidden**: `direction_up_after_cost`, `tp_before_sl` are strictly excluded.
- **V1.44 Recommendation Fix**:
    - Recommendations for V1.44 now explicitly guide towards raw market and alpha-specific families.
    - The hybrid family `alpha_score_or_model_output` is strictly excluded from raw engineering recommendations.
- **Project State Alignment**:
    - Full synchronization of diagnostic status fields.
    - New flags for audit: `model_outputs_separated_from_raw_features`, `ev_proxies_separated_from_raw_features`, `metadata_separated_from_raw_features`.

## Safety and Constraints
- **Evidence Classification**: `DIAGNOSTIC_ONLY`.
- **Strategy Validation**: `None`.
- **Safety Flags**: `no_real_trading`, `no_paper_live`, `no_new_filter` are all `true`.

## Conclusion
The diagnostic state is now perfectly clean. Future feature engineering in V1.44 will operate on a strictly causal and raw market feature set, with model outputs and proxies isolated for diagnostic reference only.
