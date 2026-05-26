from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from galapagos.features.ohlcv_trades_feature_selection_schemas import (
    ALLOWED_FEATURE_COLUMNS_V8_9,
    AUDIT_ONLY_COLUMNS_V8_9,
    FEATURE_FAMILY_BY_COLUMN_V8_9,
    FORBIDDEN_FEATURE_EXACT_V8_9,
    FORBIDDEN_FEATURE_PREFIXES_V8_9,
    REQUIRED_CORE_FEATURES_V8_9,
    SOURCE_TYPES_V8_9,
)


def classify_feature_family_v8_9(feature_name: str) -> str:
    return FEATURE_FAMILY_BY_COLUMN_V8_9.get(feature_name, "unknown")


def classify_source_type_v8_9(feature_name: str) -> str:
    return SOURCE_TYPES_V8_9.get(classify_feature_family_v8_9(feature_name), "unknown")


def is_forbidden_feature_v8_9(feature_name: str) -> bool:
    lowered = feature_name.casefold()
    return lowered in FORBIDDEN_FEATURE_EXACT_V8_9 or any(
        lowered.startswith(prefix.casefold()) for prefix in FORBIDDEN_FEATURE_PREFIXES_V8_9
    )


def build_leakage_guard_v8_9(features: list[str]) -> dict[str, Any]:
    forbidden = sorted(feature for feature in features if is_forbidden_feature_v8_9(feature))
    return {
        "forbidden_features_present": forbidden,
        "checked_features_count": len(features),
        "passed": not forbidden,
    }


def build_feature_family_balance_v8_9(
    feature_inventory: list[dict[str, Any]],
    selected_features: list[str] | None = None,
    review_features: list[str] | None = None,
) -> dict[str, Any]:
    selected = set(selected_features or [])
    review = set(review_features or [])
    inventory_counts = Counter(item["feature_family"] for item in feature_inventory)
    allowed_counts = Counter(item["feature_family"] for item in feature_inventory if item["allowed_for_ml"])
    selected_counts = Counter(item["feature_family"] for item in feature_inventory if item["feature_name"] in selected)
    review_counts = Counter(item["feature_family"] for item in feature_inventory if item["feature_name"] in review)
    total_allowed = sum(allowed_counts.values()) or 1
    overrepresented = sorted(
        family for family, count in allowed_counts.items() if count / total_allowed > 0.30 and family not in {"ohlcv_base"}
    )
    underrepresented = sorted(family for family, count in allowed_counts.items() if count <= 2)
    return {
        "inventory_count_by_family": dict(sorted(inventory_counts.items())),
        "allowed_count_by_family": dict(sorted(allowed_counts.items())),
        "selected_count_by_family": dict(sorted(selected_counts.items())),
        "review_count_by_family": dict(sorted(review_counts.items())),
        "overrepresented_families": overrepresented,
        "underrepresented_families": underrepresented,
        "families_to_refactor_or_merge": sorted({"trade_aggregation", "trade_intensity", "rolling_trade"} & set(overrepresented)),
        "notes": [
            "Les familles trade_aggregation, trade_intensity et rolling_trade contiennent plusieurs mesures derivees proches.",
            "La balance est descriptive et ne constitue pas une importance modele.",
        ],
    }


def select_refined_features_v8_9(
    feature_inventory: list[dict[str, Any]],
    missingness_summary: dict[str, Any],
    variance_summary: dict[str, Any],
    collinearity_summary: dict[str, Any],
    stability_by_timeframe: dict[str, Any],
) -> dict[str, Any]:
    redundant = set(collinearity_summary.get("redundant_features", []))
    required = [feature for feature in REQUIRED_CORE_FEATURES_V8_9 if feature in ALLOWED_FEATURE_COLUMNS_V8_9]
    missing_flags = _features_with_flag(missingness_summary, "suspicious_missingness")
    zero_variance = _features_with_flag(variance_summary, "zero_variance")
    near_constant = _features_with_flag(variance_summary, "near_constant")
    outlier_flags = _features_with_flag(variance_summary, "extreme_outlier_flag")
    unstable_families = set(stability_by_timeframe.get("families_to_review", []))

    selected: list[str] = []
    dropped: list[str] = []
    review: list[str] = []
    reasons: dict[str, dict[str, Any]] = {}

    for item in feature_inventory:
        feature = item["feature_name"]
        family = item["feature_family"]
        decision = "keep_core"
        reasons_for_feature: list[str] = []
        if feature in AUDIT_ONLY_COLUMNS_V8_9 or not item["allowed_for_ml"]:
            decision = "drop_audit_only" if family == "audit" else "review_domain_logic"
            reasons_for_feature.append(item.get("excluded_reason") or "not_allowed_for_ml")
        elif is_forbidden_feature_v8_9(feature):
            decision = "drop_audit_only"
            reasons_for_feature.append("forbidden_leakage_or_output_name")
        elif feature in zero_variance:
            decision = "drop_constant"
            reasons_for_feature.append("zero_variance")
        elif feature in redundant and feature not in required:
            decision = "drop_redundant"
            reasons_for_feature.append("high_pairwise_correlation_cluster")
        elif feature in missing_flags:
            decision = "review_high_missingness"
            reasons_for_feature.append("suspicious_missingness")
        elif feature in near_constant or feature in outlier_flags:
            decision = "review_domain_logic"
            if feature in near_constant:
                reasons_for_feature.append("near_constant")
            if feature in outlier_flags:
                reasons_for_feature.append("extreme_outlier_flag")
        elif family in unstable_families and feature not in required:
            decision = "review_unstable"
            reasons_for_feature.append("family_associated_with_unstable_timeframe_diagnostics")
        else:
            decision = "keep_core" if feature in required else "keep_but_monitor"
            reasons_for_feature.append("core_or_diversifying_feature")

        if decision.startswith("drop_"):
            dropped.append(feature)
        elif decision.startswith("review_"):
            review.append(feature)
        else:
            selected.append(feature)
        reasons[feature] = {
            "decision": decision,
            "feature_family": family,
            "reasons": reasons_for_feature,
        }

    selected = _preserve_allowed_order(selected)
    dropped = _preserve_inventory_order(dropped, feature_inventory)
    review = _preserve_inventory_order(review, feature_inventory)
    leakage_guard = build_leakage_guard_v8_9(selected)
    return {
        "selected_features_count": len(selected),
        "dropped_features_count": len(dropped),
        "review_features_count": len(review),
        "required_features": required,
        "selected_features": selected,
        "dropped_features": dropped,
        "review_features": review,
        "excluded_audit_columns": [feature for feature in AUDIT_ONLY_COLUMNS_V8_9 if feature in dropped],
        "reasons_by_feature": reasons,
        "decision_categories": sorted(set(reason["decision"] for reason in reasons.values())),
        "leakage_guard": leakage_guard,
    }


def _features_with_flag(summary: dict[str, Any], flag_name: str) -> set[str]:
    features: set[str] = set()
    for timeframe_payload in summary.get("by_timeframe", {}).values():
        for feature, payload in timeframe_payload.items():
            if payload.get(flag_name) is True:
                features.add(feature)
    return features


def _preserve_allowed_order(features: list[str]) -> list[str]:
    selected = set(features)
    return [feature for feature in ALLOWED_FEATURE_COLUMNS_V8_9 if feature in selected]


def _preserve_inventory_order(features: list[str], feature_inventory: list[dict[str, Any]]) -> list[str]:
    selected = set(features)
    return [item["feature_name"] for item in feature_inventory if item["feature_name"] in selected]
