from __future__ import annotations

import hashlib
import json
import uuid
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.ohlcv_trades_1y_window_validation import validate_ohlcv_trades_1y_offline_supervised_dataset_v8_4
from galapagos.features.ohlcv_trades_feature_selection import (
    build_feature_family_balance_v8_9,
    build_leakage_guard_v8_9,
    classify_feature_family_v8_9,
    classify_source_type_v8_9,
    is_forbidden_feature_v8_9,
    select_refined_features_v8_9,
)
from galapagos.features.ohlcv_trades_feature_selection_schemas import (
    ALLOWED_FEATURE_COLUMNS_V8_9,
    ALL_V8_3_DATASET_FEATURE_COLUMNS_V8_9,
    ARTIFACT_INVENTORY_JSON_V8_9,
    ATTESTATION_JSON_V8_9,
    AUDIT_ONLY_COLUMNS_V8_9,
    COLLINEARITY_SAMPLE_ROWS_PER_TIMEFRAME_V8_9,
    COLLINEARITY_SAMPLE_SEED_V8_9,
    COLLINEARITY_THRESHOLD_V8_9,
    DOC_PATH_V8_9,
    EXPECTED_LIMITATIONS_V8_9,
    FINDINGS_FALSE_FIELDS_V8_9,
    INPUT_DATASET_MANIFEST_PATH_V8_9,
    INPUT_DECISION_JSON_PATH_V8_9,
    INPUT_DECISION_MD_PATH_V8_9,
    INPUT_FEATURE_MANIFEST_PATH_V8_9,
    INPUT_FEATURE_REPORT_PATH_V8_9,
    INPUT_ML_MANIFEST_PATH_V8_9,
    INPUT_ML_REPORT_PATH_V8_9,
    INPUT_WALK_FORWARD_MANIFEST_PATH_V8_9,
    INPUT_WALK_FORWARD_REPORT_PATH_V8_9,
    MANIFEST_PATH_V8_9,
    ORIGINAL_FEATURE_COLUMNS_COUNT_V8_9,
    REPORT_JSON_PATH_V8_9,
    REPORT_MD_PATH_V8_9,
    SAFETY_FLAGS_V8_9,
    SELECTION_JSON_PATH_V8_9,
    SELECTION_MD_PATH_V8_9,
    TIMEFRAMES_V8_9,
    VERSION_V8_9,
    ZIP_SIZE_JSON_V8_9,
)
from galapagos.ml.strict_walk_forward_validation import validate_strict_walk_forward_validation_v8_7


def run_ohlcv_trades_feature_audit_v8_9(
    root: Path = Path("."),
    *,
    validate_inputs: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_inputs:
        _validate_inputs(root)

    dataset_manifest = _load_json(root / INPUT_DATASET_MANIFEST_PATH_V8_9)
    feature_manifest = _load_json(root / INPUT_FEATURE_MANIFEST_PATH_V8_9)
    walk_forward_available = (root / INPUT_WALK_FORWARD_MANIFEST_PATH_V8_9).exists()
    walk_forward_manifest = _load_json(root / INPUT_WALK_FORWARD_MANIFEST_PATH_V8_9) if walk_forward_available else {}
    ml_manifest = _load_json(root / INPUT_ML_MANIFEST_PATH_V8_9)
    decision_gate = _load_json(root / INPUT_DECISION_JSON_PATH_V8_9)

    created_at = utc_now_iso()
    run_id = f"v8_9_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    dataset_frames = _load_dataset_frames(root, dataset_manifest)
    feature_inventory = build_feature_inventory_v8_9(dataset_frames, feature_manifest)
    missingness_summary = build_missingness_summary_v8_9(dataset_frames, feature_inventory)
    variance_summary = build_variance_summary_v8_9(dataset_frames, feature_inventory)
    collinearity_summary = build_collinearity_summary_v8_9(dataset_frames)
    stability_by_timeframe = build_stability_by_timeframe_v8_9(walk_forward_manifest, decision_gate)
    candidate = select_refined_features_v8_9(
        feature_inventory,
        missingness_summary,
        variance_summary,
        collinearity_summary,
        stability_by_timeframe,
    )
    feature_family_balance = build_feature_family_balance_v8_9(
        feature_inventory,
        candidate["selected_features"],
        candidate["review_features"],
    )
    leakage_guard = build_leakage_guard_v8_9(candidate["selected_features"])
    warnings = _collect_warnings(candidate, collinearity_summary, stability_by_timeframe, decision_gate)
    manifest = {
        "version": VERSION_V8_9,
        "status": "PASS" if leakage_guard["passed"] else "FAIL",
        "created_at_utc": created_at,
        "feature_audit_run_id": run_id,
        "input_dataset_manifest": {
            "path": INPUT_DATASET_MANIFEST_PATH_V8_9.as_posix(),
            "sha256": sha256_file(root / INPUT_DATASET_MANIFEST_PATH_V8_9),
            "window_start": dataset_manifest["input_features_manifest"]["window_start"],
            "window_end": dataset_manifest["input_features_manifest"]["window_end"],
            "total_days": dataset_manifest["input_features_manifest"]["total_days"],
            "feature_columns_count": ORIGINAL_FEATURE_COLUMNS_COUNT_V8_9,
            "dataset_feature_columns_count_raw": dataset_manifest["feature_columns_count"],
        },
        "input_feature_manifest": {
            "path": INPUT_FEATURE_MANIFEST_PATH_V8_9.as_posix(),
            "sha256": sha256_file(root / INPUT_FEATURE_MANIFEST_PATH_V8_9),
        },
        "input_feature_report": {
            "path": INPUT_FEATURE_REPORT_PATH_V8_9.as_posix(),
            "sha256": sha256_file(root / INPUT_FEATURE_REPORT_PATH_V8_9),
        },
        "input_ml_manifest": {
            "path": INPUT_ML_MANIFEST_PATH_V8_9.as_posix(),
            "sha256": sha256_file(root / INPUT_ML_MANIFEST_PATH_V8_9),
            "available": True,
            "feature_columns_count": ml_manifest.get("feature_columns_count"),
        },
        "input_walk_forward_manifest": {
            "path": INPUT_WALK_FORWARD_MANIFEST_PATH_V8_9.as_posix(),
            "sha256": sha256_file(root / INPUT_WALK_FORWARD_MANIFEST_PATH_V8_9) if walk_forward_available else None,
            "available": walk_forward_available,
        },
        "input_decision_gate_v8_8": {
            "path": INPUT_DECISION_JSON_PATH_V8_9.as_posix(),
            "sha256": sha256_file(root / INPUT_DECISION_JSON_PATH_V8_9),
            "summary_verdict": decision_gate.get("summary_verdict"),
            "recommended_next_step": decision_gate.get("recommended_next_step"),
        },
        "feature_inventory": feature_inventory,
        "missingness_summary": missingness_summary,
        "variance_summary": variance_summary,
        "collinearity_summary": collinearity_summary,
        "feature_family_balance": feature_family_balance,
        "stability_by_timeframe": stability_by_timeframe,
        "candidate_refined_feature_set": candidate,
        "leakage_guard": leakage_guard,
        "findings": {
            "feature_set_validated_for_trading": False,
            "strategy_validated": False,
            "backtest_performed": False,
            "actionable_signal_produced": False,
            "warnings": warnings,
        },
        "safety": SAFETY_FLAGS_V8_9,
        "limitations": EXPECTED_LIMITATIONS_V8_9,
    }
    _write_json(root / MANIFEST_PATH_V8_9, manifest)
    _write_json(root / REPORT_JSON_PATH_V8_9, manifest)
    selection_report = build_selection_report_v8_9(manifest)
    _write_json(root / SELECTION_JSON_PATH_V8_9, selection_report)
    audit_markdown = build_feature_audit_markdown_v8_9(manifest)
    selection_markdown = build_feature_selection_markdown_v8_9(selection_report)
    _write_text(root / REPORT_MD_PATH_V8_9, audit_markdown)
    _write_text(root / DOC_PATH_V8_9, audit_markdown)
    _write_text(root / SELECTION_MD_PATH_V8_9, selection_markdown)
    update_project_state_v8_9(root, manifest)
    return manifest


def build_feature_inventory_v8_9(dataset_frames: dict[str, pd.DataFrame], feature_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    first_frame = dataset_frames[TIMEFRAMES_V8_9[0]]
    feature_schema_columns = set(feature_manifest["feature_columns"])
    inventory: list[dict[str, Any]] = []
    for feature in ALL_V8_3_DATASET_FEATURE_COLUMNS_V8_9:
        family = classify_feature_family_v8_9(feature)
        allowed = feature in ALLOWED_FEATURE_COLUMNS_V8_9 and not is_forbidden_feature_v8_9(feature)
        excluded_reason = None
        if is_forbidden_feature_v8_9(feature):
            excluded_reason = "forbidden_feature_name"
        elif feature in AUDIT_ONLY_COLUMNS_V8_9 or family == "audit":
            excluded_reason = "audit_only_not_ml_feature"
        elif feature not in ALLOWED_FEATURE_COLUMNS_V8_9:
            excluded_reason = "not_in_v8_7_allowed_ml_features"
        inventory.append(
            {
                "feature_name": feature,
                "feature_family": family,
                "source_type": classify_source_type_v8_9(feature),
                "dtype": str(first_frame[feature].dtype) if feature in first_frame.columns else "missing",
                "present_in_v8_3_schema": feature in feature_schema_columns,
                "present_in_v8_4_dataset": all(feature in frame.columns for frame in dataset_frames.values()),
                "allowed_for_ml": allowed,
                "excluded_reason": excluded_reason,
            }
        )
    return inventory


def build_missingness_summary_v8_9(dataset_frames: dict[str, pd.DataFrame], feature_inventory: list[dict[str, Any]]) -> dict[str, Any]:
    by_timeframe: dict[str, dict[str, Any]] = {}
    suspicious: dict[str, list[str]] = {}
    for timeframe, frame in dataset_frames.items():
        warmup_mask = frame["warmup_row"].astype(bool) if "warmup_row" in frame else pd.Series(False, index=frame.index)
        post_warmup_rows = int((~warmup_mask).sum())
        by_timeframe[timeframe] = {}
        for item in feature_inventory:
            feature = item["feature_name"]
            series = frame[feature]
            numeric = _numeric_series(series) if _is_numeric_like(series) else None
            null_count = int(series.isna().sum())
            inf_count = int(np.isinf(numeric).sum()) if numeric is not None else 0
            post = series[~warmup_mask]
            post_null_rate = float(post.isna().mean()) if len(post) else 0.0
            suspicious_flag = post_null_rate > 0.05 or (inf_count / max(len(series), 1)) > 0.0
            if suspicious_flag:
                suspicious.setdefault(timeframe, []).append(feature)
            by_timeframe[timeframe][feature] = {
                "null_count": null_count,
                "null_rate": round(null_count / max(len(series), 1), 8),
                "inf_count": inf_count,
                "inf_rate": round(inf_count / max(len(series), 1), 8),
                "warmup_dependency": bool(feature.endswith("_rolling_mean_60") or feature.endswith("_zscore_60") or feature.endswith("_lag_1")),
                "post_warmup_null_rate": round(post_null_rate, 8),
                "suspicious_missingness": suspicious_flag,
            }
    return {
        "by_timeframe": by_timeframe,
        "suspicious_features_by_timeframe": suspicious,
        "timeframes": TIMEFRAMES_V8_9,
    }


def build_variance_summary_v8_9(dataset_frames: dict[str, pd.DataFrame], feature_inventory: list[dict[str, Any]]) -> dict[str, Any]:
    by_timeframe: dict[str, dict[str, Any]] = {}
    for timeframe, frame in dataset_frames.items():
        by_timeframe[timeframe] = {}
        for item in feature_inventory:
            feature = item["feature_name"]
            series = frame[feature]
            numeric = _numeric_series(series) if _is_numeric_like(series) else None
            unique_count = int(series.nunique(dropna=True))
            variance = float(numeric.var(skipna=True)) if numeric is not None else 0.0
            top_frequency = float(series.value_counts(dropna=True, normalize=True).iloc[0]) if unique_count else 0.0
            zero_variance = unique_count <= 1
            near_constant = bool(unique_count <= 2 or top_frequency >= 0.995)
            outlier_flag = _extreme_outlier_flag(numeric) if numeric is not None else False
            if zero_variance:
                suggested_action = "drop_constant"
            elif outlier_flag:
                suggested_action = "review_outliers"
            elif near_constant:
                suggested_action = "review_missingness"
            else:
                suggested_action = "keep"
            by_timeframe[timeframe][feature] = {
                "variance": _finite_float(variance),
                "unique_count": unique_count,
                "zero_variance": zero_variance,
                "near_constant": near_constant,
                "extreme_outlier_flag": outlier_flag,
                "suggested_action": suggested_action,
            }
    return {"by_timeframe": by_timeframe}


def build_collinearity_summary_v8_9(dataset_frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    samples: list[pd.DataFrame] = []
    rows_by_timeframe: dict[str, int] = {}
    for index, timeframe in enumerate(TIMEFRAMES_V8_9):
        frame = dataset_frames[timeframe]
        base = frame.loc[~frame["warmup_row"].astype(bool), ALLOWED_FEATURE_COLUMNS_V8_9]
        rows = min(COLLINEARITY_SAMPLE_ROWS_PER_TIMEFRAME_V8_9, len(base))
        sample = base.sample(n=rows, random_state=COLLINEARITY_SAMPLE_SEED_V8_9 + index) if rows else base
        samples.append(sample)
        rows_by_timeframe[timeframe] = int(rows)
    sample_frame = pd.concat(samples, ignore_index=True)
    numeric = sample_frame.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    corr = numeric.corr(method="pearson").abs()
    high_pairs: list[dict[str, Any]] = []
    parent = {feature: feature for feature in ALLOWED_FEATURE_COLUMNS_V8_9}
    for i, left in enumerate(ALLOWED_FEATURE_COLUMNS_V8_9):
        for right in ALLOWED_FEATURE_COLUMNS_V8_9[i + 1 :]:
            value = corr.loc[left, right]
            if pd.notna(value) and float(value) >= COLLINEARITY_THRESHOLD_V8_9:
                high_pairs.append({"feature_a": left, "feature_b": right, "abs_correlation": round(float(value), 6)})
                _union(parent, left, right)
    clusters_raw: dict[str, list[str]] = defaultdict(list)
    for feature in ALLOWED_FEATURE_COLUMNS_V8_9:
        clusters_raw[_find(parent, feature)].append(feature)
    clusters: list[dict[str, Any]] = []
    redundant: list[str] = []
    for cluster_features in clusters_raw.values():
        if len(cluster_features) <= 1:
            continue
        representative = _choose_representative(cluster_features)
        cluster_redundant = [feature for feature in cluster_features if feature != representative]
        redundant.extend(cluster_redundant)
        clusters.append(
            {
                "representative_feature": representative,
                "redundant_features": cluster_redundant,
                "features": cluster_features,
                "suggested_action": "keep_representative_review_redundant_features",
            }
        )
    return {
        "sample_strategy": {
            "method": "deterministic_per_timeframe_sample",
            "correlation_method": "pearson",
            "sample_seed": COLLINEARITY_SAMPLE_SEED_V8_9,
            "max_rows_per_timeframe": COLLINEARITY_SAMPLE_ROWS_PER_TIMEFRAME_V8_9,
            "rows_sampled_by_timeframe": rows_by_timeframe,
            "labels_used": False,
            "future_columns_used": False,
        },
        "high_correlation_threshold": COLLINEARITY_THRESHOLD_V8_9,
        "high_correlation_pairs_count": len(high_pairs),
        "high_correlation_pairs": sorted(high_pairs, key=lambda item: item["abs_correlation"], reverse=True)[:200],
        "feature_clusters": clusters,
        "redundant_features": sorted(set(redundant), key=ALLOWED_FEATURE_COLUMNS_V8_9.index),
    }


def build_stability_by_timeframe_v8_9(walk_forward_manifest: dict[str, Any], decision_gate: dict[str, Any]) -> dict[str, Any]:
    if not walk_forward_manifest:
        return {
            "attribution_supported": False,
            "reason": "V8.7 walk-forward manifest unavailable.",
            "families_to_review": ["trade_aggregation", "trade_intensity", "rolling_trade", "microstructure_proxy"],
        }
    aggregate = walk_forward_manifest.get("aggregate_metrics", {})
    unstable_entries = {
        key: value.get("unstable_folds", [])
        for key, value in aggregate.items()
        if value.get("unstable_folds") or value.get("fold_concentration_warnings")
    }
    return {
        "attribution_supported": False,
        "reason": "Les rapports V8.5/V8.7 ne fournissent pas d'importance feature; l'instabilite ne peut pas etre attribuee proprement a une feature precise.",
        "decision_gate_v8_8_verdict": decision_gate.get("summary_verdict"),
        "unstable_model_timeframe_entries": unstable_entries,
        "families_to_review": ["trade_aggregation", "trade_intensity", "rolling_trade", "microstructure_proxy"],
        "descriptive_only": True,
    }


def build_selection_report_v8_9(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION_V8_9,
        "status": manifest["status"],
        "created_at_utc": manifest["created_at_utc"],
        "feature_audit_run_id": manifest["feature_audit_run_id"],
        "candidate_refined_feature_set": manifest["candidate_refined_feature_set"],
        "feature_family_balance": manifest["feature_family_balance"],
        "leakage_guard": manifest["leakage_guard"],
        "findings": manifest["findings"],
        "safety": manifest["safety"],
        "limitations": manifest["limitations"],
    }


def build_feature_audit_markdown_v8_9(manifest: dict[str, Any]) -> str:
    candidate = manifest["candidate_refined_feature_set"]
    balance = manifest["feature_family_balance"]
    leakage = manifest["leakage_guard"]
    lines = [
        "# OHLCV + Trades feature audit V8.9",
        "",
        "## 1. Executive summary",
        "",
        "- V8.9 audite et propose uniquement une selection/refactorisation de features OHLCV + aggTrades.",
        "- V8.9 ne valide aucune strategie.",
        "- V8.9 ne valide aucun modele exploitable en trading.",
        "- V8.9 ne valide pas les features pour trading.",
        "- V8.9 ne produit aucun backtest.",
        "- V8.9 ne produit aucun signal de trading.",
        "- V8.9 ne produit aucun ordre.",
        "- La selection proposee est une hypothese de recherche pour V9.0.",
        "",
        "## 2. Inputs",
        "",
        f"- Fenetre : `{manifest['input_dataset_manifest']['window_start']}` -> `{manifest['input_dataset_manifest']['window_end']}`.",
        f"- Total jours : `{manifest['input_dataset_manifest']['total_days']}`.",
        f"- Feature columns ML originales : `{manifest['input_dataset_manifest']['feature_columns_count']}`.",
        f"- V8.8 verdict : `{manifest['input_decision_gate_v8_8']['summary_verdict']}`.",
        "",
        "## 3. Feature inventory",
        "",
        f"- Features inventoriees : `{len(manifest['feature_inventory'])}`.",
        f"- Features autorisees ML : `{sum(1 for item in manifest['feature_inventory'] if item['allowed_for_ml'])}`.",
        f"- Comptage par famille : `{balance['inventory_count_by_family']}`.",
        "",
        "## 4. Missingness / warmup audit",
        "",
        f"- Timeframes audites : `{manifest['missingness_summary']['timeframes']}`.",
        f"- Suspicious missingness : `{manifest['missingness_summary']['suspicious_features_by_timeframe']}`.",
        "",
        "## 5. Variance / degeneracy audit",
        "",
        "- Les constantes, quasi constantes et outliers extremes sont marques pour drop ou revue.",
        "",
        "## 6. Collinearity audit",
        "",
        f"- Methode : `{manifest['collinearity_summary']['sample_strategy']['correlation_method']}`.",
        f"- Seuil high correlation : `{manifest['collinearity_summary']['high_correlation_threshold']}`.",
        f"- Paires fortement correlees : `{manifest['collinearity_summary']['high_correlation_pairs_count']}`.",
        f"- Clusters : `{len(manifest['collinearity_summary']['feature_clusters'])}`.",
        "",
        "## 7. Feature family balance",
        "",
        f"- Families surrepresentees : `{balance['overrepresented_families']}`.",
        f"- Families a refactoriser/fusionner : `{balance['families_to_refactor_or_merge']}`.",
        "",
        "## 8. Candidate refined feature set",
        "",
        f"- Selected features : `{candidate['selected_features_count']}`.",
        f"- Dropped features : `{candidate['dropped_features_count']}`.",
        f"- Review features : `{candidate['review_features_count']}`.",
        f"- Selected : `{candidate['selected_features']}`.",
        f"- Dropped : `{candidate['dropped_features']}`.",
        f"- Review : `{candidate['review_features']}`.",
        "",
        "## 9. Leakage guard",
        "",
        f"- Passed : `{leakage['passed']}`.",
        f"- Forbidden selected features : `{leakage['forbidden_features_present']}`.",
        "",
        "## 10. Risks and limitations",
        "",
        "- L'audit ne recalcule pas de nouvelles features.",
        "- L'audit ne cree pas de dataset V9.0.",
        "- L'audit n'entraine aucun modele ML.",
        "- Les diagnostics V8.5/V8.7 ne permettent pas d'attribuer causalement l'instabilite a une feature precise.",
        "- La selection proposee doit etre revalidee dans V9.0/V9.x.",
        "",
        "## 11. Recommended V9.0 direction",
        "",
        "- Construire un feature store raffine avec le set selectionne et les features en revue traitees explicitement.",
        "- Revalider ensuite le dataset, le ML offline et le strict walk-forward.",
        "",
        "## 12. Interdits maintenus",
        "",
        "- Pas de trading.",
        "- Pas de paper live.",
        "- Pas d'ordre.",
        "- Pas de nouveau dataset.",
        "- Pas de modele ML.",
        "- Pas de backtest.",
        "- Pas de strategie.",
        "- Pas de signal de trading.",
        "- Pas de claim de rentabilite.",
    ]
    return "\n".join(lines) + "\n"


def build_feature_selection_markdown_v8_9(selection_report: dict[str, Any]) -> str:
    candidate = selection_report["candidate_refined_feature_set"]
    return (
        "# OHLCV + Trades feature selection V8.9\n\n"
        f"- Selected features : `{candidate['selected_features_count']}`.\n"
        f"- Dropped features : `{candidate['dropped_features_count']}`.\n"
        f"- Review features : `{candidate['review_features_count']}`.\n"
        "- Cette selection est une hypothese de recherche pour V9.0, pas une validation trading.\n"
        "- V8.9 ne valide aucune strategie.\n"
        "- V8.9 ne produit aucun backtest.\n"
        "- V8.9 ne produit aucun signal de trading.\n"
        "- V8.9 ne produit aucun ordre.\n\n"
        "## Selected\n\n"
        + "\n".join(f"- {feature}" for feature in candidate["selected_features"])
        + "\n\n## Dropped\n\n"
        + "\n".join(f"- {feature}" for feature in candidate["dropped_features"])
        + "\n\n## Review\n\n"
        + "\n".join(f"- {feature}" for feature in candidate["review_features"])
        + "\n"
    )


def update_project_state_v8_9(root: Path, manifest: dict[str, Any]) -> None:
    candidate = manifest["candidate_refined_feature_set"]
    state_path = root / "reports/PROJECT_STATE.json"
    state = _load_json(state_path)
    state.update(
        {
            "last_validated_version": "V8.8",
            "candidate_version": VERSION_V8_9,
            "candidate_status": "pending_external_audit",
            "direction": "OHLCV + trades feature audit / selection",
            "ohlcv_trades_feature_audit_v8_9_created": True,
            "feature_audit_window_start_v8_9": manifest["input_dataset_manifest"]["window_start"],
            "feature_audit_window_end_v8_9": manifest["input_dataset_manifest"]["window_end"],
            "feature_audit_total_days_v8_9": manifest["input_dataset_manifest"]["total_days"],
            "original_feature_columns_count_v8_9": manifest["input_dataset_manifest"]["feature_columns_count"],
            "selected_features_count_v8_9": candidate["selected_features_count"],
            "dropped_features_count_v8_9": candidate["dropped_features_count"],
            "review_features_count_v8_9": candidate["review_features_count"],
            "new_dataset_v8_9_created": False,
            "model_v8_9_created": False,
            "ml_v8_9_created": False,
            "backtest_v8_9_created": False,
            "strategy_v8_9_created": False,
            "signal_v8_9_created": False,
            "orders_v8_9_created": False,
            "paper_live_v8_9_created": False,
            "trading_v8_9_created": False,
        }
    )
    _write_json(state_path, state)
    metrics = {
        "last_validated_version": "V8.8",
        "candidate_version": VERSION_V8_9,
        "candidate_status": "pending_external_audit",
        "direction": "OHLCV + trades feature audit / selection",
        "window_start": manifest["input_dataset_manifest"]["window_start"],
        "window_end": manifest["input_dataset_manifest"]["window_end"],
        "total_days": manifest["input_dataset_manifest"]["total_days"],
        "original_feature_columns_count": manifest["input_dataset_manifest"]["feature_columns_count"],
        "selected_features_count": candidate["selected_features_count"],
        "dropped_features_count": candidate["dropped_features_count"],
        "review_features_count": candidate["review_features_count"],
        "selected_count_by_family": manifest["feature_family_balance"]["selected_count_by_family"],
        "review_count_by_family": manifest["feature_family_balance"]["review_count_by_family"],
        "new_dataset_created": False,
        "model_created": False,
        "backtest_enabled": False,
        "strategy_enabled": False,
        "signal_created": False,
        "orders_enabled": False,
        "trading_enabled": False,
        "paper_live_enabled": False,
        "external_validation_required": True,
    }
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    _write_text(root / "reports/PROJECT_STATE.md", _project_state_markdown(manifest))
    _write_text(root / "reports/current/latest_metrics.md", _latest_metrics_markdown(metrics))
    _write_text(root / "reports/current/latest_summary.md", _latest_summary_markdown(manifest))
    _write_text(root / "README.md", _readme_markdown(manifest))


def _load_dataset_frames(root: Path, dataset_manifest: dict[str, Any]) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    columns = ["warmup_row", *ALL_V8_3_DATASET_FEATURE_COLUMNS_V8_9]
    deduped_columns = list(dict.fromkeys(columns))
    for timeframe in TIMEFRAMES_V8_9:
        path = root / dataset_manifest["outputs"][timeframe]["path"]
        frame = read_parquet(path)
        frames[timeframe] = frame[deduped_columns].copy()
    return frames


def _validate_inputs(root: Path) -> None:
    dataset_result = validate_ohlcv_trades_1y_offline_supervised_dataset_v8_4(root)
    if not dataset_result["passed"]:
        raise RuntimeError(f"V8.4 dataset validation failed before V8.9: {dataset_result['errors']}")
    if (root / INPUT_WALK_FORWARD_MANIFEST_PATH_V8_9).exists():
        walk_forward_result = validate_strict_walk_forward_validation_v8_7(root)
        if not walk_forward_result["passed"]:
            raise RuntimeError(f"V8.7 walk-forward validation failed before V8.9: {walk_forward_result['errors']}")


def _collect_warnings(
    candidate: dict[str, Any],
    collinearity_summary: dict[str, Any],
    stability_by_timeframe: dict[str, Any],
    decision_gate: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    if candidate["review_features_count"]:
        warnings.append(f"{candidate['review_features_count']} features require review before V9.0.")
    if collinearity_summary["feature_clusters"]:
        warnings.append(f"{len(collinearity_summary['feature_clusters'])} high-correlation clusters detected.")
    if stability_by_timeframe.get("attribution_supported") is False:
        warnings.append("Feature-level instability attribution is not supported by V8.5/V8.7 reports.")
    if decision_gate.get("label_shuffle_assessment", {}).get("no_clear_edge_vs_shuffled_labels_count", 0) > 0:
        warnings.append("V8.8 reported labels-shuffle proximity; feature selection must be revalidated.")
    return warnings


def _extreme_outlier_flag(series: pd.Series | None) -> bool:
    if series is None:
        return False
    clean = series.dropna()
    if len(clean) < 100:
        return False
    q1 = clean.quantile(0.25)
    q3 = clean.quantile(0.75)
    iqr = q3 - q1
    if not np.isfinite(iqr) or iqr == 0:
        return False
    lower = q1 - 50 * iqr
    upper = q3 + 50 * iqr
    return bool(((clean < lower) | (clean > upper)).mean() > 0.001)


def _is_numeric_like(series: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series)


def _numeric_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").astype("float64")


def _finite_float(value: float) -> float | None:
    return float(value) if np.isfinite(value) else None


def _find(parent: dict[str, str], item: str) -> str:
    while parent[item] != item:
        parent[item] = parent[parent[item]]
        item = parent[item]
    return item


def _union(parent: dict[str, str], left: str, right: str) -> None:
    root_left = _find(parent, left)
    root_right = _find(parent, right)
    if root_left != root_right:
        parent[root_right] = root_left


def _choose_representative(features: list[str]) -> str:
    for required in ALL_V8_3_DATASET_FEATURE_COLUMNS_V8_9:
        if required in features and required in ALLOWED_FEATURE_COLUMNS_V8_9:
            return required
    return sorted(features)[0]


def _project_state_markdown(manifest: dict[str, Any]) -> str:
    candidate = manifest["candidate_refined_feature_set"]
    return f"""# Etat du Projet : V8.8 validee + candidat V8.9

- **Derniere version validee** : V8.8.
- **Version candidate** : V8.9.
- **Statut candidate** : `pending_external_audit`.
- **Direction** : OHLCV + trades feature audit / selection.

## Candidat V8.9

- Fenetre : `{manifest['input_dataset_manifest']['window_start']}` -> `{manifest['input_dataset_manifest']['window_end']}`.
- Nombre de jours : `{manifest['input_dataset_manifest']['total_days']}`.
- Feature columns originales : `{manifest['input_dataset_manifest']['feature_columns_count']}`.
- Selected features : `{candidate['selected_features_count']}`.
- Dropped features : `{candidate['dropped_features_count']}`.
- Review features : `{candidate['review_features_count']}`.
- Aucun nouveau dataset, aucun modele ML et aucun backtest.

## Clause De Securite

- Aucun trading reel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucune strategie.
- Aucun signal de trading.
- Aucun modele ML.
- Aucune API privee.
- Aucune cle API.
- V8.9 reste non validee avant audit externe.
"""


def _latest_summary_markdown(manifest: dict[str, Any]) -> str:
    candidate = manifest["candidate_refined_feature_set"]
    return f"""# Latest Summary V8.9

V8.8 est la derniere version validee localement.

V8.9 est la candidate courante. Elle produit un audit et une selection/refactorisation de features OHLCV + aggTrades a partir des artefacts V8.3/V8.4/V8.5/V8.7/V8.8, sans recalculer les features et sans entrainer de modele.

Fenetre : `{manifest['input_dataset_manifest']['window_start']}` -> `{manifest['input_dataset_manifest']['window_end']}`.

Total jours : `{manifest['input_dataset_manifest']['total_days']}`.

Feature columns originales : `{manifest['input_dataset_manifest']['feature_columns_count']}`.

Selected features : `{candidate['selected_features_count']}`.

Dropped features : `{candidate['dropped_features_count']}`.

Review features : `{candidate['review_features_count']}`.

Aucun nouveau dataset, aucun modele ML, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live et aucun trading reel.

V8.9 reste `pending_external_audit`.
"""


def _latest_metrics_markdown(metrics: dict[str, Any]) -> str:
    return f"""# Latest Metrics V8.9

- Derniere version validee : V8.8.
- Candidate : V8.9.
- Statut : `pending_external_audit`.
- Direction : OHLCV + trades feature audit / selection.
- Fenetre : `{metrics['window_start']}` -> `{metrics['window_end']}`.
- Total jours : `{metrics['total_days']}`.
- Feature columns originales : `{metrics['original_feature_columns_count']}`.
- Selected features : `{metrics['selected_features_count']}`.
- Dropped features : `{metrics['dropped_features_count']}`.
- Review features : `{metrics['review_features_count']}`.
- Families retenues : `{metrics['selected_count_by_family']}`.
- Families a revoir : `{metrics['review_count_by_family']}`.

Aucun nouveau dataset, aucun modele ML, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre et aucun trading reel.
"""


def _readme_markdown(manifest: dict[str, Any]) -> str:
    candidate = manifest["candidate_refined_feature_set"]
    return f"""# Projet Galapagos

- Derniere version validee : V8.8.
- Candidate : V8.9, OHLCV + trades feature audit / selection.

V8.9 audite et propose une selection/refactorisation des features OHLCV + aggTrades existantes sans recalculer les features, sans creer de dataset et sans entrainer de modele.

Fenetre : `{manifest['input_dataset_manifest']['window_start']}` -> `{manifest['input_dataset_manifest']['window_end']}`, `{manifest['input_dataset_manifest']['total_days']}` jours.

Feature columns originales : `{manifest['input_dataset_manifest']['feature_columns_count']}`.

Selected / dropped / review : `{candidate['selected_features_count']}` / `{candidate['dropped_features_count']}` / `{candidate['review_features_count']}`.

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live, aucun trading reel et aucun modele ML.

## Commandes V8.9

```bash
python scripts/run_ohlcv_trades_feature_audit_v8_9.py
python scripts/validate_ohlcv_trades_feature_audit_v8_9.py
python -m pytest -q tests/features/test_ohlcv_trades_feature_audit_v8_9.py
python -m pytest -q tests/validation/test_ohlcv_trades_feature_audit_v8_9_validator.py
python scripts/release_audit_lite_zip_v8_9.py
python scripts/audit_audit_lite_zip_v8_9.py --zip projet-galapagos-v8.9-audit-lite.zip
python scripts/smoke_audit_lite_zip_v8_9.py --zip projet-galapagos-v8.9-audit-lite.zip
python -m pytest --collect-only -q
```
"""


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
