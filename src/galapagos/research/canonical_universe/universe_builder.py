import pandas as pd
from .input_audit import audit_inputs
from .join_policy import apply_join_policy
from .dedup_policy import apply_dedup_policy
from .warmup_policy import apply_warmup_policy
from .outcome_policy import separate_outcome_frame
from .leakage_policy import audit_leakage
from .universe_fingerprint import generate_universe_fingerprint
from .universe_schema import ALLOWED_SELECTION_COLUMNS, CANONICAL_KEYS
from .selection_frame_audit import audit_selection_frame
from .ev_feature_audit import audit_ev_features
from .cost_policy_audit import audit_cost_policy
from .ev_filter_reference_audit import audit_ev_filter_reference

from .input_path_guard import check_input_paths
from .count_sanity_guard import check_count_sanity

# New imports for V1.37
from .dataset_split_policy import get_dataset_split_policy
from .canonical_selection_dataset import audit_selection_dataset
from .canonical_outcome_dataset import audit_outcome_dataset
from .canonical_opportunity_index import audit_opportunity_index
from .warning_resolution_audit import audit_warning_resolution

def build_canonical_universe(df_preds, df_dataset, version="v1.37.1", paths=None):
    # 0. Path Guard
    path_guard = {"input_path_guard_status": "SKIPPED"}
    if paths:
        path_guard = check_input_paths(
            paths.get("predictions_path", ""),
            paths.get("dataset_path", ""),
            paths.get("intrabar_path", ""),
            version=version
        )
        if path_guard["input_path_guard_status"] == "CANONICAL_INPUT_PATH_GUARD_FAILED":
             # We let it continue so reports are written, but we will check later in builder
             pass

    # A. Level 1: Raw Prediction Universe
    raw_rows = len(df_preds)
    raw_rows_2026 = len(df_preds[df_preds["timestamp"].astype(str).str.contains("2026")]) if "timestamp" in df_preds.columns else 0
    
    # 1. Audit Inputs (Raw)
    input_audit = audit_inputs(df_preds, df_dataset)
    
    # 2. Join (Level 2: Canonical Opportunity Universe starts here)
    df_joined, join_report = apply_join_policy(df_preds, df_dataset)
    
    # 3. Dedup
    df_dedup, dedup_report = apply_dedup_policy(df_joined)
    
    # 4. Warmup marking
    df_warmup, warmup_report = apply_warmup_policy(df_dedup)
    
    # Canonical keys must exist even on minimal research fixtures.
    canonical_defaults = {
        "model_name": "unknown",
        "feature_set": "unknown",
        "target": pd.NA,
        "split_name": "unknown",
    }
    for key, default in canonical_defaults.items():
        if key not in df_warmup.columns:
            df_warmup[key] = default
    
    # 5. Outcome separation (Formal Split V1.37)
    df_outcome_full, outcome_report_legacy = separate_outcome_frame(df_warmup)
    
    # Selection frame cleanup (keep only allowed causal)
    selection_cols = [c for c in ALLOWED_SELECTION_COLUMNS if c in df_warmup.columns]
    df_selection = df_warmup[selection_cols].copy()
    
    # --- New V1.37 Split Logic ---
    split_policy = get_dataset_split_policy()
    
    # Index
    df_index = df_selection[CANONICAL_KEYS].copy()
    index_audit = audit_opportunity_index(df_index)
    
    # Selection
    selection_audit = audit_selection_dataset(df_selection, df_preds)
    
    # Outcome (Subset to allowed columns)
    outcome_cols = [c for c in split_policy["outcome_columns"] if c in df_outcome_full.columns]
    df_outcome = df_outcome_full[outcome_cols].copy()
    outcome_audit = audit_outcome_dataset(df_outcome)
    
    # 6. Count Sanity Guard
    count_guard = check_count_sanity(
        raw_rows,
        len(df_selection),
        selection_audit["selection_dataset_rows"],
        outcome_audit["outcome_dataset_rows"],
        index_audit["opportunity_index_rows"],
        version=version
    )

    # Warning Resolution
    warning_res_audit = audit_warning_resolution(selection_audit, outcome_audit, input_audit)
    # Add guard statuses to warning audit for visibility
    warning_res_audit["input_path_guard_status"] = path_guard["input_path_guard_status"]
    warning_res_audit["count_sanity_guard_status"] = count_guard["count_sanity_guard_status"]
    # -----------------------------
    
    # Audits for features/costs
    ev_feature_audit_data = audit_ev_features(df_warmup)
    cost_policy_audit_data = audit_cost_policy(df_warmup)
    
    # B. Level 3: EV Filter Reference Selected Universe (Reference only)
    ref_audit = audit_ev_filter_reference()
    
    # 7. Leakage audit
    leakage_report = audit_leakage(df_selection, df_outcome)
    
    # 8. Fingerprint
    definition = {
        "version": version,
        "count_semantics_version": "v1.37.2_real_data_split",
        "join_policy": join_report["dataset_join_type"],
        "dedup_policy": dedup_report["dedup_policy_status"],
        "warmup_min_periods": warmup_report["warmup_min_periods"],
        "warning_resolution_status": warning_res_audit["warning_resolution_status"]
    }
    fingerprint_report = generate_universe_fingerprint(df_selection, definition, version)
    
    # C. Level 2: Canonical Opportunity Universe counts
    opportunity_rows = len(df_selection)
    opportunity_rows_2026 = len(df_selection[df_selection["timestamp"].astype(str).str.contains("2026")])
    
    count_semantics_version = "v1.36.8_explicit" if str(version).startswith("v1.36.8") else "v1.37.2_real_data_split"

    counts = {
        "count_semantics_version": count_semantics_version,
        "raw_prediction_rows": raw_rows,
        "raw_prediction_rows_2026": raw_rows_2026,
        "canonical_opportunity_rows": opportunity_rows,
        "canonical_opportunity_rows_2026": opportunity_rows_2026,
        "selection_dataset_rows": selection_audit["selection_dataset_rows"],
        "selection_dataset_rows_2026": selection_audit["selection_dataset_rows_2026"],
        "outcome_dataset_rows": outcome_audit["outcome_dataset_rows"],
        "outcome_dataset_rows_2026": outcome_audit["outcome_dataset_rows_2026"],
        "opportunity_index_rows": index_audit["opportunity_index_rows"],
        "opportunity_index_rows_2026": index_audit["opportunity_index_rows_2026"],
        "warmup_ready_rows": ev_feature_audit_data["warmup_ready_rows"],
        "warmup_ready_rows_2026": ev_feature_audit_data["warmup_ready_rows_2026"],
        "ev_feature_ready_rows": ev_feature_audit_data["ev_feature_ready_rows"],
        "ev_feature_ready_rows_2026": ev_feature_audit_data["ev_feature_ready_rows_2026"],
        "ev_proxy_ready_rows": ev_feature_audit_data["ev_proxy_ready_rows"],
        "ev_proxy_ready_rows_2026": ev_feature_audit_data["ev_proxy_ready_rows_2026"],
        "ev_filter_reference_selected_rows": ref_audit["ev_filter_reference_selected_rows"],
        "ev_filter_reference_selected_rows_2026": ref_audit["ev_filter_reference_selected_rows_2026"],
        "ev_filter_reference_status": ref_audit["ev_filter_reference_status"],
        "counts_status": "CANONICAL_UNIVERSE_COUNTS_COMPLETE_V1_37_1"
    }
    
    return {
        "selection_dataset": df_selection,
        "selection_frame": df_selection,
        "outcome_dataset": df_outcome,
        "outcome_frame": df_outcome,
        "opportunity_index": df_index,
        "reports": {
            "input_path_guard": path_guard,
            "count_sanity_guard": count_guard,
            "input_audit": input_audit,
            "join_policy_audit": join_report,
            "dedup_policy_audit": dedup_report,
            "warmup_policy_audit": warmup_report,
            "dataset_split_policy": split_policy,
            "selection_dataset_audit": selection_audit,
            "outcome_dataset_audit": outcome_audit,
            "opportunity_index_audit": index_audit,
            "warning_resolution_audit": warning_res_audit,
            "ev_feature_audit": ev_feature_audit_data,
            "cost_policy_audit": cost_policy_audit_data,
            "ev_filter_reference_audit": ref_audit,
            "leakage_audit": leakage_report,
            "fingerprint": fingerprint_report,
            "counts": counts
        }
    }
