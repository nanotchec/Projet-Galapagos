from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import SGDClassifier
from sklearn.tree import DecisionTreeClassifier

from galapagos.datasets.ohlcv_aggtrades_exact_funding_5y_dataset_v9_60_schemas import (
    COMMON_WINDOW_LABEL,
    DATASET_BASE_PATH,
    FEATURE_COLUMNS,
    SELECTED_PRIMARY_LABEL,
    TIMEFRAMES,
)
from galapagos.features.funding_only_feature_store_v9_57_schemas import FEATURE_COLUMNS as FUNDING_FEATURE_COLUMNS
from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_v9_47_schemas import FEATURE_COLUMNS as BASE_FEATURE_COLUMNS
from galapagos.ml.ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62_metrics import classification_metrics_v9_62
from galapagos.ml.ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62_quality import (
    no_persistent_model_check_v9_62,
    scan_forbidden_features_v9_62,
    scan_forbidden_metrics_v9_62,
)


VERSION = "V9.62"
SOURCE_VERSION = "V9.61"
SOURCE_DATASET_VERSION = "V9.60"
TARGET_NAME = SELECTED_PRIMARY_LABEL
TARGET_CLASSES = ["DOWN", "FLAT", "UP"]
WINDOW = COMMON_WINDOW_LABEL
MODEL_NAMES = ["majority_class_baseline", "random_seeded_baseline", "logistic_regression", "decision_tree_depth_2"]
LEARNED_MODEL_NAMES = ["logistic_regression", "decision_tree_depth_2"]
FEATURE_VARIANT_WITHOUT_FUNDING = "without_funding"
FEATURE_VARIANT_WITH_FUNDING = "with_funding"
FEATURE_VARIANTS = (FEATURE_VARIANT_WITHOUT_FUNDING, FEATURE_VARIANT_WITH_FUNDING)
RANDOM_SEED = 42
NON_NUMERIC_FEATURE_COLUMNS = ("first_trade_ts", "last_trade_ts")
MODEL_FEATURE_COLUMNS_WITHOUT_FUNDING = tuple(column for column in BASE_FEATURE_COLUMNS if column not in NON_NUMERIC_FEATURE_COLUMNS)
MODEL_FEATURE_COLUMNS_WITH_FUNDING = tuple(column for column in FEATURE_COLUMNS if column not in NON_NUMERIC_FEATURE_COLUMNS)
ML_WORKERS = int(os.environ.get("GALAPAGOS_ML_WORKERS", "12"))

REPORT_JSON_PATH = Path("reports/ml/ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62.json")
REPORT_MD_PATH = Path("reports/ml/ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62.md")
SCORES_JSON_PATH = Path("reports/ml/ohlcv_aggtrades_exact_funding_5y_offline_scores_v9_62.json")
SCORES_MD_PATH = Path("reports/ml/ohlcv_aggtrades_exact_funding_5y_offline_scores_v9_62.md")
MANIFEST_PATH = Path("reports/manifests/ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62_manifest.json")
DOC_PATH = Path("docs/ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62.md")
V9_61_REPORT_PATH = Path("reports/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61.json")

SUCCESS_SOURCE_DECISIONS = {"funding_common_window_dataset_validated", "funding_common_window_dataset_validated_with_warnings"}

FINDINGS = {
    "robust_edge_claimed": False,
    "strategy_validated": False,
    "backtest_performed": False,
    "actionable_signal_produced": False,
    "walk_forward_validated_for_trading": False,
    "trading_allowed": False,
    "paper_live_allowed": False,
    "real_trading_allowed": False,
}

SAFETY_FLAGS = {
    "no_trading": True,
    "no_paper_live": True,
    "no_orders": True,
    "no_backtest": True,
    "no_walk_forward": True,
    "no_strategy": True,
    "no_actionable_signal": True,
    "no_persistent_model": True,
    "api_key_used": False,
    "private_endpoint_used": False,
    "exchange_auth_used": False,
    "websocket_live_used": False,
    "network_used": False,
    "no_new_data_download": True,
    "no_destructive_cleanup": True,
    "no_sidecars": True,
    "no_zip_fingerprints": True,
    "ml_executed": True,
    "offline_ml_only": True,
    "model_persisted": False,
    "walk_forward_executed": False,
    "backtest_executed": False,
    "signal_created": False,
    "strategy_created": False,
}


def run_offline_ml_v9_62(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    started = datetime.now(UTC)
    source_validation = _read_optional_json(root / V9_61_REPORT_PATH)
    if source_validation.get("decision") not in SUCCESS_SOURCE_DECISIONS:
        report = _blocked_report("funding_common_window_ml_blocked_by_dataset_issue", started, ["V9.61 dataset validation is not successful"])
        _write_outputs(root, report)
        return report

    ml_run_id = f"v9_62_ml_{started.strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    model_results_by_timeframe: dict[str, Any] = {}
    model_results_by_split: dict[str, Any] = {}
    shuffled_label_baseline_metrics: dict[str, Any] = {}
    original_vs_shuffled_delta: dict[str, Any] = {}
    dataset_inputs: dict[str, Any] = {}
    warnings: list[str] = []
    errors: list[str] = []

    feature_scans = {
        FEATURE_VARIANT_WITHOUT_FUNDING: scan_forbidden_features_v9_62(list(MODEL_FEATURE_COLUMNS_WITHOUT_FUNDING)),
        FEATURE_VARIANT_WITH_FUNDING: scan_forbidden_features_v9_62(list(MODEL_FEATURE_COLUMNS_WITH_FUNDING)),
    }
    if any(scan["status"] != "PASS" for scan in feature_scans.values()):
        errors.append("forbidden feature columns detected")

    for timeframe in TIMEFRAMES:
        dataset_path = dataset_path_v9_62(root, timeframe)
        dataset_inputs[timeframe] = _input_block(root, dataset_path)
        try:
            frame = read_ml_frame_v9_62(dataset_path)
            if frame.empty:
                errors.append(f"empty V9.62 ML frame for {timeframe}")
                continue
            timeframe_metrics, shuffle_metrics, shuffle_deltas, variant_rows = run_timeframe_models_v9_62(timeframe, frame)
            model_results_by_timeframe[timeframe] = {
                "rows_used": int(len(frame)),
                "train_rows": int(frame["split"].eq("train").sum()),
                "validation_rows": int(frame["split"].eq("validation").sum()),
                "test_rows": int(frame["split"].eq("test").sum()),
                "feature_variants": list(FEATURE_VARIANTS),
                "variant_feature_counts": {
                    FEATURE_VARIANT_WITHOUT_FUNDING: len(MODEL_FEATURE_COLUMNS_WITHOUT_FUNDING),
                    FEATURE_VARIANT_WITH_FUNDING: len(MODEL_FEATURE_COLUMNS_WITH_FUNDING),
                },
                "variant_rows": variant_rows,
                "models": MODEL_NAMES,
                "metrics": timeframe_metrics,
            }
            model_results_by_split.update(timeframe_metrics)
            shuffled_label_baseline_metrics.update(shuffle_metrics)
            original_vs_shuffled_delta.update(shuffle_deltas)
        except Exception as exc:  # pragma: no cover - integration failure path.
            errors.append(f"{timeframe}: {type(exc).__name__}: {exc}")

    baseline_comparison = baseline_comparison_v9_62(model_results_by_split)
    funding_ablation_comparison = funding_ablation_comparison_v9_62(model_results_by_split)
    no_clear_vs_shuffled_count = int(sum(1 for item in original_vs_shuffled_delta.values() if item["no_clear_edge_vs_shuffled_labels"]))
    class_collapse_analysis = class_collapse_analysis_v9_62(model_results_by_split)
    if no_clear_vs_shuffled_count:
        warnings.append("learned models are close to shuffled-label falsification on at least one evaluation split")
    if baseline_comparison["clear_wins_count"] == 0:
        warnings.append("learned models do not clearly beat majority/random baselines on evaluation splits")
    if funding_ablation_comparison["clear_improvement_with_funding_count"] == 0:
        warnings.append("funding variant does not show a clear aggregate improvement over no-funding variant")

    forbidden_metric_scan = scan_forbidden_metrics_v9_62(
        {
            "model_results_by_split": model_results_by_split,
            "baseline_comparison": baseline_comparison,
            "shuffled_label_baseline_metrics": shuffled_label_baseline_metrics,
            "funding_ablation_comparison": funding_ablation_comparison,
        }
    )
    no_model_check = no_persistent_model_check_v9_62(root)
    leakage_guard_status = "PASS" if not errors and all(scan["status"] == "PASS" for scan in feature_scans.values()) else "FAIL"
    quality_status = "PASS" if not errors and forbidden_metric_scan["status"] == "PASS" and no_model_check["status"] == "PASS" else "FAIL"
    decision = decide_v9_62(quality_status, leakage_guard_status, forbidden_metric_scan, baseline_comparison, funding_ablation_comparison, no_clear_vs_shuffled_count, class_collapse_analysis)
    runtime = (datetime.now(UTC) - started).total_seconds()

    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "source_dataset_version": SOURCE_DATASET_VERSION,
        "created_at_utc": _utc_now(),
        "ml_run_id": ml_run_id,
        "status": "PASS" if quality_status == "PASS" else "FAIL",
        "decision": decision,
        "target_name": TARGET_NAME,
        "target": TARGET_NAME,
        "common_window": {"label": COMMON_WINDOW_LABEL, "source_decision": source_validation.get("decision")},
        "dataset_inputs": dataset_inputs,
        "feature_variants": {
            FEATURE_VARIANT_WITHOUT_FUNDING: {
                "description": "OHLCV + aggTrades exact features only",
                "feature_columns": list(MODEL_FEATURE_COLUMNS_WITHOUT_FUNDING),
                "feature_columns_count": len(MODEL_FEATURE_COLUMNS_WITHOUT_FUNDING),
                "funding_features_included": False,
            },
            FEATURE_VARIANT_WITH_FUNDING: {
                "description": "OHLCV + aggTrades exact features plus funding features",
                "feature_columns": list(MODEL_FEATURE_COLUMNS_WITH_FUNDING),
                "feature_columns_count": len(MODEL_FEATURE_COLUMNS_WITH_FUNDING),
                "funding_features": list(FUNDING_FEATURE_COLUMNS),
                "funding_feature_columns_count": len(FUNDING_FEATURE_COLUMNS),
                "funding_features_included": True,
            },
        },
        "excluded_non_numeric_feature_columns": list(NON_NUMERIC_FEATURE_COLUMNS),
        "models_executed": MODEL_NAMES,
        "optional_models_executed": [],
        "ml_workers_requested": ML_WORKERS,
        "train_only_fit": True,
        "validation_test_not_used_for_fit": True,
        "same_window_same_splits_same_target": True,
        "random_seed": RANDOM_SEED,
        "model_results_by_timeframe": model_results_by_timeframe,
        "model_results_by_split": model_results_by_split,
        "baseline_comparison": baseline_comparison,
        "funding_ablation_comparison": funding_ablation_comparison,
        "shuffled_label_baseline_metrics": shuffled_label_baseline_metrics,
        "original_vs_shuffled_delta": original_vs_shuffled_delta,
        "no_clear_edge_vs_shuffled_labels_count": no_clear_vs_shuffled_count,
        "class_collapse_analysis": class_collapse_analysis,
        "warnings": warnings,
        "errors": errors,
        "limitations": [
            "V9.62 est un diagnostic ML offline classification-only.",
            "Aucun signal, strategie, backtest, walk-forward, ordre ou modele persistant n'est produit.",
            "Les metriques sont des resultats de recherche offline non actionnables et ne revendiquent aucun robust edge.",
        ],
        "quality_status": quality_status,
        "leakage_guard_status": leakage_guard_status,
        "forbidden_feature_scan": feature_scans,
        "forbidden_metric_scan": forbidden_metric_scan,
        "no_persistent_model_check": no_model_check,
        "dataset_created": False,
        "labels_created": False,
        "ml_executed": True,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "signal_created": False,
        "strategy_created": False,
        "model_persisted": False,
        "network_used": False,
        "new_data_downloaded": False,
        "findings": dict(FINDINGS),
        "safety_flags": dict(SAFETY_FLAGS),
        "next_recommendation": recommendation_v9_62(decision),
        "runtime_seconds": runtime,
    }
    _write_outputs(root, report)
    return report


def dataset_path_v9_62(root: Path, timeframe: str) -> Path:
    return root / DATASET_BASE_PATH / f"timeframe={timeframe}" / f"window={WINDOW}" / "dataset.parquet"


def read_ml_frame_v9_62(path: Path) -> pd.DataFrame:
    columns = [
        "timeframe",
        "decision_ts",
        "split",
        "row_valid_for_dataset",
        TARGET_NAME,
        *FEATURE_COLUMNS,
    ]
    frame = pd.read_parquet(path, columns=columns, engine="pyarrow")
    mask = (
        frame["row_valid_for_dataset"].eq(True)
        & frame[TARGET_NAME].notna()
        & frame["split"].isin(["train", "validation", "test"])
    )
    result = frame.loc[mask].reset_index(drop=True)
    result[TARGET_NAME] = result[TARGET_NAME].astype("int64").map({-1: "DOWN", 0: "FLAT", 1: "UP"}).astype(str)
    return result


def run_timeframe_models_v9_62(timeframe: str, frame: pd.DataFrame) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, int]]:
    metrics: dict[str, Any] = {}
    shuffled_metrics: dict[str, Any] = {}
    shuffle_deltas: dict[str, Any] = {}
    variant_rows: dict[str, int] = {}
    for feature_variant, columns in model_columns_by_variant_v9_62().items():
        train = frame[frame["split"] == "train"]
        variant_rows[feature_variant] = int(len(frame))
        predictions_by_model: dict[str, pd.Series] = {}
        for model_name in MODEL_NAMES:
            result = fit_predict_model_v9_62(model_name, train[list(columns)], train[TARGET_NAME].astype(str), frame[list(columns)])
            predictions_by_model[model_name] = result.predicted_class.reset_index(drop=True)
            for split, split_frame in frame.groupby("split", sort=True, observed=True):
                if split_frame.empty:
                    continue
                split_index = split_frame.index
                key = f"{timeframe}.{feature_variant}.{model_name}.{split}"
                metrics[key] = classification_metrics_v9_62(
                    timeframe=timeframe,
                    feature_variant=feature_variant,
                    model_name=model_name,
                    split=str(split),
                    y_true=split_frame[TARGET_NAME],
                    y_pred=predictions_by_model[model_name].iloc[split_index],
                )
        eval_frame = frame[frame["split"].isin(["validation", "test"])]
        shuffled_target = train[TARGET_NAME].sample(frac=1.0, random_state=RANDOM_SEED).reset_index(drop=True)
        for model_name in LEARNED_MODEL_NAMES:
            shuffled = fit_predict_model_v9_62(model_name, train[list(columns)], shuffled_target.astype(str), eval_frame[list(columns)])
            shuffled_predictions = shuffled.predicted_class.reset_index(drop=True)
            for split, split_frame in eval_frame.groupby("split", sort=True, observed=True):
                if split_frame.empty:
                    continue
                eval_positions = eval_frame.index.get_indexer(split_frame.index)
                shuffled_key = f"{timeframe}.{feature_variant}.{model_name}.shuffled_train_labels.{split}"
                original_key = f"{timeframe}.{feature_variant}.{model_name}.{split}"
                shuffled_metrics[shuffled_key] = classification_metrics_v9_62(
                    timeframe=timeframe,
                    feature_variant=feature_variant,
                    model_name=f"{model_name}_shuffled_train_labels",
                    split=str(split),
                    y_true=split_frame[TARGET_NAME],
                    y_pred=shuffled_predictions.iloc[eval_positions],
                )
                shuffle_deltas[original_key] = {
                    "timeframe": timeframe,
                    "feature_variant": feature_variant,
                    "model_name": model_name,
                    "split": str(split),
                    "original_accuracy": metrics[original_key]["accuracy"],
                    "shuffled_accuracy": shuffled_metrics[shuffled_key]["accuracy"],
                    "delta_accuracy_original_vs_shuffled": metrics[original_key]["accuracy"] - shuffled_metrics[shuffled_key]["accuracy"],
                    "original_macro_f1": metrics[original_key]["macro_f1"],
                    "shuffled_macro_f1": shuffled_metrics[shuffled_key]["macro_f1"],
                    "delta_macro_f1_original_vs_shuffled": metrics[original_key]["macro_f1"] - shuffled_metrics[shuffled_key]["macro_f1"],
                    "no_clear_edge_vs_shuffled_labels": (metrics[original_key]["macro_f1"] - shuffled_metrics[shuffled_key]["macro_f1"]) < 0.02,
                    "random_seed": RANDOM_SEED,
                    "diagnostic_only": True,
                }
    return metrics, shuffled_metrics, shuffle_deltas, variant_rows


def model_columns_by_variant_v9_62() -> dict[str, tuple[str, ...]]:
    return {
        FEATURE_VARIANT_WITHOUT_FUNDING: MODEL_FEATURE_COLUMNS_WITHOUT_FUNDING,
        FEATURE_VARIANT_WITH_FUNDING: MODEL_FEATURE_COLUMNS_WITH_FUNDING,
    }


def fit_predict_model_v9_62(
    model_name: str,
    train_features: pd.DataFrame,
    train_target: pd.Series,
    predict_features: pd.DataFrame,
) -> Any:
    if model_name == "majority_class_baseline":
        majority = str(train_target.value_counts().sort_values(ascending=False).index[0])
        return type("OfflineResult", (), {"predicted_class": pd.Series(majority, index=predict_features.index, name="research_predicted_class")})()
    if model_name == "random_seeded_baseline":
        distribution = train_target.value_counts(normalize=True).reindex(TARGET_CLASSES, fill_value=0.0)
        rng = np.random.default_rng(RANDOM_SEED)
        draws = rng.choice(TARGET_CLASSES, size=len(predict_features), p=distribution.to_numpy(dtype=float))
        return type("OfflineResult", (), {"predicted_class": pd.Series(draws, index=predict_features.index, name="research_predicted_class")})()
    if model_name == "logistic_regression":
        estimator = SGDClassifier(loss="log_loss", max_iter=8, tol=1e-3, shuffle=False, random_state=RANDOM_SEED, n_jobs=ML_WORKERS)
    elif model_name == "decision_tree_depth_2":
        estimator = DecisionTreeClassifier(max_depth=2, random_state=RANDOM_SEED)
    else:
        raise ValueError(f"unsupported V9.62 model: {model_name}")
    train_matrix = model_matrix_v9_62(train_features)
    predict_matrix = model_matrix_v9_62(predict_features)
    estimator.fit(train_matrix, train_target.to_numpy(dtype=str))
    predicted = pd.Series(estimator.predict(predict_matrix), index=predict_features.index, name="research_predicted_class")
    return type("OfflineResult", (), {"predicted_class": predicted.astype(str)})()


def model_matrix_v9_62(features: pd.DataFrame) -> np.ndarray:
    matrix = features.to_numpy(dtype=np.float32, copy=True)
    return np.nan_to_num(matrix, nan=0.0, posinf=0.0, neginf=0.0, copy=False)


def baseline_comparison_v9_62(metrics: dict[str, Any]) -> dict[str, Any]:
    comparisons: dict[str, Any] = {}
    for key, item in metrics.items():
        if item["model_name"] not in LEARNED_MODEL_NAMES or item["split"] not in {"validation", "test"}:
            continue
        baselines = [
            metric
            for metric in metrics.values()
            if metric["timeframe"] == item["timeframe"]
            and metric["feature_variant"] == item["feature_variant"]
            and metric["split"] == item["split"]
            and metric["model_name"] in {"majority_class_baseline", "random_seeded_baseline"}
        ]
        best_macro = max((metric["macro_f1"] for metric in baselines), default=0.0)
        best_accuracy = max((metric["accuracy"] for metric in baselines), default=0.0)
        comparisons[key] = {
            "timeframe": item["timeframe"],
            "feature_variant": item["feature_variant"],
            "model_name": item["model_name"],
            "split": item["split"],
            "accuracy": item["accuracy"],
            "macro_f1": item["macro_f1"],
            "delta_accuracy_vs_best_baseline": item["accuracy"] - best_accuracy,
            "delta_macro_f1_vs_best_baseline": item["macro_f1"] - best_macro,
            "clear_win_vs_baseline": (item["macro_f1"] - best_macro) > 0.02,
        }
    return {
        "comparisons": comparisons,
        "clear_wins_count": int(sum(1 for item in comparisons.values() if item["clear_win_vs_baseline"])),
        "weak_vs_baselines_count": int(sum(1 for item in comparisons.values() if not item["clear_win_vs_baseline"])),
        "mean_delta_macro_f1_vs_best_baseline": mean_v9_62([item["delta_macro_f1_vs_best_baseline"] for item in comparisons.values()]),
        "classification_only": True,
    }


def funding_ablation_comparison_v9_62(metrics: dict[str, Any]) -> dict[str, Any]:
    comparisons: dict[str, Any] = {}
    for key, with_item in metrics.items():
        if with_item["feature_variant"] != FEATURE_VARIANT_WITH_FUNDING:
            continue
        if with_item["model_name"] not in LEARNED_MODEL_NAMES or with_item["split"] not in {"validation", "test"}:
            continue
        without_key = key.replace(f".{FEATURE_VARIANT_WITH_FUNDING}.", f".{FEATURE_VARIANT_WITHOUT_FUNDING}.")
        without_item = metrics.get(without_key)
        if not without_item:
            continue
        comparisons[key] = {
            "timeframe": with_item["timeframe"],
            "model_name": with_item["model_name"],
            "split": with_item["split"],
            "with_funding_macro_f1": with_item["macro_f1"],
            "without_funding_macro_f1": without_item["macro_f1"],
            "delta_macro_f1_with_vs_without_funding": with_item["macro_f1"] - without_item["macro_f1"],
            "with_funding_balanced_accuracy": with_item["balanced_accuracy"],
            "without_funding_balanced_accuracy": without_item["balanced_accuracy"],
            "delta_balanced_accuracy_with_vs_without_funding": with_item["balanced_accuracy"] - without_item["balanced_accuracy"],
            "clear_improvement_with_funding": (with_item["macro_f1"] - without_item["macro_f1"]) > 0.01,
        }
    deltas = [item["delta_macro_f1_with_vs_without_funding"] for item in comparisons.values()]
    return {
        "comparisons": comparisons,
        "clear_improvement_with_funding_count": int(sum(1 for item in comparisons.values() if item["clear_improvement_with_funding"])),
        "weak_or_negative_with_funding_count": int(sum(1 for item in comparisons.values() if not item["clear_improvement_with_funding"])),
        "mean_delta_macro_f1_with_vs_without_funding": mean_v9_62(deltas),
        "best_delta_macro_f1_with_vs_without_funding": max(deltas) if deltas else 0.0,
        "worst_delta_macro_f1_with_vs_without_funding": min(deltas) if deltas else 0.0,
        "same_target_window_splits_models_preprocessing": True,
    }


def class_collapse_analysis_v9_62(metrics: dict[str, Any]) -> dict[str, Any]:
    warnings: dict[str, Any] = {}
    for key, item in metrics.items():
        if item.get("model_name") not in LEARNED_MODEL_NAMES or item.get("split") not in {"validation", "test"}:
            continue
        rows = max(int(item.get("rows", 0)), 1)
        prediction_distribution = item.get("prediction_distribution", {})
        max_pred_ratio = max((value / rows for value in prediction_distribution.values()), default=0.0)
        recall = item.get("per_class_recall", {})
        down_recall = float(recall.get("DOWN", 0.0))
        up_recall = float(recall.get("UP", 0.0))
        if max_pred_ratio > 0.90 or down_recall < 0.02 or up_recall < 0.02:
            warnings[key] = {
                "timeframe": item.get("timeframe"),
                "feature_variant": item.get("feature_variant"),
                "model_name": item.get("model_name"),
                "split": item.get("split"),
                "max_prediction_ratio": max_pred_ratio,
                "down_recall": down_recall,
                "up_recall": up_recall,
                "class_collapse_warning": True,
            }
    return {"collapse_warnings": warnings, "collapse_warning_count": len(warnings)}


def decide_v9_62(
    quality_status: str,
    leakage_guard_status: str,
    forbidden_metric_scan: dict[str, Any],
    baseline_comparison: dict[str, Any],
    funding_ablation_comparison: dict[str, Any],
    no_clear_vs_shuffled_count: int,
    class_collapse_analysis: dict[str, Any],
) -> str:
    if leakage_guard_status != "PASS":
        return "funding_common_window_ml_blocked_by_leakage"
    if forbidden_metric_scan["status"] != "PASS":
        return "funding_common_window_ml_blocked_by_forbidden_metrics"
    if quality_status != "PASS":
        return "funding_common_window_ml_blocked_by_dataset_issue"
    if class_collapse_analysis["collapse_warning_count"] > 0:
        return "funding_common_window_ml_completed_but_class_collapse"
    if no_clear_vs_shuffled_count > 0:
        return "funding_common_window_ml_completed_but_close_to_shuffled_labels"
    if baseline_comparison["clear_wins_count"] == 0 or funding_ablation_comparison["clear_improvement_with_funding_count"] == 0:
        return "funding_common_window_ml_completed_but_weak_vs_baselines"
    return "funding_common_window_ml_completed_with_improvement"


def recommendation_v9_62(decision: str) -> str:
    if decision == "funding_common_window_ml_completed_with_improvement":
        return "V9.63 - Strict walk-forward design gate"
    if decision == "funding_common_window_ml_completed_but_class_collapse":
        return "V9.63 - Target/label balance diagnostic"
    if decision in {"funding_common_window_ml_completed_but_weak_vs_baselines", "funding_common_window_ml_completed_but_close_to_shuffled_labels"}:
        return "V9.63 - Feature/label diagnostic before walk-forward"
    return "V9.63 - Dataset or leakage correction"


def _blocked_report(decision: str, started: datetime, errors: list[str]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "source_dataset_version": SOURCE_DATASET_VERSION,
        "created_at_utc": _utc_now(),
        "status": "FAIL",
        "decision": decision,
        "target_name": TARGET_NAME,
        "feature_variants": {},
        "models_executed": [],
        "errors": errors,
        "warnings": [],
        "quality_status": "FAIL",
        "leakage_guard_status": "NOT_RUN",
        "forbidden_metric_scan": {"status": "NOT_RUN", "forbidden_terms_present": []},
        "no_persistent_model_check": no_persistent_model_check_v9_62(Path(".")),
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "signal_created": False,
        "strategy_created": False,
        "model_persisted": False,
        "network_used": False,
        "new_data_downloaded": False,
        "findings": dict(FINDINGS),
        "safety_flags": {**SAFETY_FLAGS, "ml_executed": False},
        "next_recommendation": "V9.63 - Dataset correction",
        "runtime_seconds": (datetime.now(UTC) - started).total_seconds(),
    }


def _write_outputs(root: Path, report: dict[str, Any]) -> None:
    scores_payload = {
        "version": VERSION,
        "ml_run_id": report.get("ml_run_id"),
        "target_name": report.get("target_name"),
        "models_executed": report.get("models_executed", []),
        "feature_variants": list(report.get("feature_variants", {}).keys()),
        "model_results_by_split": report.get("model_results_by_split", {}),
        "baseline_comparison": report.get("baseline_comparison", {}),
        "funding_ablation_comparison": report.get("funding_ablation_comparison", {}),
        "shuffled_label_baseline_metrics": report.get("shuffled_label_baseline_metrics", {}),
        "original_vs_shuffled_delta": report.get("original_vs_shuffled_delta", {}),
        "class_collapse_analysis": report.get("class_collapse_analysis", {}),
        "classification_only": True,
        "contains_predictions": False,
        "contains_actionable_signal": False,
    }
    manifest = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": _utc_now(),
        "decision": report["decision"],
        "report_path": REPORT_JSON_PATH.as_posix(),
        "scores_path": SCORES_JSON_PATH.as_posix(),
        "target_name": report.get("target_name"),
        "models_executed": report.get("models_executed", []),
        "quality_status": report.get("quality_status"),
        "leakage_guard_status": report.get("leakage_guard_status"),
        "findings": report.get("findings"),
        "safety_flags": report.get("safety_flags"),
        "artifacts": {
            "json_report": REPORT_JSON_PATH.as_posix(),
            "md_report": REPORT_MD_PATH.as_posix(),
            "scores_json": SCORES_JSON_PATH.as_posix(),
            "scores_md": SCORES_MD_PATH.as_posix(),
            "doc": DOC_PATH.as_posix(),
        },
    }
    _write_json(root / REPORT_JSON_PATH, report)
    _write_json(root / SCORES_JSON_PATH, scores_payload)
    _write_json(root / MANIFEST_PATH, manifest)
    markdown = markdown_v9_62(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / SCORES_MD_PATH, scores_markdown_v9_62(scores_payload, report))
    _write_text(root / DOC_PATH, markdown)


def markdown_v9_62(report: dict[str, Any]) -> str:
    lines = [
        "# V9.62 - Funding common window ML offline",
        "",
        "V9.62 execute un diagnostic ML offline research-only comparant OHLCV + aggTrades exact sans funding et avec funding sur la meme fenetre commune.",
        "",
        f"- Decision : `{report['decision']}`.",
        f"- Target : `{report.get('target_name')}`.",
        f"- Modeles executes : `{', '.join(report.get('models_executed', []))}`.",
        f"- Qualite : `{report.get('quality_status')}`.",
        f"- Leakage guard : `{report.get('leakage_guard_status')}`.",
        f"- Clear improvements funding : `{report.get('funding_ablation_comparison', {}).get('clear_improvement_with_funding_count', 0)}`.",
        f"- No-clear vs shuffled labels : `{report.get('no_clear_edge_vs_shuffled_labels_count', 0)}`.",
        "",
        "## Synthese par timeframe",
    ]
    for timeframe, block in report.get("model_results_by_timeframe", {}).items():
        lines.append(f"- `{timeframe}` : `{block['rows_used']}` lignes valides ML.")
    lines.extend(
        [
            "",
            "## Garde-fous",
            "- Aucun trading reel.",
            "- Aucun paper live.",
            "- Aucun ordre.",
            "- Aucun backtest.",
            "- Aucun walk-forward.",
            "- Aucune strategie.",
            "- Aucun signal actionnable.",
            "- Aucun modele persistant.",
            "- Aucun reseau et aucun telechargement.",
            "- Aucun resultat actionnable.",
        ]
    )
    return "\n".join(lines) + "\n"


def scores_markdown_v9_62(scores_payload: dict[str, Any], report: dict[str, Any]) -> str:
    lines = [
        "# Scores agreges V9.62",
        "",
        "Ce fichier contient uniquement des metriques agregees classification-only. Il ne contient aucune prediction exploitable comme signal.",
        "",
        f"- Target : `{scores_payload['target_name']}`.",
        f"- Modeles : `{', '.join(scores_payload['models_executed'])}`.",
        f"- Variantes : `{', '.join(scores_payload['feature_variants'])}`.",
        f"- Comparaisons funding : `{len(report.get('funding_ablation_comparison', {}).get('comparisons', {}))}`.",
        f"- Comparaisons shuffled : `{len(report.get('original_vs_shuffled_delta', {}))}`.",
        "- Signal actionnable : `false`.",
    ]
    return "\n".join(lines) + "\n"


def mean_v9_62(values: list[float]) -> float:
    return float(sum(values) / max(len(values), 1))


def _input_block(root: Path, path: Path) -> dict[str, Any]:
    return {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size if path.is_file() else 0, "exists": path.is_file()}


def _read_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
