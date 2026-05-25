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
from galapagos.datasets.ohlcv_trades_1y_window_validation import validate_ohlcv_trades_1y_offline_supervised_dataset_v8_4
from galapagos.datasets.schemas import MANIFEST_PATH_V8_4
from galapagos.ml.ohlcv_trades_1y_window import input_dataset_path, score_output_path
from galapagos.ml.ohlcv_trades_1y_window_validation import validate_ohlcv_trades_1y_offline_ml_research_v8_5
from galapagos.ml.offline_baselines import fit_predict_model
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V8_5 as ALLOWED_FEATURE_COLUMNS_V8_6,
    MANIFEST_PATH_V5_4,
    MANIFEST_PATH_V6_2,
    MANIFEST_PATH_V7_4,
    MANIFEST_PATH_V8_0 as REFERENCE_MANIFEST_PATH_V8_0,
    MANIFEST_PATH_V8_5 as ML_MANIFEST_PATH_V8_6,
    MODEL_NAMES_V8_5 as MODEL_NAMES_V8_6,
    REPORT_JSON_PATH_V5_4,
    REPORT_JSON_PATH_V6_2,
    REPORT_JSON_PATH_V8_5 as ML_REPORT_JSON_PATH_V8_6,
    SCORES_JSON_PATH_V5_4,
    SCORES_JSON_PATH_V6_2,
    SCORES_JSON_PATH_V8_5 as ML_SCORES_JSON_PATH_V8_6,
    TARGET_CLASSES_V8_5 as TARGET_CLASSES_V8_6,
    TARGET_NAME_V8_5 as TARGET_NAME_V8_6,
    TIMEFRAMES_V8_5 as TIMEFRAMES_V8_6,
)


VERSION_V8_6 = "V8.6"
ROBUSTNESS_RUN_ID_PREFIX_V8_6 = "v8_6"
ROBUSTNESS_MANIFEST_PATH_V8_6 = Path("reports/manifests/ohlcv_trades_1y_ml_robustness_v8_6_manifest.json")
ROBUSTNESS_REPORT_JSON_PATH_V8_6 = Path("reports/ml/ohlcv_trades_1y_ml_robustness_v8_6.json")
ROBUSTNESS_REPORT_MD_PATH_V8_6 = Path("reports/ml/ohlcv_trades_1y_ml_robustness_v8_6.md")
ROBUSTNESS_DOC_PATH_V8_6 = Path("docs/ohlcv_trades_1y_ml_robustness_v8_6.md")
DECISION_GATE_JSON_PATH_V8_6 = Path("reports/research_decisions/v8_6_research_decision_gate.json")
DECISION_GATE_MD_PATH_V8_6 = Path("reports/research_decisions/v8_6_research_decision_gate.md")
DECISION_GATE_DOC_PATH_V8_6 = Path("docs/research_decision_gate_v8_6.md")
MANIFEST_PATH_V8_6 = ROBUSTNESS_MANIFEST_PATH_V8_6
REPORT_JSON_PATH_V8_6 = ROBUSTNESS_REPORT_JSON_PATH_V8_6
REPORT_MD_PATH_V8_6 = ROBUSTNESS_REPORT_MD_PATH_V8_6
DOC_PATH_V8_6 = ROBUSTNESS_DOC_PATH_V8_6
ACCURACY_GAP_WARNING_THRESHOLD_V8_6 = 0.10
MACRO_F1_GAP_WARNING_THRESHOLD_V8_6 = 0.10
LABEL_SHUFFLE_RANDOM_SEED_V8_6 = 123
ROBUSTNESS_MODELS_V8_6 = ["logistic_regression", "decision_tree_depth_2"]
ROBUSTNESS_SPLITS_V8_6 = ["train", "validation", "test"]
EVALUATION_SPLITS_V8_6 = ["validation", "test"]
WALK_FORWARD_WEAK_ACCURACY_THRESHOLD_V8_6 = 0.34
WALK_FORWARD_WEAK_MACRO_F1_THRESHOLD_V8_6 = 0.20
FORBIDDEN_ROBUSTNESS_FEATURE_PREFIXES_V8_6 = [
    "future_",
    "label_",
    "direction_",
    "up_down_flat_",
]
FORBIDDEN_ROBUSTNESS_FEATURE_EXACT_V8_6 = [
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
FORBIDDEN_ROBUSTNESS_METRIC_TERMS_V8_6 = [
    "sharpe",
    "drawdown",
    "pnl",
    "equity_curve",
    "profit_factor",
    "trading_win_rate",
]
EXPECTED_LIMITATIONS_V8_6 = [
    "V8.6 audite uniquement la robustesse descriptive des baselines ML offline V8.5 sur la fenetre OHLCV + aggTrades d'environ 1 an.",
    "V8.6 compare descriptivement V8.5 a des references si disponibles, mais certaines fenetres peuvent differer.",
    "V8.6 ne produit aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.",
]
SAFETY_FLAGS_V8_6 = {
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
DECISION_GATE_SAFETY_V8_6 = {
    "trading_enabled": False,
    "paper_live_enabled": False,
    "orders_enabled": False,
    "backtest_enabled": False,
    "strategy_enabled": False,
    "execution_enabled": False,
}
DECISION_GATE_CLAIMS_V8_6 = {
    "strategy_validated": False,
    "model_validated_for_trading": False,
    "ohlcv_trades_validated_for_trading": False,
    "profitability_claimed": False,
    "real_trading_allowed": False,
}


def run_ohlcv_trades_1y_ml_robustness_v8_6(
    root: Path = Path("."),
    *,
    validate_inputs: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_inputs:
        _validate_inputs(root)

    dataset_manifest = _read_json(root / MANIFEST_PATH_V8_4)
    ml_manifest = _read_json(root / ML_MANIFEST_PATH_V8_6)
    ml_report = _read_json(root / ML_REPORT_JSON_PATH_V8_6)
    scores_report = _read_json(root / ML_SCORES_JSON_PATH_V8_6)
    window = ml_manifest["input_dataset_manifest"]
    metrics = ml_manifest["metrics"]
    walk_forward_metrics = ml_manifest["walk_forward_metrics"]
    reference_reports = build_reference_reports_v8_6(root)

    analyses: dict[str, Any] = {
        "baseline_delta": compute_ohlcv_trades_baseline_delta_v8_6(metrics),
        "split_stability": compute_ohlcv_trades_split_stability_v8_6(metrics),
        "timeframe_stability": compute_ohlcv_trades_timeframe_stability_v8_6(metrics),
        "walk_forward_stability": compute_ohlcv_trades_walk_forward_stability_v8_6(walk_forward_metrics),
        "ohlcv_trades_1y_vs_references_comparison": compute_ohlcv_trades_1y_vs_references_comparison_v8_6(root, metrics, walk_forward_metrics),
        "label_shuffle_falsification": compute_ohlcv_trades_label_shuffle_falsification_v8_6(root, ml_manifest),
        "feature_leakage_scan": scan_ohlcv_trades_feature_leakage_v8_6(ml_manifest["feature_columns"]),
    }
    analyses["metric_forbidden_scan"] = scan_ohlcv_trades_metric_forbidden_terms_v8_6(
        {
            "ml_manifest_metrics": ml_manifest.get("metrics", {}),
            "ml_manifest_walk_forward_metrics": ml_manifest.get("walk_forward_metrics", {}),
            "ml_report_metrics": ml_report.get("metrics", {}),
            "ml_report_walk_forward_metrics": ml_report.get("walk_forward_metrics", {}),
            "scores_report": scores_report,
            "v8_6_analyses": analyses,
        }
    )

    warnings = _collect_warnings(analyses)
    status = "PASS"
    if analyses["feature_leakage_scan"]["forbidden_feature_columns_present"]:
        status = "FAIL"
    if analyses["metric_forbidden_scan"]["forbidden_terms_present"]:
        status = "FAIL"

    manifest = {
        "version": VERSION_V8_6,
        "status": status,
        "created_at_utc": utc_now_iso(),
        "robustness_run_id": _robustness_run_id(),
        "input_dataset_manifest": {
            "path": MANIFEST_PATH_V8_4.as_posix(),
            "sha256": sha256_file(root / MANIFEST_PATH_V8_4),
            "window_start": window["window_start"],
            "window_end": window["window_end"],
            "total_days": int(window["total_days"]),
            "feature_columns_count": int(dataset_manifest["feature_columns_count"]),
        },
        "input_ml_manifest": {
            "path": ML_MANIFEST_PATH_V8_6.as_posix(),
            "sha256": sha256_file(root / ML_MANIFEST_PATH_V8_6),
            "window_start": window["window_start"],
            "window_end": window["window_end"],
            "total_days": int(window["total_days"]),
            "feature_columns_count": int(ml_manifest["feature_columns_count"]),
        },
        "input_score_files": _input_score_files(root, ml_manifest),
        "reference_reports": reference_reports,
        "analyses": analyses,
        "thresholds": {
            "accuracy_gap_warning_threshold": ACCURACY_GAP_WARNING_THRESHOLD_V8_6,
            "macro_f1_gap_warning_threshold": MACRO_F1_GAP_WARNING_THRESHOLD_V8_6,
            "random_seed": LABEL_SHUFFLE_RANDOM_SEED_V8_6,
        },
        "findings": {
            "robust_edge_claimed": False,
            "strategy_validated": False,
            "backtest_performed": False,
            "actionable_signal_produced": False,
            "ohlcv_trades_validated_for_trading": False,
            "warnings": warnings,
        },
        "safety": SAFETY_FLAGS_V8_6,
        "limitations": EXPECTED_LIMITATIONS_V8_6,
    }
    _write_json(root / ROBUSTNESS_MANIFEST_PATH_V8_6, manifest)
    _write_json(root / ROBUSTNESS_REPORT_JSON_PATH_V8_6, manifest)
    markdown = build_ohlcv_trades_ml_robustness_markdown_v8_6(manifest)
    _write_text(root / ROBUSTNESS_REPORT_MD_PATH_V8_6, markdown)
    _write_text(root / ROBUSTNESS_DOC_PATH_V8_6, markdown)
    _update_project_state(root, manifest)
    return manifest


def compute_ohlcv_trades_baseline_delta_v8_6(metrics: dict[str, Any]) -> dict[str, Any]:
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


def compute_ohlcv_trades_split_stability_v8_6(metrics: dict[str, Any]) -> dict[str, Any]:
    stability: dict[str, Any] = {}
    models = sorted({metric["model_name"] for metric in metrics.values()})
    timeframes = sorted({metric["timeframe"] for metric in metrics.values()}, key=TIMEFRAMES_V8_6.index)
    for timeframe in timeframes:
        for model_name in models:
            split_metrics = {split: metrics.get(f"{timeframe}.{model_name}.{split}") for split in ROBUSTNESS_SPLITS_V8_6}
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
                train_validation_accuracy_gap > ACCURACY_GAP_WARNING_THRESHOLD_V8_6
                or train_validation_macro_f1_gap > MACRO_F1_GAP_WARNING_THRESHOLD_V8_6
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


def compute_ohlcv_trades_timeframe_stability_v8_6(metrics: dict[str, Any]) -> dict[str, Any]:
    stability: dict[str, Any] = {}
    models = sorted({metric["model_name"] for metric in metrics.values()})
    for model_name in models:
        test_metrics = {
            timeframe: metrics[f"{timeframe}.{model_name}.test"]
            for timeframe in TIMEFRAMES_V8_6
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
            "single_timeframe_concentration_warning": bool(sorted_accuracy[0][1] - second_accuracy > ACCURACY_GAP_WARNING_THRESHOLD_V8_6),
        }
    return stability


def compute_ohlcv_trades_walk_forward_stability_v8_6(walk_forward_metrics: dict[str, Any]) -> dict[str, Any]:
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
            if accuracy_by_group[group] < WALK_FORWARD_WEAK_ACCURACY_THRESHOLD_V8_6
            or macro_f1_by_group[group] < WALK_FORWARD_WEAK_MACRO_F1_THRESHOLD_V8_6
        ]
        unstable_groups = [
            group
            for group in accuracy_by_group
            if abs(accuracy_by_group[group] - mean_accuracy) > ACCURACY_GAP_WARNING_THRESHOLD_V8_6
            or abs(macro_f1_by_group[group] - mean_macro_f1) > MACRO_F1_GAP_WARNING_THRESHOLD_V8_6
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


def build_reference_reports_v8_6(root: Path) -> dict[str, Any]:
    warnings: list[str] = []
    v8_0_available = (root / REFERENCE_MANIFEST_PATH_V8_0).exists()
    v7_4_available = (root / MANIFEST_PATH_V7_4).exists()
    v6_2_available = (root / MANIFEST_PATH_V6_2).exists()
    v5_4_available = (root / MANIFEST_PATH_V5_4).exists()
    if not v8_0_available:
        warnings.append("V8.0 OHLCV+trades 90-day reference manifest is unavailable; comparison is skipped.")
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
    if v8_0_available or v7_4_available or v6_2_available or v5_4_available:
        warnings.append("not directly comparable due to different window length/source set")
    return {
        "v8_0_available": bool(v8_0_available),
        "v8_0_manifest_path": REFERENCE_MANIFEST_PATH_V8_0.as_posix(),
        "v8_0_manifest_sha256": sha256_file(root / REFERENCE_MANIFEST_PATH_V8_0) if v8_0_available else None,
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


def compute_ohlcv_trades_1y_vs_references_comparison_v8_6(
    root: Path,
    ohlcv_trades_metrics: dict[str, Any],
    ohlcv_trades_walk_forward_metrics: dict[str, Any],
) -> dict[str, Any]:
    references = {
        "ohlcv_trades_90d_v8_0": {
            "manifest_path": REFERENCE_MANIFEST_PATH_V8_0,
            "reference_label": "V8.0 OHLCV+trades 90 jours",
        },
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
        compared[reference_name] = _compare_single_reference_v8_6(
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


def _compare_single_reference_v8_6(
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


def compute_ohlcv_trades_label_shuffle_falsification_v8_6(root: Path, ml_manifest: dict[str, Any]) -> dict[str, Any]:
    root = root.resolve()
    original_metrics = ml_manifest["metrics"]
    dataset_manifest = _read_json(root / MANIFEST_PATH_V8_4)
    falsification: dict[str, Any] = {}
    needed_columns = [
        *ALLOWED_FEATURE_COLUMNS_V8_6,
        TARGET_NAME_V8_6,
        "label_valid_h1",
        "warmup_row",
        "split",
    ]
    for timeframe in TIMEFRAMES_V8_6:
        rng = np.random.default_rng(LABEL_SHUFFLE_RANDOM_SEED_V8_6)
        dataset_path = input_dataset_path(root, timeframe, dataset_manifest)
        dataset = pd.read_parquet(dataset_path, columns=needed_columns, engine="pyarrow")
        ml_frame = dataset[(dataset["label_valid_h1"] == True) & (dataset["warmup_row"] == False)].copy()  # noqa: E712
        slices = {split: ml_frame[ml_frame["split"] == split].copy() for split in ROBUSTNESS_SPLITS_V8_6}
        train = slices["train"]
        shuffled_train_target = pd.Series(rng.permutation(train[TARGET_NAME_V8_6].astype(str).to_numpy()), index=train.index)
        predict_frame = pd.concat([slices[split] for split in EVALUATION_SPLITS_V8_6], axis=0)
        for model_name in ROBUSTNESS_MODELS_V8_6:
            result = fit_predict_model(
                model_name,
                train[ALLOWED_FEATURE_COLUMNS_V8_6],
                shuffled_train_target,
                predict_frame[ALLOWED_FEATURE_COLUMNS_V8_6],
            )
            for split in EVALUATION_SPLITS_V8_6:
                split_frame = slices[split]
                y_true = split_frame[TARGET_NAME_V8_6].astype(str)
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
                    "random_seed": LABEL_SHUFFLE_RANDOM_SEED_V8_6,
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


def scan_ohlcv_trades_feature_leakage_v8_6(feature_columns: list[str]) -> dict[str, Any]:
    exact_terms = {term.casefold() for term in FORBIDDEN_ROBUSTNESS_FEATURE_EXACT_V8_6}
    prefix_terms = tuple(term.casefold() for term in FORBIDDEN_ROBUSTNESS_FEATURE_PREFIXES_V8_6)
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


def scan_ohlcv_trades_metric_forbidden_terms_v8_6(payload: Any) -> dict[str, Any]:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True).casefold()
    present = [term for term in FORBIDDEN_ROBUSTNESS_METRIC_TERMS_V8_6 if term in text]
    return {
        "forbidden_terms": FORBIDDEN_ROBUSTNESS_METRIC_TERMS_V8_6,
        "forbidden_terms_present": present,
        "metric_forbidden_terms_detected": bool(present),
    }


def build_ohlcv_trades_ml_robustness_markdown_v8_6(manifest: dict[str, Any]) -> str:
    findings = manifest["findings"]
    warning_count = len(findings["warnings"])
    lines = [
        "# Audit robustesse, walk-forward et falsification - V8.6",
        "",
        "## Objectif",
        "",
        "V8.6 audite les resultats ML offline V8.6 avec des analyses descriptives et falsifiables sur une fenetre preview de 1 an.",
        "Cet audit ne transforme pas les scores en decision operationnelle.",
        "",
        "## Analyses",
        "",
        "- `baseline_delta` compare chaque modele aux baselines majority et random.",
        "- `split_stability` mesure les ecarts train / validation / test.",
        "- `timeframe_stability` compare les resultats entre 1m, 5m, 15m et 1h.",
        "- `walk_forward_stability` resume les metriques descriptives par groupe walk-forward.",
        "- `ohlcv_trades_1y_vs_references_comparison` compare descriptivement V8.6 OHLCV + trades a V7.4, V6.2 et V5.4 si les references sont disponibles.",
        "- `label_shuffle_falsification` entraine logistic regression et decision tree depth 2 avec labels train melanges, seed 123.",
        "- `feature_leakage_scan` verifie la liste de features V8.6.",
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
        "- V8.6 ne valide aucune strategie.",
        "- V8.6 ne valide aucun modele exploitable en trading.",
        "- V8.6 ne valide pas les features OHLCV+trades pour trading.",
        "- V8.6 ne produit aucun backtest.",
        "- V8.6 ne produit aucun signal de trading.",
        "- V8.6 ne produit aucun ordre.",
        "- V8.6 n'autorise aucun paper live.",
        "- V8.6 n'autorise aucun trading reel.",
        "- Les resultats sont descriptifs et falsifiables.",
        "- Les metriques walk-forward ne sont pas un backtest.",
        "- La fenetre de 1 an est trop courte pour une conclusion robuste.",
        "- Les comparaisons avec V6.2/V5.4 sont non directement comparables si les fenetres different.",
        "- La comparaison OHLCV+trades vs references OHLCV est descriptive, non actionnable.",
        "- Toute interpretation doit rester prudente.",
    ]
    return "\n".join(lines) + "\n"


def _validate_inputs(root: Path) -> None:
    dataset_result = validate_ohlcv_trades_1y_offline_supervised_dataset_v8_4(root)
    if not dataset_result["passed"]:
        raise RuntimeError(f"V8.4 dataset validation failed before V8.6: {dataset_result['errors']}")
    ml_result = validate_ohlcv_trades_1y_offline_ml_research_v8_5(root)
    if not ml_result["passed"]:
        raise RuntimeError(f"V8.5 ML validation failed before V8.6: {ml_result['errors']}")


def _input_score_files(root: Path, ml_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    window = ml_manifest["input_dataset_manifest"]
    blocks: dict[str, dict[str, Any]] = {}
    for timeframe in TIMEFRAMES_V8_6:
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
        "macro_f1": float(f1_score(y_true, y_pred, labels=TARGET_CLASSES_V8_6, average="macro", zero_division=0)),
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
    warnings.extend(analyses["ohlcv_trades_1y_vs_references_comparison"].get("warnings", []))
    for key, value in analyses["label_shuffle_falsification"].items():
        if value["no_clear_edge_vs_shuffled_labels"]:
            warnings.append(f"no clear edge vs shuffled labels: {key}")
    return sorted(warnings)


def _robustness_run_id() -> str:
    return f"{ROBUSTNESS_RUN_ID_PREFIX_V8_6}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"


def _round_metric(value: float) -> float:
    return round(float(value), 12)


def _update_project_state(root: Path, manifest: dict[str, Any]) -> None:
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    state.update(
        {
            "last_validated_version": "V8.5",
            "candidate_version": "V8.6",
            "candidate_status": "pending_external_audit",
            "direction": "OHLCV + public trades 1-year robustness and research decision gate",
            "ohlcv_trades_1y_robustness_window_start_v8_6": manifest["input_ml_manifest"]["window_start"],
            "ohlcv_trades_1y_robustness_window_end_v8_6": manifest["input_ml_manifest"]["window_end"],
            "ohlcv_trades_1y_robustness_days_v8_6": manifest["input_ml_manifest"]["total_days"],
            "feature_columns_count_v8_6": manifest["input_ml_manifest"]["feature_columns_count"],
            "backtest_v8_6_created": False,
            "strategy_v8_6_created": False,
            "signal_v8_6_created": False,
            "orders_v8_6_created": False,
            "paper_live_v8_6_created": False,
            "trading_v8_6_created": False,
            "persistent_model_v8_6_created": False,
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
        "last_validated_version": "V8.5",
        "candidate_version": "V8.6",
        "candidate_status": "pending_external_audit",
        "direction": "OHLCV + public trades 1-year robustness and research decision gate",
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
    return f"""# Etat du Projet : V8.5 validee + candidat V8.6

- **Derniere version validee** : V8.5.
- **Version candidate** : V8.6.
- **Statut candidate** : `pending_external_audit`.
- **Direction** : OHLCV + public trades 1-year robustness and research decision gate.

## Candidat V8.6

- Fenetre : `{manifest['input_ml_manifest']['window_start']}` -> `{manifest['input_ml_manifest']['window_end']}`.
- Nombre de jours : `{manifest['input_ml_manifest']['total_days']}`.
- Feature columns count : `{manifest['input_ml_manifest']['feature_columns_count']}`.
- Analyses : `{sorted(manifest['analyses'])}`.
- Warnings descriptifs : `{len(manifest['findings']['warnings'])}`.
- V8.6 reste candidate `pending_external_audit`.

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
- V8.6 reste non validee avant audit externe.
"""


def _latest_metrics_markdown(manifest: dict[str, Any]) -> str:
    return f"""# Latest Metrics V8.6

- Derniere version validee : V8.5.
- Candidate : V8.6.
- Statut : `pending_external_audit`.
- Direction : OHLCV + public trades 1-year robustness and research decision gate.
- Fenetre : `{manifest['input_ml_manifest']['window_start']}` -> `{manifest['input_ml_manifest']['window_end']}`.
- Total jours : `{manifest['input_ml_manifest']['total_days']}`.
- Feature columns count : `{manifest['input_ml_manifest']['feature_columns_count']}`.
- Warnings descriptifs : `{len(manifest['findings']['warnings'])}`.

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun modele persistant et aucun trading reel.
"""


def _latest_summary_markdown(manifest: dict[str, Any]) -> str:
    return f"""# Latest Summary V8.6

V8.5 est la derniere version validee par audit externe.

V8.6 est la candidate courante. Elle audite uniquement la robustesse descriptive, les groupes walk-forward et la falsification par label shuffle des resultats ML offline V8.5.

Fenetre utilisee : `{manifest['input_ml_manifest']['window_start']}` -> `{manifest['input_ml_manifest']['window_end']}`.

Total jours : `{manifest['input_ml_manifest']['total_days']}`.

Feature columns count : `{manifest['input_ml_manifest']['feature_columns_count']}`.

Analyses produites : `{sorted(manifest['analyses'])}`.

Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucune strategie, aucun signal de trading, aucun modele persistant et aucun claim de rentabilite.

V8.6 reste `pending_external_audit`.
"""


def _readme_markdown(manifest: dict[str, Any]) -> str:
    return f"""# Projet Galapagos

- Derniere version validee : V8.5.
- Candidate : V8.6, OHLCV + public trades 1-year robustness and research decision gate.

V8.6 audite uniquement les scores ML offline V8.5, la robustesse descriptive, les groupes walk-forward et la falsification par label shuffle.

Fenetre : `{manifest['input_ml_manifest']['window_start']}` -> `{manifest['input_ml_manifest']['window_end']}`, `{manifest['input_ml_manifest']['total_days']}` jours.

Feature columns ML : `{manifest['input_ml_manifest']['feature_columns_count']}`.

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live, aucun trading reel et aucun modele persistant.

## Commandes V8.6

```bash
python scripts/run_ohlcv_trades_1y_ml_robustness_v8_6.py
python scripts/validate_ohlcv_trades_1y_ml_robustness_v8_6.py
python scripts/run_research_decision_gate_v8_6.py
python scripts/validate_research_decision_gate_v8_6.py
```

V8.6 reste `pending_external_audit` avant validation externe.
"""


def run_research_decision_gate_v8_6(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    robustness_manifest = _read_json(root / ROBUSTNESS_MANIFEST_PATH_V8_6)
    analyses = robustness_manifest["analyses"]
    findings = robustness_manifest["findings"]
    baseline_assessment = _build_baseline_assessment(analyses["baseline_delta"])
    split_assessment = _build_split_stability_assessment(analyses["split_stability"])
    timeframe_assessment = _build_timeframe_stability_assessment(analyses["timeframe_stability"])
    walk_forward_assessment = _build_walk_forward_assessment(analyses["walk_forward_stability"])
    label_shuffle_assessment = _build_label_shuffle_assessment(analyses["label_shuffle_falsification"])
    leakage_assessment = _build_leakage_assessment(analyses)
    comparison_assessment = _build_comparison_assessment(analyses["ohlcv_trades_1y_vs_references_comparison"])

    backtest_allowed = (
        baseline_assessment["learned_models_clear_above_baselines"] is True
        and split_assessment["stable_enough_for_backtest_research"] is True
        and timeframe_assessment["stable_across_timeframes"] is True
        and walk_forward_assessment["stable_across_walk_forward_groups"] is True
        and label_shuffle_assessment["falsification_clean"] is True
        and leakage_assessment["leakage_detected"] is False
    )
    if backtest_allowed:
        recommended = "E. Preparer un backtest research tres borne."
        secondary = "D. Preparer une validation walk-forward offline plus stricte."
        verdict = "interessant_mais_recherche_uniquement"
    else:
        recommended = "D. Preparer une validation walk-forward offline plus stricte."
        secondary = "B. Ameliorer/refactoriser les features OHLCV + trades."
        verdict = "interessant_mais_mitige_non_concluant"

    decision = {
        "version": VERSION_V8_6,
        "status": "PASS",
        "decision_gate_type": "research_only",
        "created_at_utc": utc_now_iso(),
        "inputs": {
            "robustness_manifest": {
                "path": ROBUSTNESS_MANIFEST_PATH_V8_6.as_posix(),
                "sha256": sha256_file(root / ROBUSTNESS_MANIFEST_PATH_V8_6),
            },
            "robustness_report": {
                "path": ROBUSTNESS_REPORT_JSON_PATH_V8_6.as_posix(),
                "sha256": sha256_file(root / ROBUSTNESS_REPORT_JSON_PATH_V8_6),
            },
            "ml_manifest": robustness_manifest["input_ml_manifest"],
            "dataset_manifest": robustness_manifest["input_dataset_manifest"],
        },
        "summary_verdict": verdict,
        "ohlcv_trades_1y_assessment": {
            "assessment": verdict,
            "window_start": robustness_manifest["input_ml_manifest"]["window_start"],
            "window_end": robustness_manifest["input_ml_manifest"]["window_end"],
            "total_days": robustness_manifest["input_ml_manifest"]["total_days"],
            "feature_columns_count": robustness_manifest["input_ml_manifest"]["feature_columns_count"],
            "interesting_signal": baseline_assessment["learned_models_positive_cases"] > 0,
            "backtest_recommended": False,
            "warnings_count": len(findings["warnings"]),
            "interpretation": "Les resultats V8.5/V8.6 restent descriptifs, utiles pour orienter la recherche, mais non suffisants pour transformer la piste en strategie.",
        },
        "comparison_to_references_assessment": comparison_assessment,
        "baseline_assessment": baseline_assessment,
        "split_stability_assessment": split_assessment,
        "timeframe_stability_assessment": timeframe_assessment,
        "walk_forward_stability_assessment": walk_forward_assessment,
        "label_shuffle_assessment": label_shuffle_assessment,
        "leakage_assessment": leakage_assessment,
        "limitations": [
            "La fenetre d'environ 1 an reste limitee et ne couvre pas tous les regimes de marche disponibles dans V5.0.",
            "Les comparaisons avec V8.0/V7.4/V6.2/V5.4 sont descriptives et souvent non directement comparables.",
            "Aucune metrique de trading interdite ou mesure d'execution n'est calculee.",
            "Les resultats ne doivent pas etre transformes en strategie ou en signal de trading.",
        ],
        "recommended_next_step": recommended,
        "secondary_next_step": secondary,
        "roadmap": [
            "V8.7 - Walk-forward offline stricte OHLCV + trades 1 an",
            "V8.8 - Diagnostics labels et raffinement features OHLCV + trades",
            "V8.9 - Dataset raffine OHLCV + trades",
            "V9.0 - ML offline raffine et falsification",
            "V9.1 - Research decision gate avant toute consideration de backtest",
        ],
        "safety": DECISION_GATE_SAFETY_V8_6,
        "claims": DECISION_GATE_CLAIMS_V8_6,
    }
    _write_json(root / DECISION_GATE_JSON_PATH_V8_6, decision)
    markdown = build_research_decision_gate_markdown_v8_6(decision)
    _write_text(root / DECISION_GATE_MD_PATH_V8_6, markdown)
    _write_text(root / DECISION_GATE_DOC_PATH_V8_6, markdown)
    _update_project_state_for_decision(root, decision)
    return decision


def _build_baseline_assessment(baseline_delta: dict[str, Any]) -> dict[str, Any]:
    learned = [
        payload
        for payload in baseline_delta.values()
        if payload.get("model_name") in {"logistic_regression", "decision_tree_depth_2"} and payload.get("split") in {"validation", "test"}
    ]
    positive = [
        payload
        for payload in learned
        if payload.get("delta_vs_majority_macro_f1", 0.0) > 0.0 and payload.get("delta_vs_random_macro_f1", 0.0) > 0.0
    ]
    clear = [
        payload
        for payload in learned
        if payload.get("delta_vs_majority_macro_f1", 0.0) > 0.02 and payload.get("delta_vs_random_macro_f1", 0.0) > 0.02
    ]
    return {
        "learned_models_checked": len(learned),
        "learned_models_positive_cases": len(positive),
        "learned_models_clear_cases": len(clear),
        "learned_models_clear_above_baselines": bool(learned and len(clear) >= max(1, len(learned) // 2)),
        "verdict": "mitige" if positive else "faible",
        "research_only": True,
    }


def _build_split_stability_assessment(split_stability: dict[str, Any]) -> dict[str, Any]:
    warnings = [key for key, value in split_stability.items() if value.get("overfit_warning") is True]
    return {
        "groups_checked": len(split_stability),
        "overfit_warning_count": len(warnings),
        "overfit_warning_groups": warnings,
        "stable_enough_for_backtest_research": len(warnings) == 0,
        "verdict": "instable" if warnings else "stable_descriptif",
    }


def _build_timeframe_stability_assessment(timeframe_stability: dict[str, Any]) -> dict[str, Any]:
    warnings = [key for key, value in timeframe_stability.items() if value.get("single_timeframe_concentration_warning") is True]
    return {
        "models_checked": len(timeframe_stability),
        "timeframe_concentration_warning_count": len(warnings),
        "timeframe_concentration_warning_models": warnings,
        "stable_across_timeframes": len(warnings) == 0,
        "verdict": "concentration_possible" if warnings else "stable_descriptif",
    }


def _build_walk_forward_assessment(walk_forward_stability: dict[str, Any]) -> dict[str, Any]:
    unstable = {key: value.get("unstable_groups", []) for key, value in walk_forward_stability.items() if value.get("unstable_groups")}
    weak = {key: value.get("weak_groups", []) for key, value in walk_forward_stability.items() if value.get("weak_groups")}
    concentrated = [key for key, value in walk_forward_stability.items() if value.get("concentrated_on_few_groups_warning") is True]
    return {
        "groups_checked": len(walk_forward_stability),
        "weak_groups_by_model": weak,
        "unstable_groups_by_model": unstable,
        "concentration_warning_groups": concentrated,
        "stable_across_walk_forward_groups": not unstable and not concentrated,
        "descriptive_not_backtest": True,
        "verdict": "instable_ou_concentre" if unstable or concentrated else "stable_descriptif",
    }


def _build_label_shuffle_assessment(label_shuffle: dict[str, Any]) -> dict[str, Any]:
    no_clear_edge = [key for key, value in label_shuffle.items() if value.get("no_clear_edge_vs_shuffled_labels") is True]
    return {
        "shuffle_seed": LABEL_SHUFFLE_RANDOM_SEED_V8_6,
        "shuffle_scope": "train_labels_only",
        "cases_checked": len(label_shuffle),
        "no_clear_edge_vs_shuffled_labels_count": len(no_clear_edge),
        "no_clear_edge_vs_shuffled_labels_cases": no_clear_edge,
        "falsification_clean": len(no_clear_edge) == 0,
        "verdict": "alerte_si_proche_shuffle" if no_clear_edge else "falsification_propre_descriptive",
    }


def _build_leakage_assessment(analyses: dict[str, Any]) -> dict[str, Any]:
    feature_scan = analyses["feature_leakage_scan"]
    metric_scan = analyses["metric_forbidden_scan"]
    leakage_detected = bool(feature_scan["forbidden_feature_columns_present"] or metric_scan["forbidden_terms_present"])
    return {
        "feature_leakage_detected": feature_scan["feature_leakage_detected"],
        "forbidden_feature_columns_present": feature_scan["forbidden_feature_columns_present"],
        "metric_forbidden_terms_detected": metric_scan["metric_forbidden_terms_detected"],
        "forbidden_metric_terms_present": metric_scan["forbidden_terms_present"],
        "leakage_detected": leakage_detected,
        "verdict": "pass" if not leakage_detected else "fail",
    }


def _build_comparison_assessment(comparison: dict[str, Any]) -> dict[str, Any]:
    return {
        "available_references": comparison["available_references"],
        "compared_metrics": comparison["compared_metrics"],
        "descriptive_only": comparison["descriptive_only"],
        "not_directly_comparable": comparison["not_directly_comparable"],
        "warnings": comparison["warnings"],
        "verdict": "comparaison_descriptive_non_directe",
    }


def build_research_decision_gate_markdown_v8_6(decision: dict[str, Any]) -> str:
    assessment = decision["ohlcv_trades_1y_assessment"]
    lines = [
        "# Research decision gate V8.6",
        "",
        "## Executive summary",
        "",
        f"- Verdict research : `{decision['summary_verdict']}`.",
        "- V8.6 ne produit aucune conclusion trading.",
        "- OHLCV + aggTrades 1 an reste interessant pour la recherche, mais les resultats doivent rester prudents et descriptifs.",
        f"- Recommandation principale : {decision['recommended_next_step']}",
        f"- Recommandation secondaire : {decision['secondary_next_step']}",
        "",
        "## Entrees analysees",
        "",
        "- V8.4 : dataset supervise offline OHLCV + aggTrades 1 an.",
        "- V8.5 : scores ML offline `research_*` et metriques descriptives.",
        f"- Fenetre : `{assessment['window_start']}` -> `{assessment['window_end']}`.",
        f"- Total jours : `{assessment['total_days']}`.",
        f"- Feature columns count : `{assessment['feature_columns_count']}`.",
        "- Target : `up_down_flat_h1`.",
        "- Modeles : majority_class_baseline, random_seeded_baseline, logistic_regression, decision_tree_depth_2.",
        "",
        "## Comparaison aux references",
        "",
        "- Les comparaisons avec V8.0, V7.4, V6.2 et V5.4 sont descriptives.",
        "- Les fenetres et sources peuvent differer : elles ne sont pas directement comparables.",
        "- Aucune superiorite trading n'est conclue.",
        "",
        "## Baselines",
        "",
        f"- Cas appris positifs vs baselines : `{decision['baseline_assessment']['learned_models_positive_cases']}`.",
        f"- Verdict : `{decision['baseline_assessment']['verdict']}`.",
        "",
        "## Stabilite train / validation / test",
        "",
        f"- Warnings overfit : `{decision['split_stability_assessment']['overfit_warning_count']}`.",
        f"- Verdict : `{decision['split_stability_assessment']['verdict']}`.",
        "",
        "## Stabilite par timeframe",
        "",
        f"- Warnings concentration timeframe : `{decision['timeframe_stability_assessment']['timeframe_concentration_warning_count']}`.",
        f"- Verdict : `{decision['timeframe_stability_assessment']['verdict']}`.",
        "",
        "## Stabilite walk-forward",
        "",
        "- Les metriques walk-forward sont descriptives et ne constituent pas un backtest.",
        f"- Verdict : `{decision['walk_forward_stability_assessment']['verdict']}`.",
        "",
        "## Label shuffle falsification",
        "",
        f"- Seed : `{decision['label_shuffle_assessment']['shuffle_seed']}`.",
        f"- Cas sans edge clair vs labels melanges : `{decision['label_shuffle_assessment']['no_clear_edge_vs_shuffled_labels_count']}`.",
        f"- Verdict : `{decision['label_shuffle_assessment']['verdict']}`.",
        "",
        "## Fuites / anti-leakage",
        "",
        f"- Feature leakage detectee : `{decision['leakage_assessment']['feature_leakage_detected']}`.",
        f"- Metriques interdites detectees : `{decision['leakage_assessment']['metric_forbidden_terms_detected']}`.",
        "",
        "## Limites",
        "",
        *[f"- {item}" for item in decision["limitations"]],
        "",
        "## Roadmap proposee",
        "",
        *[f"- {item}" for item in decision["roadmap"]],
        "",
        "## Interdits maintenus",
        "",
        "- Pas de trading.",
        "- Pas de paper live.",
        "- Pas d'ordre.",
        "- Pas de backtest validant une strategie.",
        "- Pas de strategie.",
        "- Pas de signal de trading.",
        "- Pas de modele persistant.",
        "- Pas de claim de rentabilite.",
    ]
    return "\n".join(lines) + "\n"


def _update_project_state_for_decision(root: Path, decision: dict[str, Any]) -> None:
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    assessment = decision["ohlcv_trades_1y_assessment"]
    state.update(
        {
            "last_validated_version": "V8.5",
            "candidate_version": "V8.6",
            "candidate_status": "pending_external_audit",
            "direction": "OHLCV + public trades 1-year robustness and research decision gate",
            "research_decision_gate_v8_6_created": True,
            "research_decision_gate_v8_6_status": "PASS",
            "research_decision_gate_v8_6_verdict": decision["summary_verdict"],
            "research_decision_gate_v8_6_recommended_next_step": decision["recommended_next_step"],
            "research_decision_gate_v8_6_secondary_next_step": decision["secondary_next_step"],
            "research_decision_gate_v8_6_window_start": assessment["window_start"],
            "research_decision_gate_v8_6_window_end": assessment["window_end"],
            "research_decision_gate_v8_6_days": assessment["total_days"],
            "feature_columns_count_v8_6": assessment["feature_columns_count"],
            "backtest_v8_6_created": False,
            "strategy_v8_6_created": False,
            "signal_v8_6_created": False,
            "orders_v8_6_created": False,
            "paper_live_v8_6_created": False,
            "trading_v8_6_created": False,
            "persistent_model_v8_6_created": False,
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
    _write_json(root / "reports/current/latest_metrics.json", _decision_latest_metrics(decision))
    _write_text(root / "reports/PROJECT_STATE.md", _decision_project_state_markdown(decision))
    _write_text(root / "reports/current/latest_metrics.md", _decision_latest_metrics_markdown(decision))
    _write_text(root / "reports/current/latest_summary.md", _decision_latest_summary_markdown(decision))
    _write_text(root / "README.md", _decision_readme_markdown(decision))


def _decision_latest_metrics(decision: dict[str, Any]) -> dict[str, Any]:
    assessment = decision["ohlcv_trades_1y_assessment"]
    return {
        "last_validated_version": "V8.5",
        "candidate_version": "V8.6",
        "candidate_status": "pending_external_audit",
        "direction": "OHLCV + public trades 1-year robustness and research decision gate",
        "input_window_start": assessment["window_start"],
        "input_window_end": assessment["window_end"],
        "input_total_days": assessment["total_days"],
        "feature_columns_count": assessment["feature_columns_count"],
        "summary_verdict": decision["summary_verdict"],
        "recommended_next_step": decision["recommended_next_step"],
        "secondary_next_step": decision["secondary_next_step"],
        "backtest_recommended": False,
        "trading_enabled": False,
        "paper_live_enabled": False,
        "orders_enabled": False,
        "backtest_enabled": False,
        "strategy_enabled": False,
        "execution_enabled": False,
        "api_key_used": False,
        "private_endpoint_used": False,
        "authentication_used": False,
        "external_validation_required": True,
    }


def _decision_project_state_markdown(decision: dict[str, Any]) -> str:
    assessment = decision["ohlcv_trades_1y_assessment"]
    return f"""# Etat du Projet : V8.5 validee + candidat V8.6

- **Derniere version validee** : V8.5.
- **Version candidate** : V8.6.
- **Statut candidate** : `pending_external_audit`.
- **Direction** : OHLCV + public trades 1-year robustness and research decision gate.
- **Verdict research** : `{decision['summary_verdict']}`.
- **Recommandation principale** : {decision['recommended_next_step']}
- **Recommandation secondaire** : {decision['secondary_next_step']}

## Candidat V8.6

- Fenetre : `{assessment['window_start']}` -> `{assessment['window_end']}`.
- Total jours : `{assessment['total_days']}`.
- Feature columns count : `{assessment['feature_columns_count']}`.
- V8.6 reste candidate `pending_external_audit`.

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
- V8.6 reste non validee avant audit externe.
"""


def _decision_latest_metrics_markdown(decision: dict[str, Any]) -> str:
    assessment = decision["ohlcv_trades_1y_assessment"]
    return f"""# Latest Metrics V8.6

- Derniere version validee : V8.5.
- Candidate : V8.6.
- Statut : `pending_external_audit`.
- Direction : OHLCV + public trades 1-year robustness and research decision gate.
- Fenetre : `{assessment['window_start']}` -> `{assessment['window_end']}`.
- Total jours : `{assessment['total_days']}`.
- Feature columns count : `{assessment['feature_columns_count']}`.
- Verdict research : `{decision['summary_verdict']}`.
- Recommandation principale : {decision['recommended_next_step']}
- Recommandation secondaire : {decision['secondary_next_step']}

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun modele persistant et aucun trading reel.
"""


def _decision_latest_summary_markdown(decision: dict[str, Any]) -> str:
    assessment = decision["ohlcv_trades_1y_assessment"]
    return f"""# Latest Summary V8.6

V8.5 est la derniere version validee par audit externe.

V8.6 est la candidate courante. Elle audite la robustesse descriptive et la falsification des resultats ML offline V8.5, puis produit une decision gate research.

Fenetre utilisee : `{assessment['window_start']}` -> `{assessment['window_end']}`.

Total jours : `{assessment['total_days']}`.

Feature columns count : `{assessment['feature_columns_count']}`.

Verdict research : `{decision['summary_verdict']}`.

Recommandation principale : {decision['recommended_next_step']}

Recommandation secondaire : {decision['secondary_next_step']}

Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucune strategie, aucun signal de trading, aucun modele persistant et aucun claim de rentabilite.

V8.6 reste `pending_external_audit`.
"""


def _decision_readme_markdown(decision: dict[str, Any]) -> str:
    assessment = decision["ohlcv_trades_1y_assessment"]
    return f"""# Projet Galapagos

- Derniere version validee : V8.5.
- Candidate : V8.6, OHLCV + public trades 1-year robustness and research decision gate.

V8.6 audite uniquement les resultats ML offline V8.5, produit des diagnostics de robustesse/falsification et une decision gate research. Elle ne produit aucun backtest, aucune strategie et aucun signal de trading.

Fenetre : `{assessment['window_start']}` -> `{assessment['window_end']}`, `{assessment['total_days']}` jours.

Feature columns ML : `{assessment['feature_columns_count']}`.

Verdict research : `{decision['summary_verdict']}`.

Recommandation principale : {decision['recommended_next_step']}

Recommandation secondaire : {decision['secondary_next_step']}

## Commandes V8.6

```bash
python scripts/run_ohlcv_trades_1y_ml_robustness_v8_6.py
python scripts/validate_ohlcv_trades_1y_ml_robustness_v8_6.py
python scripts/run_research_decision_gate_v8_6.py
python scripts/validate_research_decision_gate_v8_6.py
python -m pytest -q tests/ml/test_ohlcv_trades_1y_ml_robustness_v8_6.py
python -m pytest -q tests/validation/test_ohlcv_trades_1y_ml_robustness_v8_6_validator.py
python -m pytest -q tests/validation/test_research_decision_gate_v8_6.py
python scripts/release_audit_lite_zip_v8_6.py
python scripts/audit_audit_lite_zip_v8_6.py --zip projet-galapagos-v8.6-audit-lite.zip
python scripts/smoke_audit_lite_zip_v8_6.py --zip projet-galapagos-v8.6-audit-lite.zip
python -m pytest --collect-only -q
```

V8.6 reste `pending_external_audit` avant validation externe.
"""


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
