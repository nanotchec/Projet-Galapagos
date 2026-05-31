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

from galapagos.datasets.ohlcv_aggtrades_exact_5y_dataset_v9_49_schemas import (
    DATASET_BASE_PATH,
    FEATURE_COLUMNS,
    SELECTED_PRIMARY_LABEL,
    TIMEFRAMES,
)
from galapagos.ml.ohlcv_aggtrades_exact_5y_offline_ml_v9_51_metrics import classification_metrics_v9_51
from galapagos.ml.ohlcv_aggtrades_exact_5y_offline_ml_v9_51_quality import (
    no_persistent_model_check_v9_51,
    scan_forbidden_features_v9_51,
    scan_forbidden_metrics_v9_51,
)


VERSION = "V9.51"
SOURCE_VERSION = "V9.50"
SOURCE_DATASET_VERSION = "V9.49"
TARGET_NAME = SELECTED_PRIMARY_LABEL
MODEL_NAMES = ["majority_class_baseline", "random_seeded_baseline", "logistic_regression", "decision_tree_depth_2"]
LEARNED_MODEL_NAMES = ["logistic_regression", "decision_tree_depth_2"]
RANDOM_SEED = 42
TARGET_CLASSES = ["DOWN", "FLAT", "UP"]
WINDOW = "2021-05-05_2026-05-05"
NON_NUMERIC_FEATURE_COLUMNS = ("first_trade_ts", "last_trade_ts")
MODEL_FEATURE_COLUMNS = tuple(column for column in FEATURE_COLUMNS if column not in NON_NUMERIC_FEATURE_COLUMNS)
ML_WORKERS = int(os.environ.get("GALAPAGOS_ML_WORKERS", "12"))

REPORT_JSON_PATH = Path("reports/ml/ohlcv_aggtrades_exact_5y_offline_ml_v9_51.json")
REPORT_MD_PATH = Path("reports/ml/ohlcv_aggtrades_exact_5y_offline_ml_v9_51.md")
SCORES_JSON_PATH = Path("reports/ml/ohlcv_aggtrades_exact_5y_offline_scores_v9_51.json")
SCORES_MD_PATH = Path("reports/ml/ohlcv_aggtrades_exact_5y_offline_scores_v9_51.md")
MANIFEST_PATH = Path("reports/manifests/ohlcv_aggtrades_exact_5y_offline_ml_v9_51_manifest.json")
DOC_PATH = Path("docs/ohlcv_aggtrades_exact_5y_offline_ml_v9_51.md")

V9_42_REPORT_PATH = Path("reports/datasets/ohlcv_aggtrades_exact_5y_dataset_validation_v9_50.json")
V9_41_REPORT_PATH = Path("reports/datasets/ohlcv_aggtrades_exact_5y_dataset_v9_49.json")
V9_48_REPORT_PATH = Path("reports/features/ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.json")
V9_40_LABEL_REPORT_PATH = Path("reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40.json")
V9_43_REPORT_PATH = Path("reports/ml/ohlcv_aggtrades_5y_offline_ml_v9_43.json")

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
    "model_persisted": False,
    "backtest_executed": False,
    "signal_created": False,
    "strategy_created": False,
}


def run_offline_ml_v9_51(root: Path = Path(".")) -> dict[str, Any]:
    started = datetime.now(UTC)
    root = root.resolve()
    source_validation = _read_json(root / V9_42_REPORT_PATH)
    if source_validation.get("decision") not in {"combined_features_5y_dataset_validated", "combined_features_5y_dataset_validated_with_warnings"}:
        report = _blocked_report("combined_features_5y_ml_blocked_by_dataset_issue", started, ["V9.50 dataset validation decision is not validated"])
        _write_outputs(root, report)
        return report

    ml_run_id = f"v9_51_ml_{started.strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    model_results_by_timeframe: dict[str, Any] = {}
    model_results_by_split: dict[str, Any] = {}
    shuffled_label_baseline_metrics: dict[str, Any] = {}
    original_vs_shuffled_delta: dict[str, Any] = {}
    dataset_inputs: dict[str, Any] = {}
    warnings: list[str] = []
    errors: list[str] = []

    feature_scan = scan_forbidden_features_v9_51(list(FEATURE_COLUMNS))
    if feature_scan["status"] != "PASS":
        errors.append("forbidden feature columns detected")

    for timeframe in TIMEFRAMES:
        dataset_path = _dataset_path(root, timeframe)
        dataset_inputs[timeframe] = _input_block(root, dataset_path)
        frame = _read_ml_frame(dataset_path)
        if frame.empty:
            errors.append(f"empty V9.51 ML frame for {timeframe}")
            continue
        timeframe_metrics, shuffle_metrics, shuffle_deltas = _run_timeframe_models(timeframe, frame)
        model_results_by_timeframe[timeframe] = {
            "rows_used": int(len(frame)),
            "train_rows": int(frame["split"].eq("train").sum()),
            "validation_rows": int(frame["split"].eq("validation").sum()),
            "test_rows": int(frame["split"].eq("test").sum()),
            "models": MODEL_NAMES,
            "metrics": timeframe_metrics,
        }
        model_results_by_split.update(timeframe_metrics)
        shuffled_label_baseline_metrics.update(shuffle_metrics)
        original_vs_shuffled_delta.update(shuffle_deltas)

    baseline_comparison = _baseline_comparison(model_results_by_split)
    no_clear_vs_shuffled_count = int(sum(1 for item in original_vs_shuffled_delta.values() if item["no_clear_edge_vs_shuffled_labels"]))
    class_collapse_analysis = _class_collapse_analysis(model_results_by_split)
    comparison_to_v9_43 = _compare_to_v9_43(root, model_results_by_split, baseline_comparison, no_clear_vs_shuffled_count, class_collapse_analysis)
    close_to_shuffled_warnings = [
        key for key, item in original_vs_shuffled_delta.items() if item["no_clear_edge_vs_shuffled_labels"]
    ]
    if close_to_shuffled_warnings:
        warnings.append("learned models are close to shuffled-label falsification on at least one evaluation split")
    if baseline_comparison["clear_wins_count"] == 0:
        warnings.append("learned models do not clearly beat majority/random baselines on evaluation splits")

    forbidden_metric_scan = scan_forbidden_metrics_v9_51(
        {
            "model_results_by_split": model_results_by_split,
            "baseline_comparison": baseline_comparison,
            "shuffled_label_baseline_metrics": shuffled_label_baseline_metrics,
        }
    )
    no_model_check = no_persistent_model_check_v9_51()
    leakage_guard_status = "PASS" if not errors and feature_scan["status"] == "PASS" else "FAIL"
    quality_status = "PASS" if not errors and forbidden_metric_scan["status"] == "PASS" else "FAIL"
    decision = _decide(quality_status, leakage_guard_status, forbidden_metric_scan, baseline_comparison, no_clear_vs_shuffled_count, class_collapse_analysis, comparison_to_v9_43)
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
        "dataset_inputs": dataset_inputs,
        "feature_columns": list(FEATURE_COLUMNS),
        "feature_columns_count": len(FEATURE_COLUMNS),
        "model_feature_columns": list(MODEL_FEATURE_COLUMNS),
        "model_feature_columns_count": len(MODEL_FEATURE_COLUMNS),
        "excluded_non_numeric_feature_columns": list(NON_NUMERIC_FEATURE_COLUMNS),
        "feature_source_version": "V9.48",
        "base_feature_columns_count": 41,
        "exact_feature_columns_count": 56,
        "models_executed": MODEL_NAMES,
        "optional_models_executed": [],
        "ml_workers_requested": ML_WORKERS,
        "train_only_fit": True,
        "validation_test_not_used_for_fit": True,
        "shuffle_false_for_split_construction": True,
        "random_seed": RANDOM_SEED,
        "model_results_by_timeframe": model_results_by_timeframe,
        "model_results_by_split": model_results_by_split,
        "baseline_comparison": baseline_comparison,
        "shuffled_label_baseline_metrics": shuffled_label_baseline_metrics,
        "original_vs_shuffled_delta": original_vs_shuffled_delta,
        "no_clear_edge_vs_shuffled_labels_count": no_clear_vs_shuffled_count,
        "class_collapse_analysis": class_collapse_analysis,
        "comparison_to_v9_43": comparison_to_v9_43,
        "close_to_shuffled_warnings": close_to_shuffled_warnings,
        "warnings": warnings,
        "errors": errors,
        "limitations": [
            "V9.51 est un diagnostic ML offline classification-only.",
            "Aucun signal, strategie, backtest, ordre ou modele persistant n'est produit.",
            "Les resultats ne sont pas une validation de robust edge et ne sont pas actionnables.",
        ],
        "quality_status": quality_status,
        "leakage_guard_status": leakage_guard_status,
        "forbidden_feature_scan": feature_scan,
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
        "next_recommendation": _recommendation(decision),
        "runtime_seconds": runtime,
    }
    _write_outputs(root, report)
    return report


def _run_timeframe_models(timeframe: str, frame: pd.DataFrame) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    train = frame[frame["split"] == "train"]
    metrics: dict[str, Any] = {}
    predictions_by_model: dict[str, pd.Series] = {}
    for model_name in MODEL_NAMES:
        result = _fit_predict_model_v9_51(model_name, train[list(MODEL_FEATURE_COLUMNS)], train[TARGET_NAME].astype(str), frame[list(MODEL_FEATURE_COLUMNS)])
        predictions_by_model[model_name] = result.predicted_class.reset_index(drop=True)
        for split, split_frame in frame.groupby("split", sort=True, observed=True):
            if split_frame.empty:
                continue
            split_index = split_frame.index
            key = f"{timeframe}.{model_name}.{split}"
            metrics[key] = classification_metrics_v9_51(
                timeframe=timeframe,
                model_name=model_name,
                split=str(split),
                y_true=split_frame[TARGET_NAME],
                y_pred=predictions_by_model[model_name].iloc[split_index],
            )
    shuffle_metrics: dict[str, Any] = {}
    shuffle_deltas: dict[str, Any] = {}
    eval_frame = frame[frame["split"].isin(["validation", "test"])]
    shuffled_target = train[TARGET_NAME].sample(frac=1.0, random_state=RANDOM_SEED).reset_index(drop=True)
    for model_name in LEARNED_MODEL_NAMES:
        shuffled = _fit_predict_model_v9_51(model_name, train[list(MODEL_FEATURE_COLUMNS)], shuffled_target.astype(str), eval_frame[list(MODEL_FEATURE_COLUMNS)])
        shuffled_predictions = shuffled.predicted_class.reset_index(drop=True)
        for split, split_frame in eval_frame.groupby("split", sort=True, observed=True):
            if split_frame.empty:
                continue
            eval_positions = eval_frame.index.get_indexer(split_frame.index)
            shuffled_key = f"{timeframe}.{model_name}.shuffled_train_labels.{split}"
            original_key = f"{timeframe}.{model_name}.{split}"
            shuffle_metrics[shuffled_key] = classification_metrics_v9_51(
                timeframe=timeframe,
                model_name=f"{model_name}_shuffled_train_labels",
                split=str(split),
                y_true=split_frame[TARGET_NAME],
                y_pred=shuffled_predictions.iloc[eval_positions],
            )
            delta_key = f"{timeframe}.{model_name}.{split}"
            shuffle_deltas[delta_key] = {
                "timeframe": timeframe,
                "model_name": model_name,
                "split": str(split),
                "original_accuracy": metrics[original_key]["accuracy"],
                "shuffled_accuracy": shuffle_metrics[shuffled_key]["accuracy"],
                "delta_accuracy_original_vs_shuffled": metrics[original_key]["accuracy"] - shuffle_metrics[shuffled_key]["accuracy"],
                "original_macro_f1": metrics[original_key]["macro_f1"],
                "shuffled_macro_f1": shuffle_metrics[shuffled_key]["macro_f1"],
                "delta_macro_f1_original_vs_shuffled": metrics[original_key]["macro_f1"] - shuffle_metrics[shuffled_key]["macro_f1"],
                "no_clear_edge_vs_shuffled_labels": (metrics[original_key]["macro_f1"] - shuffle_metrics[shuffled_key]["macro_f1"]) < 0.02,
                "random_seed": RANDOM_SEED,
                "diagnostic_only": True,
            }
    return metrics, shuffle_metrics, shuffle_deltas


def _fit_predict_model_v9_51(
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
        estimator = SGDClassifier(
            loss="log_loss",
            max_iter=8,
            tol=1e-3,
            shuffle=False,
            random_state=RANDOM_SEED,
            n_jobs=ML_WORKERS,
        )
    elif model_name == "decision_tree_depth_2":
        estimator = DecisionTreeClassifier(max_depth=2, random_state=RANDOM_SEED)
    else:
        raise ValueError(f"unsupported V9.51 model: {model_name}")
    train_matrix = _model_matrix_v9_51(train_features)
    predict_matrix = _model_matrix_v9_51(predict_features)
    estimator.fit(train_matrix, train_target.to_numpy(dtype=str))
    predicted = pd.Series(estimator.predict(predict_matrix), index=predict_features.index, name="research_predicted_class")
    return type("OfflineResult", (), {"predicted_class": predicted.astype(str)})()


def _model_matrix_v9_51(features: pd.DataFrame) -> np.ndarray:
    matrix = features.to_numpy(dtype=np.float32, copy=True)
    return np.nan_to_num(matrix, nan=0.0, posinf=0.0, neginf=0.0, copy=False)


def _baseline_comparison(metrics: dict[str, Any]) -> dict[str, Any]:
    comparisons: dict[str, Any] = {}
    for key, item in metrics.items():
        if item["model_name"] not in LEARNED_MODEL_NAMES or item["split"] not in {"validation", "test"}:
            continue
        baselines = [
            metric
            for metric in metrics.values()
            if metric["timeframe"] == item["timeframe"]
            and metric["split"] == item["split"]
            and metric["model_name"] in {"majority_class_baseline", "random_seeded_baseline"}
        ]
        best_macro = max((metric["macro_f1"] for metric in baselines), default=0.0)
        best_accuracy = max((metric["accuracy"] for metric in baselines), default=0.0)
        comparisons[key] = {
            "timeframe": item["timeframe"],
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
        "mean_delta_macro_f1_vs_best_baseline": _mean([item["delta_macro_f1_vs_best_baseline"] for item in comparisons.values()]),
        "classification_only": True,
    }


def _class_collapse_analysis(metrics: dict[str, Any]) -> dict[str, Any]:
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
                "model_name": item.get("model_name"),
                "split": item.get("split"),
                "max_prediction_ratio": max_pred_ratio,
                "down_recall": down_recall,
                "up_recall": up_recall,
                "class_collapse_warning": True,
            }
    return {"collapse_warnings": warnings, "collapse_warning_count": len(warnings)}


def _compare_to_v9_43(root: Path, metrics: dict[str, Any], baseline_comparison: dict[str, Any], no_clear_vs_shuffled_count: int, class_collapse_analysis: dict[str, Any]) -> dict[str, Any]:
    if not (root / V9_43_REPORT_PATH).is_file():
        return {"available": False, "clear_improvement_vs_v9_43": False, "reason": "missing V9.43 report"}
    v43 = _read_json(root / V9_43_REPORT_PATH)
    v43_metrics = v43.get("model_results_by_split", {})
    deltas: dict[str, Any] = {}
    for key, item in metrics.items():
        previous = v43_metrics.get(key)
        if not previous:
            continue
        deltas[key] = {
            "macro_f1_delta": item.get("macro_f1", 0.0) - previous.get("macro_f1", 0.0),
            "balanced_accuracy_delta": item.get("balanced_accuracy", 0.0) - previous.get("balanced_accuracy", 0.0),
            "down_recall_delta": item.get("per_class_recall", {}).get("DOWN", 0.0) - previous.get("per_class_recall", {}).get("DOWN", 0.0),
            "up_recall_delta": item.get("per_class_recall", {}).get("UP", 0.0) - previous.get("per_class_recall", {}).get("UP", 0.0),
        }
    eval_deltas = [value for key, value in deltas.items() if ".validation" in key or ".test" in key]
    mean_macro_delta = _mean([item["macro_f1_delta"] for item in eval_deltas])
    mean_balanced_delta = _mean([item["balanced_accuracy_delta"] for item in eval_deltas])
    previous_baseline = v43.get("baseline_comparison", {})
    previous_shuffle_count = int(v43.get("no_clear_edge_vs_shuffled_labels_count", 0))
    clear_improvement = (
        mean_macro_delta > 0.02
        and mean_balanced_delta > 0.02
        and baseline_comparison.get("clear_wins_count", 0) > previous_baseline.get("clear_wins_count", 0)
        and no_clear_vs_shuffled_count < previous_shuffle_count
        and class_collapse_analysis["collapse_warning_count"] == 0
    )
    return {
        "available": True,
        "baseline_clear_wins_count_v9_43": previous_baseline.get("clear_wins_count"),
        "baseline_clear_wins_count_v9_51": baseline_comparison.get("clear_wins_count"),
        "no_clear_edge_vs_shuffled_labels_count_v9_43": previous_shuffle_count,
        "no_clear_edge_vs_shuffled_labels_count_v9_51": no_clear_vs_shuffled_count,
        "mean_macro_f1_delta_vs_v9_43": mean_macro_delta,
        "mean_balanced_accuracy_delta_vs_v9_43": mean_balanced_delta,
        "per_metric_deltas": deltas,
        "clear_improvement_vs_v9_43": clear_improvement,
    }


def _read_ml_frame(path: Path) -> pd.DataFrame:
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


def _dataset_path(root: Path, timeframe: str) -> Path:
    return root / DATASET_BASE_PATH / f"timeframe={timeframe}" / f"window={WINDOW}" / "dataset.parquet"


def _input_block(root: Path, path: Path) -> dict[str, Any]:
    return {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "exists": path.is_file()}


def _decide(
    quality_status: str,
    leakage_guard_status: str,
    forbidden_metric_scan: dict[str, Any],
    baseline_comparison: dict[str, Any],
    no_clear_vs_shuffled_count: int,
    class_collapse_analysis: dict[str, Any],
    comparison_to_v9_43: dict[str, Any],
) -> str:
    if leakage_guard_status != "PASS":
        return "combined_features_5y_ml_blocked_by_leakage"
    if forbidden_metric_scan["status"] != "PASS":
        return "combined_features_5y_ml_blocked_by_forbidden_metrics"
    if quality_status != "PASS":
        return "combined_features_5y_ml_blocked_by_dataset_issue"
    if class_collapse_analysis["collapse_warning_count"] > 0:
        return "combined_features_5y_ml_completed_but_class_collapse"
    if no_clear_vs_shuffled_count > 0:
        return "combined_features_5y_ml_completed_but_close_to_shuffled_labels"
    if baseline_comparison["clear_wins_count"] < max(1, len(baseline_comparison["comparisons"]) // 2):
        return "combined_features_5y_ml_completed_but_weak_vs_baselines"
    if comparison_to_v9_43.get("clear_improvement_vs_v9_43") is True:
        return "combined_features_5y_ml_completed_with_improvement"
    return "combined_features_5y_ml_completed"


def _recommendation(decision: str) -> str:
    if decision == "combined_features_5y_ml_completed_with_improvement":
        return "V9.52 - Strict Walk-Forward Design / Candidate"
    if decision == "combined_features_5y_ml_completed_but_class_collapse":
        return "V9.52 - Label Redesign Binary/Quantile Diagnostic"
    if decision in {"combined_features_5y_ml_completed_but_weak_vs_baselines", "combined_features_5y_ml_completed_but_close_to_shuffled_labels"}:
        return "V9.52 - Funding / Open Interest Readiness or Label Redesign Diagnostic"
    return "V9.52 - Dataset Correction"


def _blocked_report(decision: str, started: datetime, errors: list[str]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "source_dataset_version": SOURCE_DATASET_VERSION,
        "created_at_utc": _utc_now(),
        "status": "FAIL",
        "decision": decision,
        "target_name": TARGET_NAME,
        "feature_columns": list(FEATURE_COLUMNS),
        "feature_columns_count": len(FEATURE_COLUMNS),
        "model_feature_columns": list(MODEL_FEATURE_COLUMNS),
        "model_feature_columns_count": len(MODEL_FEATURE_COLUMNS),
        "excluded_non_numeric_feature_columns": list(NON_NUMERIC_FEATURE_COLUMNS),
        "models_executed": [],
        "errors": errors,
        "warnings": [],
        "quality_status": "FAIL",
        "leakage_guard_status": "NOT_RUN",
        "forbidden_metric_scan": {"status": "NOT_RUN", "forbidden_terms_present": []},
        "no_persistent_model_check": no_persistent_model_check_v9_51(),
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
        "next_recommendation": "V9.52 - Dataset Correction",
        "runtime_seconds": (datetime.now(UTC) - started).total_seconds(),
    }


def _write_outputs(root: Path, report: dict[str, Any]) -> None:
    scores_payload = {
        "version": VERSION,
        "ml_run_id": report.get("ml_run_id"),
        "target_name": report.get("target_name"),
        "models_executed": report.get("models_executed", []),
        "model_results_by_split": report.get("model_results_by_split", {}),
        "baseline_comparison": report.get("baseline_comparison", {}),
        "shuffled_label_baseline_metrics": report.get("shuffled_label_baseline_metrics", {}),
        "original_vs_shuffled_delta": report.get("original_vs_shuffled_delta", {}),
        "class_collapse_analysis": report.get("class_collapse_analysis", {}),
        "comparison_to_v9_43": report.get("comparison_to_v9_43", {}),
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
    markdown = _markdown(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / SCORES_MD_PATH, _scores_markdown(scores_payload, report))
    _write_text(root / DOC_PATH, markdown)


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# V9.51 - OHLCV + AggTrades 5Y ML offline",
        "",
        "V9.51 execute un diagnostic ML offline research-only sur le dataset V9.49 valide par V9.50.",
        "",
        f"- Decision : `{report['decision']}`.",
        f"- Target : `{report.get('target_name')}`.",
        f"- Features utilisees : `{report.get('feature_columns_count')}`.",
        f"- Modeles executes : `{', '.join(report.get('models_executed', []))}`.",
        f"- Qualite : `{report.get('quality_status')}`.",
        f"- Leakage guard : `{report.get('leakage_guard_status')}`.",
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
        ]
    )
    return "\n".join(lines) + "\n"


def _scores_markdown(scores_payload: dict[str, Any], report: dict[str, Any]) -> str:
    lines = [
        "# Scores agreges V9.51",
        "",
        "Ce fichier contient uniquement des metriques agregees classification-only. Il ne contient pas de predictions exploitables comme signal.",
        "",
        f"- Target : `{scores_payload['target_name']}`.",
        f"- Modeles : `{', '.join(scores_payload['models_executed'])}`.",
        f"- Comparaisons baseline : `{len(report.get('baseline_comparison', {}).get('comparisons', {}))}`.",
        f"- Comparaisons shuffled : `{len(report.get('original_vs_shuffled_delta', {}))}`.",
        "- Signal actionnable : `false`.",
    ]
    return "\n".join(lines) + "\n"


def _mean(values: list[float]) -> float:
    return float(sum(values) / max(len(values), 1))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
