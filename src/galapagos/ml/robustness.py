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
from galapagos.datasets.schemas import MANIFEST_PATH_V3_2, get_dataset_v3_2_path
from galapagos.ml.offline_baselines import fit_predict_model
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V3_3,
    MANIFEST_PATH_V3_3,
    MODEL_NAMES_V3_3,
    TARGET_CLASSES_V3_3,
    TARGET_NAME_V3_3,
    TIMEFRAMES_V3_3,
    get_multi_day_ml_score_path_v3_3,
)


VERSION_V3_4 = "V3.4"
ROBUSTNESS_RUN_ID_PREFIX_V3_4 = "v3_4"
MANIFEST_PATH_V3_4 = Path("reports/manifests/multi_day_ml_robustness_v3_4_manifest.json")
REPORT_JSON_PATH_V3_4 = Path("reports/ml/multi_day_ml_robustness_v3_4.json")
REPORT_MD_PATH_V3_4 = Path("reports/ml/multi_day_ml_robustness_v3_4.md")
DOC_PATH_V3_4 = Path("docs/multi_day_ml_robustness_v3_4.md")
ACCURACY_GAP_WARNING_THRESHOLD_V3_4 = 0.10
MACRO_F1_GAP_WARNING_THRESHOLD_V3_4 = 0.10
LABEL_SHUFFLE_RANDOM_SEED_V3_4 = 123
ROBUSTNESS_MODELS_V3_4 = ["logistic_regression", "decision_tree_depth_2"]
ROBUSTNESS_SPLITS_V3_4 = ["train", "validation", "test"]
EVALUATION_SPLITS_V3_4 = ["validation", "test"]
FORBIDDEN_ROBUSTNESS_FEATURE_TERMS_V3_4 = [
    "future_",
    "label_",
    "direction_",
    "up_down_flat_",
    "target",
    "split",
    "signal",
    "order",
    "strategy",
    "pnl",
    "profit",
    "backtest",
]
FORBIDDEN_ROBUSTNESS_METRIC_TERMS_V3_4 = [
    "sharpe",
    "drawdown",
    "pnl",
    "equity_curve",
    "profit_factor",
    "trading_win_rate",
]
EXPECTED_LIMITATIONS_V3_4 = [
    "V3.4 audite uniquement la robustesse descriptive des baselines ML offline V3.3.",
    "V3.4 ne produit aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.",
]
SAFETY_FLAGS_V3_4 = {
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


def run_multi_day_ml_robustness_v3_4(
    root: Path = Path("."),
    *,
    validate_inputs: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_inputs:
        _validate_inputs(root)

    ml_manifest = _read_json(root / MANIFEST_PATH_V3_3)
    ml_report = _read_json(root / "reports/ml/multi_day_offline_ml_research_v3_3.json")
    scores_report = _read_json(root / "reports/ml/multi_day_offline_research_scores_v3_3.json")
    scores_by_timeframe = {timeframe: read_parquet(get_multi_day_ml_score_path_v3_3(root, timeframe)) for timeframe in TIMEFRAMES_V3_3}

    analyses = {
        "baseline_delta": compute_baseline_delta_v3_4(ml_manifest["metrics"]),
        "split_stability": compute_split_stability_v3_4(ml_manifest["metrics"]),
        "timeframe_stability": compute_timeframe_stability_v3_4(ml_manifest["metrics"]),
        "label_shuffle_falsification": compute_label_shuffle_falsification_v3_4(root, ml_manifest["metrics"]),
        "feature_leakage_scan": scan_feature_leakage_v3_4(ml_manifest["feature_columns"]),
        "metric_forbidden_scan": scan_metric_forbidden_terms_v3_4(
            {
                "ml_manifest_metrics": ml_manifest.get("metrics", {}),
                "ml_report_metrics": ml_report.get("metrics", {}),
                "scores_report_metrics": scores_report.get("metrics", {}),
            }
        ),
    }
    warnings = _collect_warnings(analyses)
    status = "PASS" if not analyses["feature_leakage_scan"]["forbidden_feature_columns_present"] and not analyses["metric_forbidden_scan"]["forbidden_terms_present"] else "FAIL"
    manifest = {
        "version": VERSION_V3_4,
        "status": status,
        "created_at_utc": utc_now_iso(),
        "robustness_run_id": _robustness_run_id(),
        "input_dataset_manifest": _path_sha_block(root, MANIFEST_PATH_V3_2),
        "input_ml_manifest": _path_sha_block(root, MANIFEST_PATH_V3_3),
        "input_score_files": _input_score_files(root, scores_by_timeframe),
        "analyses": analyses,
        "thresholds": {
            "accuracy_gap_warning_threshold": ACCURACY_GAP_WARNING_THRESHOLD_V3_4,
            "macro_f1_gap_warning_threshold": MACRO_F1_GAP_WARNING_THRESHOLD_V3_4,
            "random_seed": LABEL_SHUFFLE_RANDOM_SEED_V3_4,
        },
        "findings": {
            "robust_edge_claimed": False,
            "strategy_validated": False,
            "backtest_performed": False,
            "actionable_signal_produced": False,
            "warnings": warnings,
        },
        "safety": SAFETY_FLAGS_V3_4,
        "limitations": EXPECTED_LIMITATIONS_V3_4,
    }
    _write_json(root / MANIFEST_PATH_V3_4, manifest)
    _write_json(root / REPORT_JSON_PATH_V3_4, manifest)
    markdown = build_multi_day_ml_robustness_markdown_v3_4(manifest)
    _write_text(root / REPORT_MD_PATH_V3_4, markdown)
    _write_text(root / DOC_PATH_V3_4, markdown)
    return manifest


def compute_baseline_delta_v3_4(metrics: dict[str, Any]) -> dict[str, Any]:
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
            "majority_class_baseline_macro_f1": float(majority["macro_f1"]),
            "random_seeded_baseline_accuracy": float(random["accuracy"]),
            "random_seeded_baseline_macro_f1": float(random["macro_f1"]),
            "delta_vs_majority_accuracy": _round_metric(metric["accuracy"] - majority["accuracy"]),
            "delta_vs_majority_macro_f1": _round_metric(metric["macro_f1"] - majority["macro_f1"]),
            "delta_vs_random_accuracy": _round_metric(metric["accuracy"] - random["accuracy"]),
            "delta_vs_random_macro_f1": _round_metric(metric["macro_f1"] - random["macro_f1"]),
        }
    return baseline_delta


def compute_split_stability_v3_4(metrics: dict[str, Any]) -> dict[str, Any]:
    stability: dict[str, Any] = {}
    models = sorted({metric["model_name"] for metric in metrics.values()})
    timeframes = sorted({metric["timeframe"] for metric in metrics.values()}, key=TIMEFRAMES_V3_3.index)
    for timeframe in timeframes:
        for model_name in models:
            split_metrics = {split: metrics.get(f"{timeframe}.{model_name}.{split}") for split in ROBUSTNESS_SPLITS_V3_4}
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
                train_validation_accuracy_gap > ACCURACY_GAP_WARNING_THRESHOLD_V3_4
                or train_validation_macro_f1_gap > MACRO_F1_GAP_WARNING_THRESHOLD_V3_4
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


def compute_timeframe_stability_v3_4(metrics: dict[str, Any]) -> dict[str, Any]:
    stability: dict[str, Any] = {}
    models = sorted({metric["model_name"] for metric in metrics.values()})
    for model_name in models:
        test_metrics = {
            timeframe: metrics[f"{timeframe}.{model_name}.test"]
            for timeframe in TIMEFRAMES_V3_3
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
            "single_timeframe_concentration_warning": bool(sorted_accuracy[0][1] - second_accuracy > ACCURACY_GAP_WARNING_THRESHOLD_V3_4),
        }
    return stability


def compute_label_shuffle_falsification_v3_4(root: Path, original_metrics: dict[str, Any]) -> dict[str, Any]:
    root = root.resolve()
    falsification: dict[str, Any] = {}
    rng = np.random.default_rng(LABEL_SHUFFLE_RANDOM_SEED_V3_4)
    for timeframe in TIMEFRAMES_V3_3:
        dataset = read_parquet(get_dataset_v3_2_path(root, timeframe))
        ml_frame = dataset[(dataset["label_valid_h1"] == True) & (dataset["warmup_row"] == False)].copy()  # noqa: E712
        slices = {split: ml_frame[ml_frame["split"] == split].copy() for split in ROBUSTNESS_SPLITS_V3_4}
        train = slices["train"]
        shuffled_train_target = pd.Series(rng.permutation(train[TARGET_NAME_V3_3].astype(str).to_numpy()), index=train.index)
        for model_name in ROBUSTNESS_MODELS_V3_4:
            for split in EVALUATION_SPLITS_V3_4:
                split_frame = slices[split]
                result = fit_predict_model(
                    model_name,
                    train[ALLOWED_FEATURE_COLUMNS_V3_3],
                    shuffled_train_target,
                    split_frame[ALLOWED_FEATURE_COLUMNS_V3_3],
                )
                y_true = split_frame[TARGET_NAME_V3_3].astype(str)
                y_pred = result.predicted_class.astype(str)
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
                    "random_seed": LABEL_SHUFFLE_RANDOM_SEED_V3_4,
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


def scan_feature_leakage_v3_4(feature_columns: list[str]) -> dict[str, Any]:
    forbidden = [
        column
        for column in feature_columns
        if any(term in column.casefold() for term in FORBIDDEN_ROBUSTNESS_FEATURE_TERMS_V3_4)
    ]
    return {
        "feature_columns_checked": list(feature_columns),
        "forbidden_feature_columns_present": forbidden,
        "feature_leakage_detected": bool(forbidden),
    }


def scan_metric_forbidden_terms_v3_4(payload: Any) -> dict[str, Any]:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True).casefold()
    present = [term for term in FORBIDDEN_ROBUSTNESS_METRIC_TERMS_V3_4 if term in text]
    return {
        "forbidden_terms": FORBIDDEN_ROBUSTNESS_METRIC_TERMS_V3_4,
        "forbidden_terms_present": present,
        "metric_forbidden_terms_detected": bool(present),
    }


def build_multi_day_ml_robustness_markdown_v3_4(manifest: dict[str, Any]) -> str:
    findings = manifest["findings"]
    warning_count = len(findings["warnings"])
    lines = [
        "# Audit robustesse et falsification - V3.4",
        "",
        "## Objectif",
        "",
        "V3.4 audite les resultats ML offline V3.3 avec des analyses descriptives et falsifiables.",
        "Cet audit ne transforme pas les scores en decision operationnelle.",
        "",
        "## Analyses",
        "",
        "- `baseline_delta` compare chaque modele aux baselines majority et random.",
        "- `split_stability` mesure les ecarts train / validation / test.",
        "- `timeframe_stability` compare les resultats entre 1m, 5m, 15m et 1h.",
        "- `label_shuffle_falsification` entraine logistic regression et decision tree depth 2 avec labels train melanges, seed 123.",
        "- `feature_leakage_scan` verifie la liste de features V3.3.",
        "- `metric_forbidden_scan` verifie l'absence de metriques de trading interdites.",
        "",
        "## Findings",
        "",
        f"- robust_edge_claimed : `{findings['robust_edge_claimed']}`.",
        f"- validation de strategie declaree : `{findings['strategy_validated']}`.",
        f"- backtest_performed : `{findings['backtest_performed']}`.",
        f"- actionable_signal_produced : `{findings['actionable_signal_produced']}`.",
        f"- warnings : `{warning_count}`.",
        "",
        "## Limitations",
        "",
        *[f"- {item}" for item in manifest["limitations"]],
        "",
        "## Non-usage warnings",
        "",
        "- V3.4 ne valide aucune strategie.",
        "- V3.4 ne valide aucun modele exploitable en trading.",
        "- V3.4 ne produit aucun backtest.",
        "- V3.4 ne produit aucun signal de trading.",
        "- V3.4 ne produit aucun ordre.",
        "- V3.4 n'autorise aucun paper live.",
        "- V3.4 n'autorise aucun trading reel.",
        "- Les resultats sont descriptifs et falsifiables.",
        "- Toute interpretation doit rester prudente.",
    ]
    return "\n".join(lines) + "\n"


def _validate_inputs(root: Path) -> None:
    from galapagos.datasets.multi_day_validation import validate_multi_day_offline_supervised_dataset_v3_2
    from galapagos.ml.multi_day_validation import validate_multi_day_offline_ml_research_v3_3

    dataset_result = validate_multi_day_offline_supervised_dataset_v3_2(root)
    if not dataset_result["passed"]:
        raise RuntimeError(f"V3.2.1 dataset validation failed before V3.4: {dataset_result['errors']}")
    ml_result = validate_multi_day_offline_ml_research_v3_3(root)
    if not ml_result["passed"]:
        raise RuntimeError(f"V3.3.1 ML validation failed before V3.4: {ml_result['errors']}")


def _input_score_files(root: Path, scores_by_timeframe: dict[str, pd.DataFrame]) -> dict[str, dict[str, Any]]:
    blocks: dict[str, dict[str, Any]] = {}
    for timeframe, scores in scores_by_timeframe.items():
        path = get_multi_day_ml_score_path_v3_3(root, timeframe)
        blocks[timeframe] = {
            "path": str(path.relative_to(root)),
            "sha256": sha256_file(path),
            "rows": int(len(scores)),
        }
    return blocks


def _path_sha_block(root: Path, relative: Path) -> dict[str, str]:
    path = root / relative
    return {"path": relative.as_posix(), "sha256": sha256_file(path)}


def _classification_summary(y_true: pd.Series, y_pred: pd.Series) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=TARGET_CLASSES_V3_3, average="macro", zero_division=0)),
    }


def _collect_warnings(analyses: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for key, value in analyses["split_stability"].items():
        if value["overfit_warning"]:
            warnings.append(f"split stability warning: {key}")
    for key, value in analyses["timeframe_stability"].items():
        if value["single_timeframe_concentration_warning"]:
            warnings.append(f"timeframe concentration warning: {key}")
    for key, value in analyses["label_shuffle_falsification"].items():
        if value["no_clear_edge_vs_shuffled_labels"]:
            warnings.append(f"no clear edge vs shuffled labels: {key}")
    return sorted(warnings)


def _robustness_run_id() -> str:
    return f"{ROBUSTNESS_RUN_ID_PREFIX_V3_4}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"


def _round_metric(value: float) -> float:
    return round(float(value), 12)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
