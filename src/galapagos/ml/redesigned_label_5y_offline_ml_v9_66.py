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

from galapagos.datasets.redesigned_label_5y_dataset_v9_65_schemas import DATASET_BASE_PATH, FEATURE_COLUMNS, SELECTED_PRIMARY_LABEL, TIMEFRAMES, WINDOW_LABEL
from galapagos.ml.ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62_quality import no_persistent_model_check_v9_62, scan_forbidden_metrics_v9_62
from galapagos.ml.redesigned_label_5y_offline_ml_v9_66_metrics import TARGET_CLASSES_V9_66, classification_metrics_v9_66


VERSION = "V9.66"
SOURCE_VERSION = "V9.65"
SOURCE_DATASET_VERSION = "V9.65"
TARGET_NAME = SELECTED_PRIMARY_LABEL
MODEL_NAMES = ["majority_class_baseline", "random_seeded_baseline", "logistic_regression", "decision_tree_depth_2", "decision_tree_depth_3"]
LEARNED_MODEL_NAMES = ["logistic_regression", "decision_tree_depth_2", "decision_tree_depth_3"]
RANDOM_SEED = 42
ML_WORKERS = int(os.environ.get("GALAPAGOS_ML_WORKERS", "12"))
NON_NUMERIC_FEATURE_COLUMNS = ("first_trade_ts", "last_trade_ts")
MODEL_FEATURE_COLUMNS = tuple(column for column in FEATURE_COLUMNS if column not in NON_NUMERIC_FEATURE_COLUMNS)

REPORT_JSON_PATH = Path("reports/ml/redesigned_label_5y_offline_ml_v9_66.json")
REPORT_MD_PATH = Path("reports/ml/redesigned_label_5y_offline_ml_v9_66.md")
SCORES_JSON_PATH = Path("reports/ml/redesigned_label_5y_offline_scores_v9_66.json")
SCORES_MD_PATH = Path("reports/ml/redesigned_label_5y_offline_scores_v9_66.md")
MANIFEST_PATH = Path("reports/manifests/redesigned_label_5y_offline_ml_v9_66_manifest.json")
V9_65_REPORT_PATH = Path("reports/datasets/redesigned_label_5y_dataset_v9_65.json")
COMPARISON_REPORTS = {
    "v9_43": Path("reports/ml/ohlcv_aggtrades_5y_offline_ml_v9_43.json"),
    "v9_51": Path("reports/ml/ohlcv_aggtrades_exact_5y_offline_ml_v9_51.json"),
    "v9_62": Path("reports/ml/ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62.json"),
}

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


def run_redesigned_label_5y_offline_ml_v9_66(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    started = datetime.now(UTC)
    source_validation = _read_json(root / V9_65_REPORT_PATH)
    if source_validation.get("decision") not in {"redesigned_label_dataset_created", "redesigned_label_dataset_created_with_warnings"}:
        report = blocked_report_v9_66("redesigned_label_ml_blocked_by_dataset_issue", started, ["V9.65 dataset is not successful"])
        write_outputs_v9_66(root, report)
        return report
    ml_run_id = f"v9_66_ml_{started.strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    model_results_by_timeframe: dict[str, Any] = {}
    model_results_by_split: dict[str, Any] = {}
    shuffled_label_baseline_metrics: dict[str, Any] = {}
    original_vs_shuffled_delta: dict[str, Any] = {}
    dataset_inputs: dict[str, Any] = {}
    warnings: list[str] = []
    errors: list[str] = []
    for timeframe in TIMEFRAMES:
        dataset_path = dataset_path_v9_66(root, timeframe)
        dataset_inputs[timeframe] = input_block_v9_66(root, dataset_path)
        try:
            frame = read_ml_frame_v9_66(dataset_path)
            metrics, shuffled, deltas = run_timeframe_models_v9_66(timeframe, frame)
            model_results_by_timeframe[timeframe] = {
                "rows_used": int(len(frame)),
                "train_rows": int(frame["split"].eq("train").sum()),
                "validation_rows": int(frame["split"].eq("validation").sum()),
                "test_rows": int(frame["split"].eq("test").sum()),
                "feature_columns_count": len(MODEL_FEATURE_COLUMNS),
                "models": MODEL_NAMES,
                "metrics": metrics,
            }
            model_results_by_split.update(metrics)
            shuffled_label_baseline_metrics.update(shuffled)
            original_vs_shuffled_delta.update(deltas)
            print(f"[V9.66] timeframe_done={timeframe} rows={len(frame)}", flush=True)
        except Exception as exc:  # pragma: no cover
            errors.append(f"{timeframe}: {type(exc).__name__}: {exc}")
    baseline_comparison = baseline_comparison_v9_66(model_results_by_split)
    no_clear_vs_shuffled_count = int(sum(1 for item in original_vs_shuffled_delta.values() if item["no_clear_edge_vs_shuffled_labels"]))
    class_collapse = class_collapse_analysis_v9_66(model_results_by_split)
    comparison_to_prior = comparison_to_prior_runs_v9_66(root, baseline_comparison, no_clear_vs_shuffled_count, class_collapse)
    if baseline_comparison["clear_wins_count"] == 0:
        warnings.append("learned models do not clearly beat majority/random baselines")
    if no_clear_vs_shuffled_count:
        warnings.append("learned models remain close to shuffled-label falsification on at least one evaluation split")
    if class_collapse["collapse_warning_count"]:
        warnings.append("class collapse warning remains present")
    forbidden_metric_scan = scan_forbidden_metrics_v9_62(
        {
            "model_results_by_split": model_results_by_split,
            "baseline_comparison": baseline_comparison,
            "shuffled_label_baseline_metrics": shuffled_label_baseline_metrics,
            "comparison_to_prior_runs": comparison_to_prior,
        }
    )
    no_model_check = no_persistent_model_check_v9_62(root)
    quality_status = "PASS" if not errors and forbidden_metric_scan["status"] == "PASS" and no_model_check["status"] == "PASS" else "FAIL"
    leakage_guard_status = "PASS" if not errors else "FAIL"
    decision = decide_v9_66(quality_status, leakage_guard_status, baseline_comparison, no_clear_vs_shuffled_count, class_collapse)
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
        "target_classes": TARGET_CLASSES_V9_66,
        "window": WINDOW_LABEL,
        "dataset_inputs": dataset_inputs,
        "feature_set": {
            "description": "OHLCV + aggTrades exact V9.47 without funding",
            "feature_columns": list(MODEL_FEATURE_COLUMNS),
            "feature_columns_count": len(MODEL_FEATURE_COLUMNS),
            "funding_features_included": False,
        },
        "excluded_non_numeric_feature_columns": list(NON_NUMERIC_FEATURE_COLUMNS),
        "models_executed": MODEL_NAMES,
        "ml_workers_requested": ML_WORKERS,
        "train_only_fit": True,
        "validation_test_not_used_for_fit": True,
        "same_window_same_splits_same_target": True,
        "random_seed": RANDOM_SEED,
        "model_results_by_timeframe": model_results_by_timeframe,
        "model_results_by_split": model_results_by_split,
        "baseline_comparison": baseline_comparison,
        "shuffled_label_baseline_metrics": shuffled_label_baseline_metrics,
        "original_vs_shuffled_delta": original_vs_shuffled_delta,
        "no_clear_edge_vs_shuffled_labels_count": no_clear_vs_shuffled_count,
        "class_collapse_analysis": class_collapse,
        "comparison_to_v9_43_v9_51_v9_62": comparison_to_prior,
        "warnings": warnings,
        "errors": errors,
        "limitations": [
            "V9.66 est un diagnostic ML offline classification-only.",
            "Aucun signal, strategie, backtest, walk-forward, ordre ou modele persistant n'est produit.",
            "Les comparaisons V9.43/V9.51/V9.62 sont descriptives car la cible differe.",
        ],
        "quality_status": quality_status,
        "leakage_guard_status": leakage_guard_status,
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
        "next_recommendation": recommendation_v9_66(decision),
        "runtime_seconds": (datetime.now(UTC) - started).total_seconds(),
    }
    write_outputs_v9_66(root, report)
    return report


def dataset_path_v9_66(root: Path, timeframe: str) -> Path:
    return root / DATASET_BASE_PATH / f"timeframe={timeframe}" / f"window={WINDOW_LABEL}" / "dataset.parquet"


def read_ml_frame_v9_66(path: Path) -> pd.DataFrame:
    columns = ["timeframe", "decision_ts", "split", "row_valid_for_dataset", TARGET_NAME, *MODEL_FEATURE_COLUMNS]
    frame = pd.read_parquet(path, columns=columns, engine="pyarrow")
    mask = frame["row_valid_for_dataset"].eq(True) & frame[TARGET_NAME].notna() & frame["split"].isin(["train", "validation", "test"])
    result = frame.loc[mask].reset_index(drop=True)
    result[TARGET_NAME] = result[TARGET_NAME].astype("int64").map({-1: "DOWN", 1: "UP"}).astype(str)
    return result


def run_timeframe_models_v9_66(timeframe: str, frame: pd.DataFrame) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    metrics: dict[str, Any] = {}
    shuffled_metrics: dict[str, Any] = {}
    shuffle_deltas: dict[str, Any] = {}
    train = frame[frame["split"] == "train"]
    predictions_by_model: dict[str, pd.Series] = {}
    for model_name in MODEL_NAMES:
        result = fit_predict_model_v9_66(model_name, train[list(MODEL_FEATURE_COLUMNS)], train[TARGET_NAME], frame[list(MODEL_FEATURE_COLUMNS)])
        predictions_by_model[model_name] = result.predicted_class.reset_index(drop=True)
        for split, split_frame in frame.groupby("split", sort=True, observed=True):
            split_index = split_frame.index
            key = f"{timeframe}.{model_name}.{split}"
            metrics[key] = classification_metrics_v9_66(timeframe=timeframe, model_name=model_name, split=str(split), y_true=split_frame[TARGET_NAME], y_pred=predictions_by_model[model_name].iloc[split_index])
    eval_frame = frame[frame["split"].isin(["validation", "test"])]
    shuffled_target = train[TARGET_NAME].sample(frac=1.0, random_state=RANDOM_SEED).reset_index(drop=True)
    for model_name in LEARNED_MODEL_NAMES:
        shuffled = fit_predict_model_v9_66(model_name, train[list(MODEL_FEATURE_COLUMNS)], shuffled_target, eval_frame[list(MODEL_FEATURE_COLUMNS)])
        shuffled_predictions = shuffled.predicted_class.reset_index(drop=True)
        for split, split_frame in eval_frame.groupby("split", sort=True, observed=True):
            eval_positions = eval_frame.index.get_indexer(split_frame.index)
            shuffled_key = f"{timeframe}.{model_name}.shuffled_train_labels.{split}"
            original_key = f"{timeframe}.{model_name}.{split}"
            shuffled_metrics[shuffled_key] = classification_metrics_v9_66(timeframe=timeframe, model_name=f"{model_name}_shuffled_train_labels", split=str(split), y_true=split_frame[TARGET_NAME], y_pred=shuffled_predictions.iloc[eval_positions])
            shuffle_deltas[original_key] = {
                "timeframe": timeframe,
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
    return metrics, shuffled_metrics, shuffle_deltas


def fit_predict_model_v9_66(model_name: str, train_features: pd.DataFrame, train_target: pd.Series, predict_features: pd.DataFrame) -> Any:
    if model_name == "majority_class_baseline":
        majority = str(train_target.value_counts().sort_values(ascending=False).index[0])
        return type("OfflineResult", (), {"predicted_class": pd.Series(majority, index=predict_features.index, name="research_predicted_class")})()
    if model_name == "random_seeded_baseline":
        distribution = train_target.value_counts(normalize=True).reindex(TARGET_CLASSES_V9_66, fill_value=0.0)
        rng = np.random.default_rng(RANDOM_SEED)
        draws = rng.choice(TARGET_CLASSES_V9_66, size=len(predict_features), p=distribution.to_numpy(dtype=float))
        return type("OfflineResult", (), {"predicted_class": pd.Series(draws, index=predict_features.index, name="research_predicted_class")})()
    if model_name == "logistic_regression":
        estimator = SGDClassifier(loss="log_loss", max_iter=8, tol=1e-3, shuffle=False, random_state=RANDOM_SEED, n_jobs=ML_WORKERS)
    elif model_name == "decision_tree_depth_2":
        estimator = DecisionTreeClassifier(max_depth=2, random_state=RANDOM_SEED)
    elif model_name == "decision_tree_depth_3":
        estimator = DecisionTreeClassifier(max_depth=3, random_state=RANDOM_SEED)
    else:
        raise ValueError(f"unsupported V9.66 model: {model_name}")
    estimator.fit(model_matrix_v9_66(train_features), train_target.to_numpy(dtype=str))
    predicted = pd.Series(estimator.predict(model_matrix_v9_66(predict_features)), index=predict_features.index, name="research_predicted_class")
    return type("OfflineResult", (), {"predicted_class": predicted.astype(str)})()


def model_matrix_v9_66(features: pd.DataFrame) -> np.ndarray:
    return np.nan_to_num(features.to_numpy(dtype=np.float32, copy=True), nan=0.0, posinf=0.0, neginf=0.0, copy=False)


def baseline_comparison_v9_66(metrics: dict[str, Any]) -> dict[str, Any]:
    comparisons: dict[str, Any] = {}
    for key, item in metrics.items():
        if item["model_name"] not in LEARNED_MODEL_NAMES or item["split"] not in {"validation", "test"}:
            continue
        baselines = [metric for metric in metrics.values() if metric["timeframe"] == item["timeframe"] and metric["split"] == item["split"] and metric["model_name"] in {"majority_class_baseline", "random_seeded_baseline"}]
        best_macro = max((metric["macro_f1"] for metric in baselines), default=0.0)
        comparisons[key] = {
            "timeframe": item["timeframe"],
            "model_name": item["model_name"],
            "split": item["split"],
            "accuracy": item["accuracy"],
            "macro_f1": item["macro_f1"],
            "balanced_accuracy": item["balanced_accuracy"],
            "delta_macro_f1_vs_best_baseline": item["macro_f1"] - best_macro,
            "clear_win_vs_baseline": (item["macro_f1"] - best_macro) > 0.02,
        }
    return {
        "comparisons": comparisons,
        "clear_wins_count": int(sum(1 for item in comparisons.values() if item["clear_win_vs_baseline"])),
        "weak_vs_baselines_count": int(sum(1 for item in comparisons.values() if not item["clear_win_vs_baseline"])),
        "mean_delta_macro_f1_vs_best_baseline": mean_v9_66([item["delta_macro_f1_vs_best_baseline"] for item in comparisons.values()]),
        "classification_only": True,
    }


def class_collapse_analysis_v9_66(metrics: dict[str, Any]) -> dict[str, Any]:
    warnings: dict[str, Any] = {}
    for key, item in metrics.items():
        if item["model_name"] not in LEARNED_MODEL_NAMES or item["split"] not in {"validation", "test"}:
            continue
        rows = max(int(item.get("rows", 0)), 1)
        prediction_distribution = item.get("prediction_distribution", {})
        max_pred_ratio = max((value / rows for value in prediction_distribution.values()), default=0.0)
        recall = item.get("per_class_recall", {})
        down_recall = float(recall.get("DOWN", 0.0))
        up_recall = float(recall.get("UP", 0.0))
        if max_pred_ratio > 0.90 or down_recall < 0.05 or up_recall < 0.05:
            warnings[key] = {"timeframe": item["timeframe"], "model_name": item["model_name"], "split": item["split"], "max_prediction_ratio": max_pred_ratio, "down_recall": down_recall, "up_recall": up_recall, "class_collapse_warning": True}
    return {"collapse_warnings": warnings, "collapse_warning_count": len(warnings)}


def comparison_to_prior_runs_v9_66(root: Path, baseline: dict[str, Any], no_clear_vs_shuffled_count: int, class_collapse: dict[str, Any]) -> dict[str, Any]:
    current = {
        "target": TARGET_NAME,
        "window": WINDOW_LABEL,
        "baseline_clear_wins": baseline["clear_wins_count"],
        "no_clear_edge_vs_shuffled_labels_count": no_clear_vs_shuffled_count,
        "class_collapse_warning_count": class_collapse["collapse_warning_count"],
    }
    prior: dict[str, Any] = {}
    for name, path in COMPARISON_REPORTS.items():
        payload = _read_json(root / path)
        prior[name] = {
            "available": bool(payload),
            "decision": payload.get("decision"),
            "target": payload.get("target_name") or payload.get("target"),
            "baseline_clear_wins": payload.get("baseline_comparison", {}).get("clear_wins_count"),
            "no_clear_edge_vs_shuffled_labels_count": payload.get("no_clear_edge_vs_shuffled_labels_count"),
            "class_collapse_warning_count": payload.get("class_collapse_analysis", {}).get("collapse_warning_count"),
            "comparison_note": "descriptive_only_target_or_window_may_differ",
        }
    return {"current_v9_66": current, "prior_runs": prior}


def decide_v9_66(quality_status: str, leakage_guard_status: str, baseline: dict[str, Any], no_clear_vs_shuffled_count: int, class_collapse: dict[str, Any]) -> str:
    if leakage_guard_status != "PASS":
        return "redesigned_label_ml_blocked_by_leakage"
    if quality_status != "PASS":
        return "redesigned_label_ml_blocked_by_dataset_issue"
    if class_collapse["collapse_warning_count"] > 0:
        return "redesigned_label_ml_completed_but_class_collapse"
    if no_clear_vs_shuffled_count > 0:
        return "redesigned_label_ml_completed_but_close_to_shuffled"
    if baseline["clear_wins_count"] == 0:
        return "redesigned_label_ml_completed_but_weak_vs_baselines"
    return "redesigned_label_ml_completed_with_improvement"


def recommendation_v9_66(decision: str) -> str:
    if decision == "redesigned_label_ml_completed_with_improvement":
        return "V9.67 - Strict Walk-Forward Design / Candidate"
    if decision in {"redesigned_label_ml_completed_but_weak_vs_baselines", "redesigned_label_ml_completed_but_close_to_shuffled", "redesigned_label_ml_completed_but_class_collapse"}:
        return "V9.67 - Manual Research Decision Gate"
    return "V9.67 - Dataset or leakage correction"


def blocked_report_v9_66(decision: str, started: datetime, errors: list[str]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "FAIL",
        "decision": decision,
        "target_name": TARGET_NAME,
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
        "next_recommendation": "V9.67 - Dataset correction",
        "runtime_seconds": (datetime.now(UTC) - started).total_seconds(),
    }


def write_outputs_v9_66(root: Path, report: dict[str, Any]) -> None:
    scores = {
        "version": VERSION,
        "ml_run_id": report.get("ml_run_id"),
        "target_name": report.get("target_name"),
        "models_executed": report.get("models_executed", []),
        "model_results_by_split": report.get("model_results_by_split", {}),
        "baseline_comparison": report.get("baseline_comparison", {}),
        "shuffled_label_baseline_metrics": report.get("shuffled_label_baseline_metrics", {}),
        "original_vs_shuffled_delta": report.get("original_vs_shuffled_delta", {}),
        "class_collapse_analysis": report.get("class_collapse_analysis", {}),
        "classification_only": True,
        "contains_predictions": False,
        "contains_actionable_signal": False,
    }
    manifest = {"version": VERSION, "source_version": SOURCE_VERSION, "created_at_utc": _utc_now(), "decision": report["decision"], "report_path": REPORT_JSON_PATH.as_posix(), "scores_path": SCORES_JSON_PATH.as_posix(), "target_name": report.get("target_name"), "models_executed": report.get("models_executed", []), "quality_status": report.get("quality_status"), "leakage_guard_status": report.get("leakage_guard_status"), "findings": report.get("findings"), "safety_flags": report.get("safety_flags")}
    _write_json(root / REPORT_JSON_PATH, report)
    _write_json(root / SCORES_JSON_PATH, scores)
    _write_json(root / MANIFEST_PATH, manifest)
    markdown = markdown_v9_66(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / SCORES_MD_PATH, scores_markdown_v9_66(scores, report))


def markdown_v9_66(report: dict[str, Any]) -> str:
    return f"# V9.66 - ML offline label redesign\n\n- Decision : `{report['decision']}`.\n- Target : `{report.get('target_name')}`.\n- Modeles : `{', '.join(report.get('models_executed', []))}`.\n- Clear wins baseline : `{report.get('baseline_comparison', {}).get('clear_wins_count', 0)}`.\n- No-clear vs shuffled : `{report.get('no_clear_edge_vs_shuffled_labels_count', 0)}`.\n- Collapse warnings : `{report.get('class_collapse_analysis', {}).get('collapse_warning_count', 0)}`.\n\nAucun signal, strategie, backtest, walk-forward, ordre ou modele persistant.\n"


def scores_markdown_v9_66(scores: dict[str, Any], report: dict[str, Any]) -> str:
    return f"# Scores V9.66\n\n- Classification only : `{scores['classification_only']}`.\n- Predictions persistantes : `{scores['contains_predictions']}`.\n- Signal actionnable : `{scores['contains_actionable_signal']}`.\n- Decision : `{report['decision']}`.\n"


def input_block_v9_66(root: Path, path: Path) -> dict[str, Any]:
    return {"path": path.relative_to(root).as_posix() if path.is_absolute() and root in path.parents else path.as_posix(), "available": path.is_file(), "bytes": path.stat().st_size if path.is_file() else 0}


def mean_v9_66(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
