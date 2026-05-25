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
from galapagos.datasets.ohlcv_trades_90d_window_validation import validate_ohlcv_trades_90d_offline_supervised_dataset_v7_9
from galapagos.datasets.schemas import MANIFEST_PATH_V7_9
from galapagos.ml.ohlcv_trades_90d_window import input_dataset_path, score_output_path
from galapagos.ml.ohlcv_trades_90d_window_validation import validate_ohlcv_trades_90d_offline_ml_research_v8_0
from galapagos.ml.offline_baselines import fit_predict_model
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V8_0,
    MANIFEST_PATH_V5_4,
    MANIFEST_PATH_V6_2,
    MANIFEST_PATH_V7_4,
    MODEL_NAMES_V8_0,
    MANIFEST_PATH_V8_0 as ML_MANIFEST_PATH_V8_0,
    REPORT_JSON_PATH_V5_4,
    REPORT_JSON_PATH_V6_2,
    REPORT_JSON_PATH_V8_0 as ML_REPORT_JSON_PATH_V8_0,
    SCORES_JSON_PATH_V5_4,
    SCORES_JSON_PATH_V6_2,
    SCORES_JSON_PATH_V8_0 as ML_SCORES_JSON_PATH_V8_0,
    TARGET_CLASSES_V8_0,
    TARGET_NAME_V8_0,
    TIMEFRAMES_V8_0,
)


VERSION_V8_0 = "V8.0"
ROBUSTNESS_RUN_ID_PREFIX_V8_0 = "v8_0"
ROBUSTNESS_MANIFEST_PATH_V8_0 = Path("reports/manifests/ohlcv_trades_90d_ml_robustness_v8_0_manifest.json")
ROBUSTNESS_REPORT_JSON_PATH_V8_0 = Path("reports/ml/ohlcv_trades_90d_ml_robustness_v8_0.json")
ROBUSTNESS_REPORT_MD_PATH_V8_0 = Path("reports/ml/ohlcv_trades_90d_ml_robustness_v8_0.md")
ROBUSTNESS_DOC_PATH_V8_0 = Path("docs/ohlcv_trades_90d_ml_robustness_v8_0.md")
MANIFEST_PATH_V8_0 = ROBUSTNESS_MANIFEST_PATH_V8_0
REPORT_JSON_PATH_V8_0 = ROBUSTNESS_REPORT_JSON_PATH_V8_0
REPORT_MD_PATH_V8_0 = ROBUSTNESS_REPORT_MD_PATH_V8_0
DOC_PATH_V8_0 = ROBUSTNESS_DOC_PATH_V8_0
ACCURACY_GAP_WARNING_THRESHOLD_V8_0 = 0.10
MACRO_F1_GAP_WARNING_THRESHOLD_V8_0 = 0.10
LABEL_SHUFFLE_RANDOM_SEED_V8_0 = 123
ROBUSTNESS_MODELS_V8_0 = ["logistic_regression", "decision_tree_depth_2"]
ROBUSTNESS_SPLITS_V8_0 = ["train", "validation", "test"]
EVALUATION_SPLITS_V8_0 = ["validation", "test"]
WALK_FORWARD_WEAK_ACCURACY_THRESHOLD_V8_0 = 0.34
WALK_FORWARD_WEAK_MACRO_F1_THRESHOLD_V8_0 = 0.20
FORBIDDEN_ROBUSTNESS_FEATURE_PREFIXES_V8_0 = [
    "future_",
    "label_",
    "direction_",
    "up_down_flat_",
]
FORBIDDEN_ROBUSTNESS_FEATURE_EXACT_V8_0 = [
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
FORBIDDEN_ROBUSTNESS_METRIC_TERMS_V8_0 = [
    "sharpe",
    "drawdown",
    "pnl",
    "equity_curve",
    "profit_factor",
    "trading_win_rate",
]
EXPECTED_LIMITATIONS_V8_0 = [
    "V8.0 entraine uniquement des baselines ML offline simples sur le dataset OHLCV + aggTrades 90 jours V7.9.",
    "V8.0 produit une robustesse descriptive et une falsification offline, sans backtest, sans strategie, sans signal de trading et sans ordre.",
    "La fenetre de 90 jours reste insuffisante pour conclure a une robustesse statistique forte.",
]
SAFETY_FLAGS_V8_0 = {
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


def run_ohlcv_trades_90d_ml_robustness_v8_0(
    root: Path = Path("."),
    *,
    validate_inputs: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_inputs:
        _validate_inputs(root)

    dataset_manifest = _read_json(root / MANIFEST_PATH_V7_9)
    ml_manifest = _read_json(root / ML_MANIFEST_PATH_V8_0)
    ml_report = _read_json(root / ML_REPORT_JSON_PATH_V8_0)
    scores_report = _read_json(root / ML_SCORES_JSON_PATH_V8_0)
    window = ml_manifest["input_dataset_manifest"]
    metrics = ml_manifest["metrics"]
    walk_forward_metrics = ml_manifest["walk_forward_metrics"]
    reference_reports = build_reference_reports_v8_0(root)

    analyses: dict[str, Any] = {
        "baseline_delta": compute_ohlcv_trades_baseline_delta_v8_0(metrics),
        "split_stability": compute_ohlcv_trades_split_stability_v8_0(metrics),
        "timeframe_stability": compute_ohlcv_trades_timeframe_stability_v8_0(metrics),
        "walk_forward_stability": compute_ohlcv_trades_walk_forward_stability_v8_0(walk_forward_metrics),
        "ohlcv_trades_90d_vs_references_comparison": compute_ohlcv_trades_90d_vs_references_comparison_v8_0(root, metrics, walk_forward_metrics),
        "label_shuffle_falsification": compute_ohlcv_trades_label_shuffle_falsification_v8_0(root, ml_manifest),
        "feature_leakage_scan": scan_ohlcv_trades_feature_leakage_v8_0(ml_manifest["feature_columns"]),
    }
    analyses["metric_forbidden_scan"] = scan_ohlcv_trades_metric_forbidden_terms_v8_0(
        {
            "ml_manifest_metrics": ml_manifest.get("metrics", {}),
            "ml_manifest_walk_forward_metrics": ml_manifest.get("walk_forward_metrics", {}),
            "ml_report_metrics": ml_report.get("metrics", {}),
            "ml_report_walk_forward_metrics": ml_report.get("walk_forward_metrics", {}),
            "scores_report": scores_report,
            "v8_0_analyses": analyses,
        }
    )

    warnings = _collect_warnings(analyses)
    status = "PASS"
    if analyses["feature_leakage_scan"]["forbidden_feature_columns_present"]:
        status = "FAIL"
    if analyses["metric_forbidden_scan"]["forbidden_terms_present"]:
        status = "FAIL"

    manifest = {
        "version": VERSION_V8_0,
        "status": status,
        "created_at_utc": utc_now_iso(),
        "robustness_run_id": _robustness_run_id(),
        "input_dataset_manifest": {
            "path": MANIFEST_PATH_V7_9.as_posix(),
            "sha256": sha256_file(root / MANIFEST_PATH_V7_9),
            "window_start": window["window_start"],
            "window_end": window["window_end"],
            "total_days": int(window["total_days"]),
            "feature_columns_count": int(dataset_manifest["feature_columns_count"]),
        },
        "input_ml_manifest": {
            "path": ML_MANIFEST_PATH_V8_0.as_posix(),
            "sha256": sha256_file(root / ML_MANIFEST_PATH_V8_0),
            "window_start": window["window_start"],
            "window_end": window["window_end"],
            "total_days": int(window["total_days"]),
            "feature_columns_count": int(ml_manifest["feature_columns_count"]),
        },
        "input_score_files": _input_score_files(root, ml_manifest),
        "reference_reports": reference_reports,
        "analyses": analyses,
        "thresholds": {
            "accuracy_gap_warning_threshold": ACCURACY_GAP_WARNING_THRESHOLD_V8_0,
            "macro_f1_gap_warning_threshold": MACRO_F1_GAP_WARNING_THRESHOLD_V8_0,
            "random_seed": LABEL_SHUFFLE_RANDOM_SEED_V8_0,
        },
        "findings": {
            "robust_edge_claimed": False,
            "strategy_validated": False,
            "backtest_performed": False,
            "actionable_signal_produced": False,
            "ohlcv_trades_validated_for_trading": False,
            "warnings": warnings,
        },
        "safety": SAFETY_FLAGS_V8_0,
        "limitations": EXPECTED_LIMITATIONS_V8_0,
    }
    _write_json(root / ROBUSTNESS_MANIFEST_PATH_V8_0, manifest)
    _write_json(root / ROBUSTNESS_REPORT_JSON_PATH_V8_0, manifest)
    markdown = build_ohlcv_trades_ml_robustness_markdown_v8_0(manifest)
    _write_text(root / ROBUSTNESS_REPORT_MD_PATH_V8_0, markdown)
    _write_text(root / ROBUSTNESS_DOC_PATH_V8_0, markdown)
    _update_project_state(root, manifest)
    return manifest


def compute_ohlcv_trades_baseline_delta_v8_0(metrics: dict[str, Any]) -> dict[str, Any]:
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


def compute_ohlcv_trades_split_stability_v8_0(metrics: dict[str, Any]) -> dict[str, Any]:
    stability: dict[str, Any] = {}
    models = sorted({metric["model_name"] for metric in metrics.values()})
    timeframes = sorted({metric["timeframe"] for metric in metrics.values()}, key=TIMEFRAMES_V8_0.index)
    for timeframe in timeframes:
        for model_name in models:
            split_metrics = {split: metrics.get(f"{timeframe}.{model_name}.{split}") for split in ROBUSTNESS_SPLITS_V8_0}
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
                train_validation_accuracy_gap > ACCURACY_GAP_WARNING_THRESHOLD_V8_0
                or train_validation_macro_f1_gap > MACRO_F1_GAP_WARNING_THRESHOLD_V8_0
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


def compute_ohlcv_trades_timeframe_stability_v8_0(metrics: dict[str, Any]) -> dict[str, Any]:
    stability: dict[str, Any] = {}
    models = sorted({metric["model_name"] for metric in metrics.values()})
    for model_name in models:
        test_metrics = {
            timeframe: metrics[f"{timeframe}.{model_name}.test"]
            for timeframe in TIMEFRAMES_V8_0
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
            "single_timeframe_concentration_warning": bool(sorted_accuracy[0][1] - second_accuracy > ACCURACY_GAP_WARNING_THRESHOLD_V8_0),
        }
    return stability


def compute_ohlcv_trades_walk_forward_stability_v8_0(walk_forward_metrics: dict[str, Any]) -> dict[str, Any]:
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
            if accuracy_by_group[group] < WALK_FORWARD_WEAK_ACCURACY_THRESHOLD_V8_0
            or macro_f1_by_group[group] < WALK_FORWARD_WEAK_MACRO_F1_THRESHOLD_V8_0
        ]
        unstable_groups = [
            group
            for group in accuracy_by_group
            if abs(accuracy_by_group[group] - mean_accuracy) > ACCURACY_GAP_WARNING_THRESHOLD_V8_0
            or abs(macro_f1_by_group[group] - mean_macro_f1) > MACRO_F1_GAP_WARNING_THRESHOLD_V8_0
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


def build_reference_reports_v8_0(root: Path) -> dict[str, Any]:
    warnings: list[str] = []
    v7_4_available = (root / MANIFEST_PATH_V7_4).exists()
    v6_2_available = (root / MANIFEST_PATH_V6_2).exists()
    v5_4_available = (root / MANIFEST_PATH_V5_4).exists()
    if not v7_4_available:
        warnings.append("V7.4 OHLCV+trades 30-day reference manifest is unavailable; comparison is skipped.")
    if not v6_2_available:
        warnings.append("V6.2 advanced OHLCV reference manifest is unavailable; comparison is skipped.")
    if not v5_4_available:
        warnings.append("V5.4 simple OHLCV reference manifest is unavailable; comparison is skipped.")
    if v6_2_available and not (root / REPORT_JSON_PATH_V6_2).exists():
        warnings.append("V6.2 advanced OHLCV quality report is unavailable.")
    if v6_2_available and not (root / SCORES_JSON_PATH_V6_2).exists():
        warnings.append("V6.2 advanced OHLCV scores report is unavailable.")
    if v5_4_available and not (root / REPORT_JSON_PATH_V5_4).exists():
        warnings.append("V5.4 simple OHLCV quality report is unavailable.")
    if v5_4_available and not (root / SCORES_JSON_PATH_V5_4).exists():
        warnings.append("V5.4 simple OHLCV scores report is unavailable.")
    if v7_4_available or v6_2_available or v5_4_available:
        warnings.append("not directly comparable due to different window length/source set")
    return {
        "v7_4_available": bool(v7_4_available),
        "v7_4_manifest_path": MANIFEST_PATH_V7_4.as_posix(),
        "v7_4_manifest_sha256": sha256_file(root / MANIFEST_PATH_V7_4) if v7_4_available else None,
        "v6_2_available": bool(v6_2_available),
        "v6_2_manifest_path": MANIFEST_PATH_V6_2.as_posix(),
        "v6_2_manifest_sha256": sha256_file(root / MANIFEST_PATH_V6_2) if v6_2_available else None,
        "v5_4_available": bool(v5_4_available),
        "v5_4_manifest_path": MANIFEST_PATH_V5_4.as_posix(),
        "v5_4_manifest_sha256": sha256_file(root / MANIFEST_PATH_V5_4) if v5_4_available else None,
        "warnings": warnings,
    }


def compute_ohlcv_trades_90d_vs_references_comparison_v8_0(
    root: Path,
    ohlcv_trades_metrics: dict[str, Any],
    ohlcv_trades_walk_forward_metrics: dict[str, Any],
) -> dict[str, Any]:
    references = {
        "ohlcv_trades_30d_v7_4": {
            "manifest_path": MANIFEST_PATH_V7_4,
            "reference_label": "V7.4 OHLCV+trades 30 jours",
        },
        "advanced_ohlcv_v6_2": {
            "manifest_path": MANIFEST_PATH_V6_2,
            "reference_label": "V6.2 advanced OHLCV",
        },
        "simple_ohlcv_v5_4": {
            "manifest_path": MANIFEST_PATH_V5_4,
            "reference_label": "V5.4 simple OHLCV",
        },
    }
    compared: dict[str, Any] = {}
    for reference_name, reference in references.items():
        compared[reference_name] = _compare_single_reference_v8_0(
            root,
            reference_name,
            reference["reference_label"],
            reference["manifest_path"],
            ohlcv_trades_metrics,
            ohlcv_trades_walk_forward_metrics,
        )
    return {
        "available_references": [name for name, payload in compared.items() if payload["available"]],
        "references": compared,
        "compared_metrics": ["accuracy", "balanced_accuracy", "macro_f1"],
        "descriptive_only": True,
        "non_actionable": True,
        "not_directly_comparable": True,
        "warnings": sorted(
            {
                warning
                for payload in compared.values()
                for warning in payload.get("warnings", [])
            }
        ),
    }


def _compare_single_reference_v8_0(
    root: Path,
    reference_name: str,
    reference_label: str,
    reference_manifest_path: Path,
    ohlcv_trades_metrics: dict[str, Any],
    ohlcv_trades_walk_forward_metrics: dict[str, Any],
) -> dict[str, Any]:
    manifest_path = root / reference_manifest_path
    if not manifest_path.exists():
        return {
            "available": False,
            "reference_name": reference_name,
            "reference_label": reference_label,
            "reference_manifest_path": reference_manifest_path.as_posix(),
            "compared_metrics": ["accuracy", "balanced_accuracy", "macro_f1"],
            "split_metric_comparisons": {},
            "walk_forward_metric_comparisons": {},
            "ohlcv_trades_better_count": 0,
            "reference_better_count": 0,
            "mixed_or_inconclusive_count": 0,
            "ohlcv_trades_improvement_consistency": 0.0,
            "descriptive_only": True,
            "non_actionable": True,
            "not_directly_comparable": True,
            "warnings": [f"{reference_label} manifest is unavailable; comparison is skipped."],
        }

    reference_manifest = _read_json(manifest_path)
    reference_metrics = reference_manifest.get("metrics", {})
    reference_walk_forward_metrics = reference_manifest.get("walk_forward_metrics", {})
    split_comparisons: dict[str, Any] = {}
    walk_forward_comparisons: dict[str, Any] = {}
    ohlcv_trades_better_count = 0
    reference_better_count = 0
    mixed_or_inconclusive_count = 0

    for key, ohlcv_trades_payload in sorted(ohlcv_trades_metrics.items()):
        reference_payload = reference_metrics.get(key)
        if not isinstance(ohlcv_trades_payload, dict) or not isinstance(reference_payload, dict):
            continue
        comparison = _ohlcv_trades_reference_metric_delta(ohlcv_trades_payload, reference_payload, reference_name)
        split_comparisons[key] = comparison
        category = comparison["comparison_category"]
        ohlcv_trades_better_count += int(category == "ohlcv_trades_better")
        reference_better_count += int(category == "reference_better")
        mixed_or_inconclusive_count += int(category == "mixed_or_inconclusive")

    for key, ohlcv_trades_payload in sorted(ohlcv_trades_walk_forward_metrics.items()):
        reference_payload = reference_walk_forward_metrics.get(key)
        if not isinstance(ohlcv_trades_payload, dict) or not isinstance(reference_payload, dict):
            continue
        walk_forward_comparisons[key] = _ohlcv_trades_reference_metric_delta(ohlcv_trades_payload, reference_payload, reference_name)

    total = ohlcv_trades_better_count + reference_better_count + mixed_or_inconclusive_count
    return {
        "available": True,
        "reference_name": reference_name,
        "reference_label": reference_label,
        "reference_manifest_path": reference_manifest_path.as_posix(),
        "reference_manifest_sha256": sha256_file(manifest_path),
        "compared_metrics": ["accuracy", "balanced_accuracy", "macro_f1"],
        "split_metric_comparisons": split_comparisons,
        "walk_forward_metric_comparisons": walk_forward_comparisons,
        "ohlcv_trades_better_count": ohlcv_trades_better_count,
        "reference_better_count": reference_better_count,
        "mixed_or_inconclusive_count": mixed_or_inconclusive_count,
        "ohlcv_trades_improvement_consistency": _round_metric(ohlcv_trades_better_count / total) if total else 0.0,
        "descriptive_only": True,
        "non_actionable": True,
        "not_directly_comparable": True,
        "warnings": ["not directly comparable due to different window length/source set"],
    }


def _ohlcv_trades_reference_metric_delta(
    ohlcv_trades_payload: dict[str, Any],
    reference_payload: dict[str, Any],
    reference_name: str,
) -> dict[str, Any]:
    accuracy_delta = _round_metric(float(ohlcv_trades_payload["accuracy"]) - float(reference_payload["accuracy"]))
    balanced_accuracy_delta = _round_metric(float(ohlcv_trades_payload["balanced_accuracy"]) - float(reference_payload["balanced_accuracy"]))
    macro_f1_delta = _round_metric(float(ohlcv_trades_payload["macro_f1"]) - float(reference_payload["macro_f1"]))
    category = "mixed_or_inconclusive"
    if accuracy_delta > 0 and macro_f1_delta > 0:
        category = "ohlcv_trades_better"
    elif accuracy_delta < 0 and macro_f1_delta < 0:
        category = "reference_better"
    return {
        "timeframe": ohlcv_trades_payload.get("timeframe"),
        "model_name": ohlcv_trades_payload.get("model_name"),
        "split": ohlcv_trades_payload.get("split"),
        "walk_forward_group": ohlcv_trades_payload.get("walk_forward_group"),
        "reference_name": reference_name,
        "ohlcv_trades_accuracy": float(ohlcv_trades_payload["accuracy"]),
        "reference_accuracy": float(reference_payload["accuracy"]),
        "delta_ohlcv_trades_minus_reference_accuracy": accuracy_delta,
        "ohlcv_trades_balanced_accuracy": float(ohlcv_trades_payload["balanced_accuracy"]),
        "reference_balanced_accuracy": float(reference_payload["balanced_accuracy"]),
        "delta_ohlcv_trades_minus_reference_balanced_accuracy": balanced_accuracy_delta,
        "ohlcv_trades_macro_f1": float(ohlcv_trades_payload["macro_f1"]),
        "reference_macro_f1": float(reference_payload["macro_f1"]),
        "delta_ohlcv_trades_minus_reference_macro_f1": macro_f1_delta,
        "comparison_category": category,
        "descriptive_only": True,
        "non_actionable": True,
        "not_directly_comparable": True,
    }


def compute_ohlcv_trades_label_shuffle_falsification_v8_0(root: Path, ml_manifest: dict[str, Any]) -> dict[str, Any]:
    root = root.resolve()
    original_metrics = ml_manifest["metrics"]
    dataset_manifest = _read_json(root / MANIFEST_PATH_V7_9)
    falsification: dict[str, Any] = {}
    needed_columns = [
        *ALLOWED_FEATURE_COLUMNS_V8_0,
        TARGET_NAME_V8_0,
        "label_valid_h1",
        "warmup_row",
        "split",
    ]
    for timeframe in TIMEFRAMES_V8_0:
        rng = np.random.default_rng(LABEL_SHUFFLE_RANDOM_SEED_V8_0)
        dataset_path = input_dataset_path(root, timeframe, dataset_manifest)
        dataset = pd.read_parquet(dataset_path, columns=needed_columns, engine="pyarrow")
        ml_frame = dataset[(dataset["label_valid_h1"] == True) & (dataset["warmup_row"] == False)].copy()  # noqa: E712
        slices = {split: ml_frame[ml_frame["split"] == split].copy() for split in ROBUSTNESS_SPLITS_V8_0}
        train = slices["train"]
        shuffled_train_target = pd.Series(rng.permutation(train[TARGET_NAME_V8_0].astype(str).to_numpy()), index=train.index)
        predict_frame = pd.concat([slices[split] for split in EVALUATION_SPLITS_V8_0], axis=0)
        for model_name in ROBUSTNESS_MODELS_V8_0:
            result = fit_predict_model(
                model_name,
                train[ALLOWED_FEATURE_COLUMNS_V8_0],
                shuffled_train_target,
                predict_frame[ALLOWED_FEATURE_COLUMNS_V8_0],
            )
            for split in EVALUATION_SPLITS_V8_0:
                split_frame = slices[split]
                y_true = split_frame[TARGET_NAME_V8_0].astype(str)
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
                    "random_seed": LABEL_SHUFFLE_RANDOM_SEED_V8_0,
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


def scan_ohlcv_trades_feature_leakage_v8_0(feature_columns: list[str]) -> dict[str, Any]:
    exact_terms = {term.casefold() for term in FORBIDDEN_ROBUSTNESS_FEATURE_EXACT_V8_0}
    prefix_terms = tuple(term.casefold() for term in FORBIDDEN_ROBUSTNESS_FEATURE_PREFIXES_V8_0)
    forbidden: list[str] = []
    for column in feature_columns:
        folded = str(column).casefold()
        if folded in exact_terms or folded.startswith(prefix_terms):
            forbidden.append(str(column))
    return {
        "feature_columns_checked": list(feature_columns),
        "forbidden_feature_columns_present": forbidden,
        "feature_leakage_detected": bool(forbidden),
    }


def scan_ohlcv_trades_metric_forbidden_terms_v8_0(payload: Any) -> dict[str, Any]:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True).casefold()
    present = [term for term in FORBIDDEN_ROBUSTNESS_METRIC_TERMS_V8_0 if term in text]
    return {
        "forbidden_terms": FORBIDDEN_ROBUSTNESS_METRIC_TERMS_V8_0,
        "forbidden_terms_present": present,
        "metric_forbidden_terms_detected": bool(present),
    }


def build_ohlcv_trades_ml_robustness_markdown_v8_0(manifest: dict[str, Any]) -> str:
    findings = manifest["findings"]
    warning_count = len(findings["warnings"])
    lines = [
        "# Audit robustesse, walk-forward et falsification - V8.0",
        "",
        "## Objectif",
        "",
        "V8.0 audite les resultats ML offline V8.0 avec des analyses descriptives et falsifiables sur une fenetre preview de 90 jours.",
        "Cet audit ne transforme pas les scores en decision operationnelle.",
        "",
        "## Analyses",
        "",
        "- `baseline_delta` compare chaque modele aux baselines majority et random.",
        "- `split_stability` mesure les ecarts train / validation / test.",
        "- `timeframe_stability` compare les resultats entre 1m, 5m, 15m et 1h.",
        "- `walk_forward_stability` resume les metriques descriptives par groupe walk-forward.",
        "- `ohlcv_trades_90d_vs_references_comparison` compare descriptivement V8.0 OHLCV + trades a V7.4, V6.2 et V5.4 si les references sont disponibles.",
        "- `label_shuffle_falsification` entraine logistic regression et decision tree depth 2 avec labels train melanges, seed 123.",
        "- `feature_leakage_scan` verifie la liste de features V8.0.",
        "- `metric_forbidden_scan` verifie l'absence de metriques de trading interdites.",
        "",
        "## Findings",
        "",
        f"- Robust edge claimed : `{findings['robust_edge_claimed']}`.",
        f"- Validation de strategie declaree : `{findings['strategy_validated']}`.",
        f"- Backtest effectue : `{findings['backtest_performed']}`.",
        f"- Signal actionnable produit : `{findings['actionable_signal_produced']}`.",
        f"- OHLCV+trades valide pour trading : `{findings['ohlcv_trades_validated_for_trading']}`.",
        f"- Warnings : `{warning_count}`.",
        "",
        "## Limitations",
        "",
        *[f"- {item}" for item in manifest["limitations"]],
        "",
        "## Avertissements d'usage",
        "",
        "- V8.0 ne valide aucune strategie.",
        "- V8.0 ne valide aucun modele exploitable en trading.",
        "- V8.0 ne valide pas les features OHLCV+trades pour trading.",
        "- V8.0 ne produit aucun backtest.",
        "- V8.0 ne produit aucun signal de trading.",
        "- V8.0 ne produit aucun ordre.",
        "- V8.0 n'autorise aucun paper live.",
        "- V8.0 n'autorise aucun trading reel.",
        "- Les resultats sont descriptifs et falsifiables.",
        "- Les metriques walk-forward ne sont pas un backtest.",
        "- La fenetre de 90 jours est trop courte pour une conclusion robuste.",
        "- Les comparaisons avec V6.2/V5.4 sont non directement comparables si les fenetres different.",
        "- La comparaison OHLCV+trades vs references OHLCV est descriptive, non actionnable.",
        "- Toute interpretation doit rester prudente.",
    ]
    return "\n".join(lines) + "\n"


def _validate_inputs(root: Path) -> None:
    dataset_result = validate_ohlcv_trades_90d_offline_supervised_dataset_v7_9(root)
    if not dataset_result["passed"]:
        raise RuntimeError(f"V7.9 dataset validation failed before V8.0: {dataset_result['errors']}")
    ml_result = validate_ohlcv_trades_90d_offline_ml_research_v8_0(root)
    if not ml_result["passed"]:
        raise RuntimeError(f"V8.0 ML validation failed before V8.0: {ml_result['errors']}")


def _input_score_files(root: Path, ml_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    window = ml_manifest["input_dataset_manifest"]
    blocks: dict[str, dict[str, Any]] = {}
    for timeframe in TIMEFRAMES_V8_0:
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
        "macro_f1": float(f1_score(y_true, y_pred, labels=TARGET_CLASSES_V8_0, average="macro", zero_division=0)),
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
    warnings.extend(analyses["ohlcv_trades_90d_vs_references_comparison"].get("warnings", []))
    for key, value in analyses["label_shuffle_falsification"].items():
        if value["no_clear_edge_vs_shuffled_labels"]:
            warnings.append(f"no clear edge vs shuffled labels: {key}")
    return sorted(warnings)


def _robustness_run_id() -> str:
    return f"{ROBUSTNESS_RUN_ID_PREFIX_V8_0}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"


def _round_metric(value: float) -> float:
    return round(float(value), 12)


def _update_project_state(root: Path, manifest: dict[str, Any]) -> None:
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    state.update(
        {
            "last_validated_version": "V7.9",
            "candidate_version": "V8.0",
            "candidate_status": "pending_external_audit",
            "direction": "OHLCV + public trades 90-day ML offline and robustness",
            "ohlcv_trades_90d_robustness_window_start_v8_0": manifest["input_ml_manifest"]["window_start"],
            "ohlcv_trades_90d_robustness_window_end_v8_0": manifest["input_ml_manifest"]["window_end"],
            "ohlcv_trades_90d_robustness_days_v8_0": manifest["input_ml_manifest"]["total_days"],
            "feature_columns_count_v8_0": manifest["input_ml_manifest"]["feature_columns_count"],
            "backtest_v8_0_created": False,
            "strategy_v8_0_created": False,
            "signal_v8_0_created": False,
            "orders_v8_0_created": False,
            "paper_live_v8_0_created": False,
            "trading_v8_0_created": False,
            "persistent_model_v8_0_created": False,
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
    _write_text(root / "README.md", _readme_markdown(manifest))


def _latest_metrics_payload(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "last_validated_version": "V7.9",
        "candidate_version": "V8.0",
        "candidate_status": "pending_external_audit",
        "direction": "OHLCV + public trades 90-day ML offline and robustness",
        "input_window_start": manifest["input_ml_manifest"]["window_start"],
        "input_window_end": manifest["input_ml_manifest"]["window_end"],
        "input_total_days": manifest["input_ml_manifest"]["total_days"],
        "feature_columns_count": manifest["input_ml_manifest"]["feature_columns_count"],
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
    return f"""# Etat du Projet : V7.9 validee + candidat V8.0

- **Derniere version validee** : V7.9.
- **Version candidate** : V8.0.
- **Statut candidate** : `pending_external_audit`.
- **Direction** : OHLCV + public trades 90-day ML offline and robustness.

## Candidat V8.0

- Fenetre : `{manifest['input_ml_manifest']['window_start']}` -> `{manifest['input_ml_manifest']['window_end']}`.
- Nombre de jours : `{manifest['input_ml_manifest']['total_days']}`.
- Feature columns count : `{manifest['input_ml_manifest']['feature_columns_count']}`.
- Analyses : `{sorted(manifest['analyses'])}`.
- Warnings descriptifs : `{len(manifest['findings']['warnings'])}`.
- V8.0 reste candidate `pending_external_audit`.

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
- V8.0 reste non validee avant audit externe.
"""


def _latest_metrics_markdown(manifest: dict[str, Any]) -> str:
    return f"""# Latest Metrics V8.0

- Derniere version validee : V7.9.
- Candidate : V8.0.
- Statut : `pending_external_audit`.
- Direction : OHLCV + public trades 90-day ML offline and robustness.
- Fenetre : `{manifest['input_ml_manifest']['window_start']}` -> `{manifest['input_ml_manifest']['window_end']}`.
- Total jours : `{manifest['input_ml_manifest']['total_days']}`.
- Feature columns count : `{manifest['input_ml_manifest']['feature_columns_count']}`.
- Warnings descriptifs : `{len(manifest['findings']['warnings'])}`.

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun modele persistant et aucun trading reel.
"""


def _latest_summary_markdown(manifest: dict[str, Any]) -> str:
    return f"""# Latest Summary V8.0

V7.9 est la derniere version validee par audit externe.

V8.0 est la candidate courante. Elle audite uniquement la robustesse descriptive, les groupes walk-forward et la falsification par label shuffle des resultats ML offline V8.0.

Fenetre utilisee : `{manifest['input_ml_manifest']['window_start']}` -> `{manifest['input_ml_manifest']['window_end']}`.

Total jours : `{manifest['input_ml_manifest']['total_days']}`.

Feature columns count : `{manifest['input_ml_manifest']['feature_columns_count']}`.

Analyses produites : `{sorted(manifest['analyses'])}`.

Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucune strategie, aucun signal de trading, aucun modele persistant et aucun claim de rentabilite.

V8.0 reste `pending_external_audit`.
"""


def _readme_markdown(manifest: dict[str, Any]) -> str:
    return f"""# Projet Galapagos

- Derniere version validee : V7.9.
- Candidate : V8.0, OHLCV + public trades 90-day ML offline and robustness.

V8.0 entraine uniquement des baselines ML offline simples sur le dataset V7.9 OHLCV + aggTrades 90 jours, produit des scores de recherche `research_*`, puis audite la robustesse descriptive et la falsification par label shuffle.

Fenetre : `{manifest['input_ml_manifest']['window_start']}` -> `{manifest['input_ml_manifest']['window_end']}`, `{manifest['input_ml_manifest']['total_days']}` jours.

Feature columns ML : `{manifest['input_ml_manifest']['feature_columns_count']}`.

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live, aucun trading reel et aucun modele persistant.

## Commandes V8.0

```bash
python scripts/run_ohlcv_trades_90d_offline_ml_research_v8_0.py
python scripts/validate_ohlcv_trades_90d_offline_ml_research_v8_0.py
python scripts/run_ohlcv_trades_90d_ml_robustness_v8_0.py
python scripts/validate_ohlcv_trades_90d_ml_robustness_v8_0.py
```

V8.0 reste `pending_external_audit` avant validation externe.
"""


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
