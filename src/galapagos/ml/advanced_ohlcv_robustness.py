from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score

from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.advanced_ohlcv_window_validation import validate_advanced_ohlcv_offline_supervised_dataset_v6_1
from galapagos.datasets.schemas import MANIFEST_PATH_V6_1
from galapagos.ml.advanced_ohlcv_window import input_dataset_path, score_output_path
from galapagos.ml.advanced_ohlcv_window_validation import validate_advanced_ohlcv_offline_ml_research_v6_2
from galapagos.ml.offline_baselines import fit_predict_model
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V6_2,
    MANIFEST_PATH_V5_4,
    MANIFEST_PATH_V6_2,
    MODEL_NAMES_V6_2,
    REPORT_JSON_PATH_V6_2,
    REPORT_JSON_PATH_V5_4,
    SCORES_JSON_PATH_V5_4,
    SCORES_JSON_PATH_V6_2,
    TARGET_CLASSES_V6_2,
    TARGET_NAME_V6_2,
    TIMEFRAMES_V6_2,
)


VERSION_V6_3 = "V6.3"
ROBUSTNESS_RUN_ID_PREFIX_V6_3 = "v6_3"
MANIFEST_PATH_V6_3 = Path("reports/manifests/advanced_ohlcv_ml_robustness_v6_3_manifest.json")
REPORT_JSON_PATH_V6_3 = Path("reports/ml/advanced_ohlcv_ml_robustness_v6_3.json")
REPORT_MD_PATH_V6_3 = Path("reports/ml/advanced_ohlcv_ml_robustness_v6_3.md")
DOC_PATH_V6_3 = Path("docs/advanced_ohlcv_ml_robustness_v6_3.md")
ACCURACY_GAP_WARNING_THRESHOLD_V6_3 = 0.10
MACRO_F1_GAP_WARNING_THRESHOLD_V6_3 = 0.10
LABEL_SHUFFLE_RANDOM_SEED_V6_3 = 123
ROBUSTNESS_MODELS_V6_3 = ["logistic_regression", "decision_tree_depth_2"]
ROBUSTNESS_SPLITS_V6_3 = ["train", "validation", "test"]
EVALUATION_SPLITS_V6_3 = ["validation", "test"]
WALK_FORWARD_WEAK_ACCURACY_THRESHOLD_V6_3 = 0.34
WALK_FORWARD_WEAK_MACRO_F1_THRESHOLD_V6_3 = 0.20
FORBIDDEN_ROBUSTNESS_FEATURE_PREFIXES_V6_3 = [
    "future_",
    "label_",
    "direction_",
    "up_down_flat_",
]
FORBIDDEN_ROBUSTNESS_FEATURE_EXACT_V6_3 = [
    "target",
    "split",
    "walk_forward_group",
    "signal",
    "trading_signal",
    "strategy_signal",
    "order",
    "strategy",
    "trade_decision",
    "position_size",
    "pnl",
    "profit",
    "backtest",
    "execution",
]
FORBIDDEN_ROBUSTNESS_METRIC_TERMS_V6_3 = [
    "sharpe",
    "drawdown",
    "pnl",
    "equity_curve",
    "profit_factor",
    "trading_win_rate",
]
EXPECTED_LIMITATIONS_V6_3 = [
    "V6.3 audite uniquement la robustesse descriptive des baselines ML offline V6.2 avec advanced OHLCV features.",
    "V6.3 compare descriptivement V6.2 a V5.4 si disponible, sans produire aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.",
]
SAFETY_FLAGS_V6_3 = {
    "public_read_only": True,
    "authentication_used": False,
    "api_key_used": False,
    "private_endpoint_used": False,
    "orders_enabled": False,
    "paper_live_enabled": False,
    "trading_enabled": False,
    "ml_enabled": True,
    "labels_enabled": True,
    "dataset_enabled": True,
    "backtest_enabled": False,
    "strategy_enabled": False,
    "execution_enabled": False,
}


def run_advanced_ohlcv_ml_robustness_v6_3(
    root: Path = Path("."),
    *,
    validate_inputs: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_inputs:
        _validate_inputs(root)

    dataset_manifest = _read_json(root / MANIFEST_PATH_V6_1)
    ml_manifest = _read_json(root / MANIFEST_PATH_V6_2)
    ml_report = _read_json(root / REPORT_JSON_PATH_V6_2)
    scores_report = _read_json(root / SCORES_JSON_PATH_V6_2)
    window = ml_manifest["input_dataset_manifest"]
    metrics = ml_manifest["metrics"]
    walk_forward_metrics = ml_manifest["walk_forward_metrics"]
    simple_reference = build_simple_ohlcv_reference_v6_3(root)

    analyses: dict[str, Any] = {
        "baseline_delta": compute_advanced_ohlcv_baseline_delta_v6_3(metrics),
        "split_stability": compute_advanced_ohlcv_split_stability_v6_3(metrics),
        "timeframe_stability": compute_advanced_ohlcv_timeframe_stability_v6_3(metrics),
        "walk_forward_stability": compute_advanced_ohlcv_walk_forward_stability_v6_3(walk_forward_metrics),
        "advanced_vs_simple_comparison": compute_advanced_vs_simple_comparison_v6_3(root, metrics, walk_forward_metrics),
        "label_shuffle_falsification": compute_advanced_ohlcv_label_shuffle_falsification_v6_3(root, ml_manifest),
        "feature_leakage_scan": scan_advanced_ohlcv_feature_leakage_v6_3(ml_manifest["feature_columns"]),
    }
    analyses["metric_forbidden_scan"] = scan_advanced_ohlcv_metric_forbidden_terms_v6_3(
        {
            "ml_manifest_metrics": ml_manifest.get("metrics", {}),
            "ml_manifest_walk_forward_metrics": ml_manifest.get("walk_forward_metrics", {}),
            "ml_report_metrics": ml_report.get("metrics", {}),
            "ml_report_walk_forward_metrics": ml_report.get("walk_forward_metrics", {}),
            "scores_report": scores_report,
            "v6_3_analyses": analyses,
        }
    )

    warnings = _collect_warnings(analyses)
    status = "PASS"
    if analyses["feature_leakage_scan"]["forbidden_feature_columns_present"]:
        status = "FAIL"
    if analyses["metric_forbidden_scan"]["forbidden_terms_present"]:
        status = "FAIL"

    manifest = {
        "version": VERSION_V6_3,
        "status": status,
        "created_at_utc": utc_now_iso(),
        "robustness_run_id": _robustness_run_id(),
        "input_dataset_manifest": {
            "path": MANIFEST_PATH_V6_1.as_posix(),
            "sha256": sha256_file(root / MANIFEST_PATH_V6_1),
            "window_start": window["window_start"],
            "window_end": window["window_end"],
            "total_days": int(window["total_days"]),
            "advanced_feature_columns_count": int(dataset_manifest["advanced_feature_columns_count"]),
        },
        "input_ml_manifest": {
            "path": MANIFEST_PATH_V6_2.as_posix(),
            "sha256": sha256_file(root / MANIFEST_PATH_V6_2),
            "window_start": window["window_start"],
            "window_end": window["window_end"],
            "total_days": int(window["total_days"]),
            "advanced_feature_columns_count": int(ml_manifest["advanced_feature_columns_count"]),
        },
        "input_score_files": _input_score_files(root, ml_manifest),
        "simple_ohlcv_reference": simple_reference,
        "analyses": analyses,
        "thresholds": {
            "accuracy_gap_warning_threshold": ACCURACY_GAP_WARNING_THRESHOLD_V6_3,
            "macro_f1_gap_warning_threshold": MACRO_F1_GAP_WARNING_THRESHOLD_V6_3,
            "random_seed": LABEL_SHUFFLE_RANDOM_SEED_V6_3,
        },
        "findings": {
            "robust_edge_claimed": False,
            "strategy_validated": False,
            "backtest_performed": False,
            "actionable_signal_produced": False,
            "advanced_features_validated_for_trading": False,
            "warnings": warnings,
        },
        "safety": SAFETY_FLAGS_V6_3,
        "limitations": EXPECTED_LIMITATIONS_V6_3,
    }
    _write_json(root / MANIFEST_PATH_V6_3, manifest)
    _write_json(root / REPORT_JSON_PATH_V6_3, manifest)
    markdown = build_advanced_ohlcv_ml_robustness_markdown_v6_3(manifest)
    _write_text(root / REPORT_MD_PATH_V6_3, markdown)
    _write_text(root / DOC_PATH_V6_3, markdown)
    _update_project_state(root, manifest)
    return manifest


def compute_advanced_ohlcv_baseline_delta_v6_3(metrics: dict[str, Any]) -> dict[str, Any]:
    baseline_delta: dict[str, Any] = {}
    for key, metric in sorted(metrics.items()):
        timeframe = metric["timeframe"]
        model_name = metric["model_name"]
        split = metric["split"]
        majority = metrics.get(f"{timeframe}.majority_class_baseline.{split}")
        random = metrics.get(f"{timeframe}.random_seeded_baseline.{split}")
        if majority is None or random is None:
            continue
        baseline_delta[key] = {
            "timeframe": timeframe,
            "model_name": model_name,
            "split": split,
            "accuracy": float(metric["accuracy"]),
            "balanced_accuracy": float(metric["balanced_accuracy"]),
            "macro_f1": float(metric["macro_f1"]),
            "majority_class_baseline_accuracy": float(majority["accuracy"]),
            "majority_class_baseline_balanced_accuracy": float(majority["balanced_accuracy"]),
            "majority_class_baseline_macro_f1": float(majority["macro_f1"]),
            "random_seeded_baseline_accuracy": float(random["accuracy"]),
            "random_seeded_baseline_balanced_accuracy": float(random["balanced_accuracy"]),
            "random_seeded_baseline_macro_f1": float(random["macro_f1"]),
            "delta_vs_majority_accuracy": _round_metric(metric["accuracy"] - majority["accuracy"]),
            "delta_vs_majority_balanced_accuracy": _round_metric(metric["balanced_accuracy"] - majority["balanced_accuracy"]),
            "delta_vs_majority_macro_f1": _round_metric(metric["macro_f1"] - majority["macro_f1"]),
            "delta_vs_random_accuracy": _round_metric(metric["accuracy"] - random["accuracy"]),
            "delta_vs_random_balanced_accuracy": _round_metric(metric["balanced_accuracy"] - random["balanced_accuracy"]),
            "delta_vs_random_macro_f1": _round_metric(metric["macro_f1"] - random["macro_f1"]),
        }
    return baseline_delta


def compute_advanced_ohlcv_split_stability_v6_3(metrics: dict[str, Any]) -> dict[str, Any]:
    stability: dict[str, Any] = {}
    models = sorted({metric["model_name"] for metric in metrics.values()})
    timeframes = sorted({metric["timeframe"] for metric in metrics.values()}, key=TIMEFRAMES_V6_2.index)
    for timeframe in timeframes:
        for model_name in models:
            split_metrics = {split: metrics.get(f"{timeframe}.{model_name}.{split}") for split in ROBUSTNESS_SPLITS_V6_3}
            if not all(split_metrics.values()):
                continue
            train = split_metrics["train"]
            validation = split_metrics["validation"]
            test = split_metrics["test"]
            train_validation_accuracy_gap = _round_metric(train["accuracy"] - validation["accuracy"])
            validation_test_accuracy_gap = _round_metric(validation["accuracy"] - test["accuracy"])
            train_validation_macro_f1_gap = _round_metric(train["macro_f1"] - validation["macro_f1"])
            validation_test_macro_f1_gap = _round_metric(validation["macro_f1"] - test["macro_f1"])
            overfit_warning = (
                train_validation_accuracy_gap > ACCURACY_GAP_WARNING_THRESHOLD_V6_3
                or train_validation_macro_f1_gap > MACRO_F1_GAP_WARNING_THRESHOLD_V6_3
            )
            stability[f"{timeframe}.{model_name}"] = {
                "timeframe": timeframe,
                "model_name": model_name,
                "train_accuracy": float(train["accuracy"]),
                "validation_accuracy": float(validation["accuracy"]),
                "test_accuracy": float(test["accuracy"]),
                "train_macro_f1": float(train["macro_f1"]),
                "validation_macro_f1": float(validation["macro_f1"]),
                "test_macro_f1": float(test["macro_f1"]),
                "train_validation_accuracy_gap": train_validation_accuracy_gap,
                "validation_test_accuracy_gap": validation_test_accuracy_gap,
                "train_validation_macro_f1_gap": train_validation_macro_f1_gap,
                "validation_test_macro_f1_gap": validation_test_macro_f1_gap,
                "overfit_warning": bool(overfit_warning),
            }
    return stability


def compute_advanced_ohlcv_timeframe_stability_v6_3(metrics: dict[str, Any]) -> dict[str, Any]:
    stability: dict[str, Any] = {}
    models = sorted({metric["model_name"] for metric in metrics.values()})
    for model_name in models:
        test_metrics = {
            timeframe: metrics[f"{timeframe}.{model_name}.test"]
            for timeframe in TIMEFRAMES_V6_2
            if f"{timeframe}.{model_name}.test" in metrics
        }
        if not test_metrics:
            continue
        accuracy_by_timeframe = {timeframe: float(metric["accuracy"]) for timeframe, metric in test_metrics.items()}
        macro_f1_by_timeframe = {timeframe: float(metric["macro_f1"]) for timeframe, metric in test_metrics.items()}
        sorted_accuracy = sorted(accuracy_by_timeframe.items(), key=lambda item: item[1], reverse=True)
        best_timeframe = sorted_accuracy[0][0]
        second_accuracy = sorted_accuracy[1][1] if len(sorted_accuracy) > 1 else sorted_accuracy[0][1]
        stability[model_name] = {
            "model_name": model_name,
            "split": "test",
            "accuracy_by_timeframe": accuracy_by_timeframe,
            "macro_f1_by_timeframe": macro_f1_by_timeframe,
            "best_accuracy_timeframe": best_timeframe,
            "accuracy_range": _round_metric(max(accuracy_by_timeframe.values()) - min(accuracy_by_timeframe.values())),
            "macro_f1_range": _round_metric(max(macro_f1_by_timeframe.values()) - min(macro_f1_by_timeframe.values())),
            "single_timeframe_concentration_warning": bool(sorted_accuracy[0][1] - second_accuracy > ACCURACY_GAP_WARNING_THRESHOLD_V6_3),
        }
    return stability


def compute_advanced_ohlcv_walk_forward_stability_v6_3(walk_forward_metrics: dict[str, Any]) -> dict[str, Any]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for metric in walk_forward_metrics.values():
        grouped.setdefault((metric["timeframe"], metric["model_name"]), []).append(metric)

    stability: dict[str, Any] = {}
    for (timeframe, model_name), records in sorted(grouped.items()):
        ordered = sorted(records, key=lambda item: item["walk_forward_group"])
        accuracy_by_group = {item["walk_forward_group"]: float(item["accuracy"]) for item in ordered}
        macro_f1_by_group = {item["walk_forward_group"]: float(item["macro_f1"]) for item in ordered}
        mean_accuracy = float(np.mean(list(accuracy_by_group.values())))
        mean_macro_f1 = float(np.mean(list(macro_f1_by_group.values())))
        weak_groups = [
            group
            for group in accuracy_by_group
            if accuracy_by_group[group] < WALK_FORWARD_WEAK_ACCURACY_THRESHOLD_V6_3
            or macro_f1_by_group[group] < WALK_FORWARD_WEAK_MACRO_F1_THRESHOLD_V6_3
        ]
        unstable_groups = [
            group
            for group in accuracy_by_group
            if abs(accuracy_by_group[group] - mean_accuracy) > ACCURACY_GAP_WARNING_THRESHOLD_V6_3
            or abs(macro_f1_by_group[group] - mean_macro_f1) > MACRO_F1_GAP_WARNING_THRESHOLD_V6_3
        ]
        stability[f"{timeframe}.{model_name}"] = {
            "timeframe": timeframe,
            "model_name": model_name,
            "walk_forward_groups": list(accuracy_by_group),
            "rows_by_group": {item["walk_forward_group"]: int(item["rows"]) for item in ordered},
            "accuracy_by_group": accuracy_by_group,
            "macro_f1_by_group": macro_f1_by_group,
            "min_accuracy_by_group": _round_metric(min(accuracy_by_group.values())),
            "max_accuracy_by_group": _round_metric(max(accuracy_by_group.values())),
            "mean_accuracy_by_group": _round_metric(mean_accuracy),
            "accuracy_range_by_group": _round_metric(max(accuracy_by_group.values()) - min(accuracy_by_group.values())),
            "min_macro_f1_by_group": _round_metric(min(macro_f1_by_group.values())),
            "max_macro_f1_by_group": _round_metric(max(macro_f1_by_group.values())),
            "mean_macro_f1_by_group": _round_metric(mean_macro_f1),
            "macro_f1_range_by_group": _round_metric(max(macro_f1_by_group.values()) - min(macro_f1_by_group.values())),
            "weak_groups": weak_groups,
            "unstable_groups": unstable_groups,
            "concentrated_on_few_groups_warning": bool(len(unstable_groups) > max(1, len(accuracy_by_group) // 3)),
        }
    return stability


def build_simple_ohlcv_reference_v6_3(root: Path) -> dict[str, Any]:
    warnings: list[str] = []
    manifest_path = root / MANIFEST_PATH_V5_4
    report_path = root / REPORT_JSON_PATH_V5_4
    scores_report_path = root / SCORES_JSON_PATH_V5_4
    if not manifest_path.exists():
        return {
            "available": False,
            "manifest_path": MANIFEST_PATH_V5_4.as_posix(),
            "manifest_sha256": None,
            "report_path": REPORT_JSON_PATH_V5_4.as_posix(),
            "scores_report_path": SCORES_JSON_PATH_V5_4.as_posix(),
            "warnings": ["V5.4 simple OHLCV reference manifest is unavailable; comparison is skipped."],
        }
    if not report_path.exists():
        warnings.append("V5.4 simple OHLCV quality report is unavailable.")
    if not scores_report_path.exists():
        warnings.append("V5.4 simple OHLCV scores report is unavailable.")
    return {
        "available": True,
        "manifest_path": MANIFEST_PATH_V5_4.as_posix(),
        "manifest_sha256": sha256_file(manifest_path),
        "report_path": REPORT_JSON_PATH_V5_4.as_posix(),
        "scores_report_path": SCORES_JSON_PATH_V5_4.as_posix(),
        "warnings": warnings,
    }


def compute_advanced_vs_simple_comparison_v6_3(
    root: Path,
    advanced_metrics: dict[str, Any],
    advanced_walk_forward_metrics: dict[str, Any],
) -> dict[str, Any]:
    simple_manifest_path = root / MANIFEST_PATH_V5_4
    if not simple_manifest_path.exists():
        return {
            "available": False,
            "compared_metrics": ["accuracy", "balanced_accuracy", "macro_f1"],
            "split_metric_comparisons": {},
            "walk_forward_metric_comparisons": {},
            "advanced_better_count": 0,
            "simple_better_count": 0,
            "mixed_or_inconclusive_count": 0,
            "advanced_improvement_consistency": 0.0,
            "descriptive_only": True,
            "non_actionable": True,
            "warnings": ["V5.4 simple OHLCV manifest is unavailable; advanced vs simple comparison skipped."],
        }

    simple_manifest = _read_json(simple_manifest_path)
    simple_metrics = simple_manifest.get("metrics", {})
    simple_walk_forward_metrics = simple_manifest.get("walk_forward_metrics", {})
    split_comparisons: dict[str, Any] = {}
    walk_forward_comparisons: dict[str, Any] = {}
    advanced_better_count = 0
    simple_better_count = 0
    mixed_or_inconclusive_count = 0

    for key, advanced_payload in sorted(advanced_metrics.items()):
        simple_payload = simple_metrics.get(key)
        if not isinstance(advanced_payload, dict) or not isinstance(simple_payload, dict):
            continue
        comparison = _advanced_simple_metric_delta(advanced_payload, simple_payload)
        split_comparisons[key] = comparison
        category = comparison["comparison_category"]
        advanced_better_count += int(category == "advanced_better")
        simple_better_count += int(category == "simple_better")
        mixed_or_inconclusive_count += int(category == "mixed_or_inconclusive")

    for key, advanced_payload in sorted(advanced_walk_forward_metrics.items()):
        simple_payload = simple_walk_forward_metrics.get(key)
        if not isinstance(advanced_payload, dict) or not isinstance(simple_payload, dict):
            continue
        walk_forward_comparisons[key] = _advanced_simple_metric_delta(advanced_payload, simple_payload)

    total = advanced_better_count + simple_better_count + mixed_or_inconclusive_count
    return {
        "available": True,
        "compared_metrics": ["accuracy", "balanced_accuracy", "macro_f1"],
        "split_metric_comparisons": split_comparisons,
        "walk_forward_metric_comparisons": walk_forward_comparisons,
        "advanced_better_count": advanced_better_count,
        "simple_better_count": simple_better_count,
        "mixed_or_inconclusive_count": mixed_or_inconclusive_count,
        "advanced_improvement_consistency": _round_metric(advanced_better_count / total) if total else 0.0,
        "descriptive_only": True,
        "non_actionable": True,
        "warnings": [],
    }


def _advanced_simple_metric_delta(advanced_payload: dict[str, Any], simple_payload: dict[str, Any]) -> dict[str, Any]:
    accuracy_delta = _round_metric(float(advanced_payload["accuracy"]) - float(simple_payload["accuracy"]))
    balanced_accuracy_delta = _round_metric(float(advanced_payload["balanced_accuracy"]) - float(simple_payload["balanced_accuracy"]))
    macro_f1_delta = _round_metric(float(advanced_payload["macro_f1"]) - float(simple_payload["macro_f1"]))
    category = "mixed_or_inconclusive"
    if accuracy_delta > 0 and macro_f1_delta > 0:
        category = "advanced_better"
    elif accuracy_delta < 0 and macro_f1_delta < 0:
        category = "simple_better"
    return {
        "timeframe": advanced_payload.get("timeframe"),
        "model_name": advanced_payload.get("model_name"),
        "split": advanced_payload.get("split"),
        "walk_forward_group": advanced_payload.get("walk_forward_group"),
        "advanced_accuracy": float(advanced_payload["accuracy"]),
        "simple_accuracy": float(simple_payload["accuracy"]),
        "delta_advanced_minus_simple_accuracy": accuracy_delta,
        "advanced_balanced_accuracy": float(advanced_payload["balanced_accuracy"]),
        "simple_balanced_accuracy": float(simple_payload["balanced_accuracy"]),
        "delta_advanced_minus_simple_balanced_accuracy": balanced_accuracy_delta,
        "advanced_macro_f1": float(advanced_payload["macro_f1"]),
        "simple_macro_f1": float(simple_payload["macro_f1"]),
        "delta_advanced_minus_simple_macro_f1": macro_f1_delta,
        "comparison_category": category,
        "descriptive_only": True,
        "non_actionable": True,
    }


def compute_advanced_ohlcv_label_shuffle_falsification_v6_3(root: Path, ml_manifest: dict[str, Any]) -> dict[str, Any]:
    root = root.resolve()
    original_metrics = ml_manifest["metrics"]
    dataset_manifest = _read_json(root / MANIFEST_PATH_V6_1)
    falsification: dict[str, Any] = {}
    needed_columns = [
        *ALLOWED_FEATURE_COLUMNS_V6_2,
        TARGET_NAME_V6_2,
        "label_valid_h1",
        "warmup_row",
        "split",
    ]
    for timeframe in TIMEFRAMES_V6_2:
        rng = np.random.default_rng(LABEL_SHUFFLE_RANDOM_SEED_V6_3)
        dataset_path = input_dataset_path(root, timeframe, dataset_manifest)
        dataset = pd.read_parquet(dataset_path, columns=needed_columns, engine="pyarrow")
        ml_frame = dataset[(dataset["label_valid_h1"] == True) & (dataset["warmup_row"] == False)].copy()  # noqa: E712
        slices = {split: ml_frame[ml_frame["split"] == split].copy() for split in ROBUSTNESS_SPLITS_V6_3}
        train = slices["train"]
        shuffled_train_target = pd.Series(rng.permutation(train[TARGET_NAME_V6_2].astype(str).to_numpy()), index=train.index)
        predict_frame = pd.concat([slices[split] for split in EVALUATION_SPLITS_V6_3], axis=0)
        for model_name in ROBUSTNESS_MODELS_V6_3:
            result = fit_predict_model(
                model_name,
                train[ALLOWED_FEATURE_COLUMNS_V6_2],
                shuffled_train_target,
                predict_frame[ALLOWED_FEATURE_COLUMNS_V6_2],
            )
            for split in EVALUATION_SPLITS_V6_3:
                split_frame = slices[split]
                y_true = split_frame[TARGET_NAME_V6_2].astype(str)
                y_pred = result.predicted_class.loc[split_frame.index].astype(str)
                shuffled_metrics = _classification_summary(y_true, y_pred)
                original = original_metrics[f"{timeframe}.{model_name}.{split}"]
                no_clear_edge = (
                    original["accuracy"] <= shuffled_metrics["accuracy"]
                    or original["macro_f1"] <= shuffled_metrics["macro_f1"]
                )
                falsification[f"{timeframe}.{model_name}.{split}"] = {
                    "timeframe": timeframe,
                    "model_name": model_name,
                    "split": split,
                    "random_seed": LABEL_SHUFFLE_RANDOM_SEED_V6_3,
                    "shuffle_scope": "train_labels_only",
                    "validation_test_contaminated": False,
                    "original_accuracy": float(original["accuracy"]),
                    "original_macro_f1": float(original["macro_f1"]),
                    "shuffled_accuracy": shuffled_metrics["accuracy"],
                    "shuffled_macro_f1": shuffled_metrics["macro_f1"],
                    "accuracy_delta_original_minus_shuffled": _round_metric(original["accuracy"] - shuffled_metrics["accuracy"]),
                    "macro_f1_delta_original_minus_shuffled": _round_metric(original["macro_f1"] - shuffled_metrics["macro_f1"]),
                    "no_clear_edge_vs_shuffled_labels": bool(no_clear_edge),
                }
    return falsification


def scan_advanced_ohlcv_feature_leakage_v6_3(feature_columns: list[str]) -> dict[str, Any]:
    exact_terms = {term.casefold() for term in FORBIDDEN_ROBUSTNESS_FEATURE_EXACT_V6_3}
    prefix_terms = tuple(term.casefold() for term in FORBIDDEN_ROBUSTNESS_FEATURE_PREFIXES_V6_3)
    forbidden: list[str] = []
    for column in feature_columns:
        folded = str(column).casefold()
        if folded in exact_terms or folded.startswith(prefix_terms):
            forbidden.append(str(column))
    return {
        "feature_columns_checked": list(feature_columns),
        "macd_like_signal_allowed": "macd_like_signal" in feature_columns,
        "forbidden_feature_columns_present": forbidden,
        "feature_leakage_detected": bool(forbidden),
    }


def scan_advanced_ohlcv_metric_forbidden_terms_v6_3(payload: Any) -> dict[str, Any]:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True).casefold()
    present = [term for term in FORBIDDEN_ROBUSTNESS_METRIC_TERMS_V6_3 if term in text]
    return {
        "forbidden_terms": FORBIDDEN_ROBUSTNESS_METRIC_TERMS_V6_3,
        "forbidden_terms_present": present,
        "metric_forbidden_terms_detected": bool(present),
    }


def build_advanced_ohlcv_ml_robustness_markdown_v6_3(manifest: dict[str, Any]) -> str:
    findings = manifest["findings"]
    warning_count = len(findings["warnings"])
    lines = [
        "# Audit robustesse, walk-forward et falsification - V6.3",
        "",
        "## Objectif",
        "",
        "V6.3 audite les resultats ML offline V6.2 avec des analyses descriptives et falsifiables sur la fenetre historique continue.",
        "Cet audit ne transforme pas les scores en decision operationnelle.",
        "",
        "## Analyses",
        "",
        "- `baseline_delta` compare chaque modele aux baselines majority et random.",
        "- `split_stability` mesure les ecarts train / validation / test.",
        "- `timeframe_stability` compare les resultats entre 1m, 5m, 15m et 1h.",
        "- `walk_forward_stability` resume les metriques descriptives par groupe walk-forward.",
        "- `advanced_vs_simple_comparison` compare descriptivement V6.2 advanced OHLCV a V5.4 simple OHLCV si la reference est disponible.",
        "- `label_shuffle_falsification` entraine logistic regression et decision tree depth 2 avec labels train melanges, seed 123.",
        "- `feature_leakage_scan` verifie la liste de features V6.2 ; `macd_like_signal` reste autorisee comme feature technique.",
        "- `metric_forbidden_scan` verifie l'absence de metriques de trading interdites.",
        "",
        "## Findings",
        "",
        f"- Robust edge claimed : `{findings['robust_edge_claimed']}`.",
        f"- Validation de strategie declaree : `{findings['strategy_validated']}`.",
        f"- Backtest effectue : `{findings['backtest_performed']}`.",
        f"- Signal actionnable produit : `{findings['actionable_signal_produced']}`.",
        f"- Advanced features validees pour trading : `{findings['advanced_features_validated_for_trading']}`.",
        f"- Warnings : `{warning_count}`.",
        "",
        "## Limitations",
        "",
        *[f"- {item}" for item in manifest["limitations"]],
        "",
        "## Avertissements d'usage",
        "",
        "- V6.3 ne valide aucune strategie.",
        "- V6.3 ne valide aucun modele exploitable en trading.",
        "- V6.3 ne valide pas les advanced features pour trading.",
        "- V6.3 ne produit aucun backtest.",
        "- V6.3 ne produit aucun signal de trading.",
        "- V6.3 ne produit aucun ordre.",
        "- V6.3 n'autorise aucun paper live.",
        "- V6.3 n'autorise aucun trading reel.",
        "- Les resultats sont descriptifs et falsifiables.",
        "- Les metriques walk-forward ne sont pas un backtest.",
        "- La comparaison advanced vs simple OHLCV est descriptive, non actionnable.",
        "- Toute interpretation doit rester prudente.",
    ]
    return "\n".join(lines) + "\n"


def _validate_inputs(root: Path) -> None:
    dataset_result = validate_advanced_ohlcv_offline_supervised_dataset_v6_1(root)
    if not dataset_result["passed"]:
        raise RuntimeError(f"V6.1 dataset validation failed before V6.3: {dataset_result['errors']}")
    ml_result = validate_advanced_ohlcv_offline_ml_research_v6_2(root)
    if not ml_result["passed"]:
        raise RuntimeError(f"V6.2 ML validation failed before V6.3: {ml_result['errors']}")


def _input_score_files(root: Path, ml_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    window = ml_manifest["input_dataset_manifest"]
    blocks: dict[str, dict[str, Any]] = {}
    for timeframe in TIMEFRAMES_V6_2:
        path = score_output_path(root, timeframe, window["window_start"], window["window_end"])
        blocks[timeframe] = {
            "path": str(path.relative_to(root)),
            "sha256": sha256_file(path),
            "rows": int(ml_manifest["outputs"][timeframe]["rows"]),
        }
    return blocks


def _classification_summary(y_true: pd.Series, y_pred: pd.Series) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=TARGET_CLASSES_V6_2, average="macro", zero_division=0)),
    }


def _collect_warnings(analyses: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for key, value in analyses["split_stability"].items():
        if value["overfit_warning"]:
            warnings.append(f"split stability warning: {key}")
    for key, value in analyses["timeframe_stability"].items():
        if value["single_timeframe_concentration_warning"]:
            warnings.append(f"timeframe concentration warning: {key}")
    for key, value in analyses["walk_forward_stability"].items():
        if value["concentrated_on_few_groups_warning"]:
            warnings.append(f"walk-forward concentration warning: {key}")
    warnings.extend(analyses["advanced_vs_simple_comparison"].get("warnings", []))
    for key, value in analyses["label_shuffle_falsification"].items():
        if value["no_clear_edge_vs_shuffled_labels"]:
            warnings.append(f"no clear edge vs shuffled labels: {key}")
    return sorted(warnings)


def _robustness_run_id() -> str:
    return f"{ROBUSTNESS_RUN_ID_PREFIX_V6_3}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"


def _round_metric(value: float) -> float:
    return round(float(value), 12)


def _update_project_state(root: Path, manifest: dict[str, Any]) -> None:
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    state.update(
        {
            "last_validated_version": "V6.2",
            "candidate_version": "V6.3",
            "candidate_status": "pending_external_audit",
            "direction": "advanced OHLCV robustness and walk-forward falsification audit",
            "advanced_ohlcv_robustness_window_start_v6_3": manifest["input_ml_manifest"]["window_start"],
            "advanced_ohlcv_robustness_window_end_v6_3": manifest["input_ml_manifest"]["window_end"],
            "advanced_ohlcv_robustness_days_v6_3": manifest["input_ml_manifest"]["total_days"],
            "advanced_feature_columns_count_v6_3": manifest["input_ml_manifest"]["advanced_feature_columns_count"],
            "backtest_v6_3_created": False,
            "strategy_v6_3_created": False,
            "signal_v6_3_created": False,
            "orders_v6_3_created": False,
            "paper_live_v6_3_created": False,
            "trading_v6_3_created": False,
            "persistent_model_v6_3_created": False,
            "backtest_enabled": False,
            "strategy_enabled": False,
            "paper_live_enabled": False,
            "orders_enabled": False,
            "trading_enabled": False,
            "execution_enabled": False,
            "api_key_used": False,
            "private_endpoint_used": False,
            "authentication_used": False,
        }
    )
    _write_json(state_path, state)
    _write_json(root / "reports/current/latest_metrics.json", _latest_metrics_payload(manifest))
    _write_text(root / "reports/PROJECT_STATE.md", _project_state_markdown(manifest))
    _write_text(root / "reports/current/latest_metrics.md", _latest_metrics_markdown(manifest))
    _write_text(root / "reports/current/latest_summary.md", _latest_summary_markdown(manifest))


def _latest_metrics_payload(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "last_validated_version": "V6.2",
        "candidate_version": "V6.3",
        "candidate_status": "pending_external_audit",
        "direction": "advanced OHLCV robustness and walk-forward falsification audit",
        "input_window_start": manifest["input_ml_manifest"]["window_start"],
        "input_window_end": manifest["input_ml_manifest"]["window_end"],
        "input_total_days": manifest["input_ml_manifest"]["total_days"],
        "advanced_feature_columns_count": manifest["input_ml_manifest"]["advanced_feature_columns_count"],
        "analyses": sorted(manifest["analyses"]),
        "warnings_count": len(manifest["findings"]["warnings"]),
        "robust_edge_claimed": False,
        "strategy_validated": False,
        "backtest_performed": False,
        "actionable_signal_produced": False,
        "backtest_enabled": False,
        "strategy_enabled": False,
        "paper_live_enabled": False,
        "orders_enabled": False,
        "trading_enabled": False,
        "execution_enabled": False,
        "api_key_used": False,
        "private_endpoint_used": False,
        "authentication_used": False,
        "external_validation_required": True,
    }


def _project_state_markdown(manifest: dict[str, Any]) -> str:
    return f"""# Etat du Projet : V6.2 validee + candidat V6.3

- **Derniere version validee** : V6.2.
- **Version candidate** : V6.3.
- **Statut candidate** : `pending_external_audit`.
- **Direction** : advanced OHLCV robustness and walk-forward falsification audit.

## Candidat V6.3

- Fenetre : `{manifest['input_ml_manifest']['window_start']}` -> `{manifest['input_ml_manifest']['window_end']}`.
- Nombre de jours : `{manifest['input_ml_manifest']['total_days']}`.
- Advanced feature columns count : `{manifest['input_ml_manifest']['advanced_feature_columns_count']}`.
- Analyses : `{sorted(manifest['analyses'])}`.
- Warnings descriptifs : `{len(manifest['findings']['warnings'])}`.
- V6.3 reste candidate `pending_external_audit`.

## Clause De Securite

- Aucun trading reel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucune strategie.
- Aucun signal de trading.
- Aucun modele persistant.
- Aucune API privee.
- Aucune cle API.
- V6.3 reste non validee avant audit externe.
"""


def _latest_metrics_markdown(manifest: dict[str, Any]) -> str:
    return f"""# Latest Metrics V6.3

- Derniere version validee : V6.2.
- Candidate : V6.3.
- Statut : `pending_external_audit`.
- Direction : advanced OHLCV robustness and walk-forward falsification audit.
- Fenetre : `{manifest['input_ml_manifest']['window_start']}` -> `{manifest['input_ml_manifest']['window_end']}`.
- Total jours : `{manifest['input_ml_manifest']['total_days']}`.
- Advanced feature columns count : `{manifest['input_ml_manifest']['advanced_feature_columns_count']}`.
- Warnings descriptifs : `{len(manifest['findings']['warnings'])}`.

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun modele persistant et aucun trading reel.
"""


def _latest_summary_markdown(manifest: dict[str, Any]) -> str:
    return f"""# Latest Summary V6.3

V6.2 est la derniere version validee par audit externe.

V6.3 est la candidate courante. Elle audite uniquement la robustesse descriptive, les groupes walk-forward et la falsification par label shuffle des resultats ML offline V6.2.

Fenetre utilisee : `{manifest['input_ml_manifest']['window_start']}` -> `{manifest['input_ml_manifest']['window_end']}`.

Total jours : `{manifest['input_ml_manifest']['total_days']}`.

Advanced feature columns count : `{manifest['input_ml_manifest']['advanced_feature_columns_count']}`.

Analyses produites : `{sorted(manifest['analyses'])}`.

Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucune strategie, aucun signal de trading, aucun modele persistant et aucun claim de rentabilite.

V6.3 reste `pending_external_audit`.
"""


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
