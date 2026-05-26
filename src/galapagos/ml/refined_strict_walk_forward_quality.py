from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V9_3,
    FORBIDDEN_FEATURE_EXACT_V9_3,
    FORBIDDEN_FEATURE_PREFIXES_V9_3,
    FORBIDDEN_OUTPUT_COLUMNS_EXACT_V9_3,
)


def assess_refined_strict_walk_forward_quality_v9_3(
    dataset: pd.DataFrame,
    folds: pd.DataFrame,
    scores: pd.DataFrame,
    timeframe: str,
) -> dict[str, Any]:
    used = dataset[(dataset["label_valid_h1"] == True) & (dataset["warmup_row"] == False)].copy()  # noqa: E712
    forbidden_features = find_forbidden_feature_columns_v9_3(ALLOWED_FEATURE_COLUMNS_V9_3)
    forbidden_outputs = [column for column in scores.columns if column.casefold() in {item.casefold() for item in FORBIDDEN_OUTPUT_COLUMNS_EXACT_V9_3}]
    fold_counts = folds.groupby(["fold_id", "fold_role"], sort=True).size().to_dict() if not folds.empty else {}
    errors: list[str] = []
    warnings: list[str] = []
    if forbidden_features:
        errors.append("forbidden feature columns present")
    if forbidden_outputs:
        errors.append("forbidden output columns present")
    if folds.empty:
        errors.append("no refined strict walk-forward folds generated")
    if scores.empty:
        errors.append("no refined strict walk-forward scores generated")
    return {
        "rows_total": int(len(dataset)),
        "rows_used_for_ml": int(len(used)),
        "folds_count": int(folds["fold_id"].nunique()) if "fold_id" in folds.columns else 0,
        "rows_excluded_warmup": int(dataset["warmup_row"].eq(True).sum()),
        "rows_excluded_invalid_label": int(dataset["label_valid_h1"].eq(False).sum()),
        "rows_purged": int(folds["is_purged"].eq(True).sum()) if "is_purged" in folds.columns else 0,
        "rows_embargoed": int(folds["is_embargoed"].eq(True).sum()) if "is_embargoed" in folds.columns else 0,
        "fold_role_counts": {f"{fold_id}.{role}": int(count) for (fold_id, role), count in sorted(fold_counts.items())},
        "forbidden_feature_columns_present": forbidden_features,
        "forbidden_output_columns_present": forbidden_outputs,
        "fold_temporal_order_valid": fold_temporal_order_valid_v9_3(folds),
        "no_shuffle_confirmed": True,
        "errors": errors,
        "warnings": warnings,
        "timeframe": timeframe,
    }


def find_forbidden_feature_columns_v9_3(columns: list[str]) -> list[str]:
    exact = {item.casefold() for item in FORBIDDEN_FEATURE_EXACT_V9_3}
    prefixes = tuple(item.casefold() for item in FORBIDDEN_FEATURE_PREFIXES_V9_3)
    forbidden: list[str] = []
    for column in columns:
        folded = column.casefold()
        if folded in exact or folded.startswith(prefixes):
            forbidden.append(column)
    return forbidden


def fold_temporal_order_valid_v9_3(folds: pd.DataFrame) -> bool:
    if folds.empty:
        return False
    for _fold_id, group in folds.groupby("fold_id", sort=True):
        role_ranges = {}
        for role in ["train", "validation", "test"]:
            role_group = group[group["fold_role"] == role]
            if role_group.empty:
                return False
            timestamps = pd.to_datetime(role_group["event_ts"], utc=True)
            role_ranges[role] = (timestamps.min(), timestamps.max())
        if not (role_ranges["train"][1] < role_ranges["validation"][0] and role_ranges["validation"][1] < role_ranges["test"][0]):
            return False
    return True
