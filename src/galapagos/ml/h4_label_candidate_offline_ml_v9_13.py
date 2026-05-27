from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.datasets.h4_label_candidate_dataset_v9_13_schemas import (
    MANIFEST_PATH_DATASET_V9_13,
    ML_FEATURE_COLUMNS_V9_13,
    TARGET_NAME_V9_13,
    TIMEFRAMES_V9_13,
    WINDOW_END_V9_13,
    WINDOW_START_V9_13,
    get_h4_candidate_dataset_path_v9_13,
    get_h4_candidate_split_path_v9_13,
)
from galapagos.ml.h4_label_candidate_offline_ml_v9_13_metrics import (
    compute_h4_classification_metrics_v9_13,
    compute_h4_walk_forward_descriptive_metrics_v9_13,
)
from galapagos.ml.h4_label_candidate_offline_ml_v9_13_quality import assess_h4_ml_quality_v9_13
from galapagos.ml.offline_baselines import fit_predict_model


VERSION_V9_13_ML = "V9.13"
ML_SCHEMA_VERSION_V9_13 = "H4_LABEL_CANDIDATE_ML_SCORE_COLUMNS_V9_13"
MODEL_NAMES_V9_13 = ["majority_class_baseline", "random_seeded_baseline", "logistic_regression", "decision_tree_depth_2"]
TARGET_CLASSES_V9_13 = ["DOWN", "FLAT", "UP"]
ML_SCORE_COLUMNS_V9_13 = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "timeframe",
    "event_ts",
    "close_ts",
    "decision_ts",
    "split",
    "walk_forward_group",
    "ml_run_id",
    "model_name",
    "target_name",
    "dataset_path",
    "feature_columns_fingerprint",
    "ml_schema_version",
    "target_value",
    "research_predicted_class",
    "research_probability_down",
    "research_probability_flat",
    "research_probability_up",
    "prediction_available_ts",
    "row_valid_for_ml",
    "ml_null_count",
    "ml_error_count",
]
FORBIDDEN_FEATURE_TERMS_V9_13 = ["future_", "label_", "direction_", "up_down_flat_", "target", "split", "walk_forward_group", "prediction", "signal", "trading_signal", "order", "pnl", "backtest", "strategy", "event_based_label"]
FORBIDDEN_METRIC_TERMS_V9_13 = ["pnl", "sharpe", "drawdown", "equity_curve", "profit_factor"]
MANIFEST_PATH_ML_V9_13 = Path("reports/manifests/h4_label_candidate_offline_ml_v9_13_manifest.json")
REPORT_JSON_PATH_ML_V9_13 = Path("reports/ml/h4_label_candidate_offline_ml_v9_13.json")
REPORT_MD_PATH_ML_V9_13 = Path("reports/ml/h4_label_candidate_offline_ml_v9_13.md")
SCORES_JSON_PATH_ML_V9_13 = Path("reports/ml/h4_label_candidate_offline_scores_v9_13.json")
SCORES_MD_PATH_ML_V9_13 = Path("reports/ml/h4_label_candidate_offline_scores_v9_13.md")
DOC_PATH_ML_V9_13 = Path("docs/h4_label_candidate_offline_ml_v9_13.md")
V9_8_REPORT_PATH = Path("reports/ml/refined_volnorm_labels_offline_ml_v9_8.json")

SAFETY_FLAGS_ML_V9_13 = {
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
    "persistent_model_created": False,
    "sidecars_created": False,
    "zip_fingerprints_created": False,
}
FINDINGS_V9_13 = {
    "robust_edge_claimed": False,
    "strategy_validated": False,
    "backtest_performed": False,
    "actionable_signal_produced": False,
    "walk_forward_validated_for_trading": False,
    "trading_allowed": False,
    "paper_live_allowed": False,
    "real_trading_allowed": False,
}
EXPECTED_LIMITATIONS_ML_V9_13 = [
    "V9.13 entraine uniquement des modeles ML offline simples pour diagnostiquer le label h4.",
    "V9.13 ne produit aucun modele persistant, aucun walk-forward, aucun backtest, aucune strategie, aucun signal actionnable et aucun ordre.",
]


def run_h4_label_candidate_offline_ml_v9_13(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    dataset_manifest = _read_json(root / MANIFEST_PATH_DATASET_V9_13)
    if dataset_manifest.get("status") != "PASS":
        report = stop_ml_report_v9_13("h4_offline_ml_not_ready_dataset_issue")
        _write_outputs(root, report)
        return report
    ml_run_id = f"v9_13_ml_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    outputs: dict[str, dict[str, Any]] = {}
    input_datasets: dict[str, dict[str, Any]] = {}
    input_splits: dict[str, dict[str, Any]] = {}
    quality: dict[str, Any] = {}
    metrics: dict[str, Any] = {}
    wf_descriptive: dict[str, Any] = {}
    label_shuffle: dict[str, Any] = {}
    status = "PASS"
    for timeframe in TIMEFRAMES_V9_13:
        dataset_path = get_h4_candidate_dataset_path_v9_13(root, timeframe)
        split_path = get_h4_candidate_split_path_v9_13(root, timeframe)
        dataset = read_parquet(dataset_path)
        scores = build_h4_model_scores_v9_13(dataset, dataset_path=dataset_path.relative_to(root).as_posix(), ml_run_id=ml_run_id)
        score_path = get_h4_ml_score_path_v9_13(root, timeframe)
        write_parquet(scores, score_path)
        outputs[timeframe] = output_block_v9_13(root, score_path, len(scores))
        input_datasets[timeframe] = input_block_v9_13(root, dataset_path, len(dataset))
        input_splits[timeframe] = input_block_v9_13(root, split_path, len(read_parquet(split_path)))
        quality[timeframe] = assess_h4_ml_quality_v9_13(dataset, scores, timeframe)
        if quality[timeframe]["errors"]:
            status = "FAIL"
        metrics.update(compute_h4_classification_metrics_v9_13(scores))
        wf_descriptive.update(compute_h4_walk_forward_descriptive_metrics_v9_13(scores))
        label_shuffle.update(compute_label_shuffle_falsification_v9_13(dataset, scores))
    baseline_comparison = baseline_comparison_v9_13(metrics)
    comparison_v9_8 = compare_to_v9_8_v9_13(root, metrics, label_shuffle, baseline_comparison)
    ml_decision = decide_ml_v9_13(status, baseline_comparison, label_shuffle)
    global_decision = decide_global_v9_13(ml_decision, comparison_v9_8)
    report = {
        "version": VERSION_V9_13_ML,
        "status": status,
        "created_at_utc": utc_now_iso_v9_13(),
        "ml_run_id": ml_run_id,
        "decision": ml_decision,
        "global_decision": global_decision,
        "input_dataset_manifest": {"path": MANIFEST_PATH_DATASET_V9_13.as_posix(), "window_start": WINDOW_START_V9_13, "window_end": WINDOW_END_V9_13, "total_days": 366},
        "input_datasets": input_datasets,
        "input_splits": input_splits,
        "outputs": outputs,
        "target_name": TARGET_NAME_V9_13,
        "feature_columns": ML_FEATURE_COLUMNS_V9_13,
        "feature_columns_count": len(ML_FEATURE_COLUMNS_V9_13),
        "models": MODEL_NAMES_V9_13,
        "metrics": metrics,
        "walk_forward_group_descriptive_metrics": wf_descriptive,
        "baseline_comparison": baseline_comparison,
        "label_shuffle_falsification": label_shuffle,
        "comparison_with_v9_8": comparison_v9_8,
        "quality": quality,
        "feature_leakage_scan": feature_leakage_scan_v9_13(ML_FEATURE_COLUMNS_V9_13),
        "metric_forbidden_scan": metric_forbidden_scan_v9_13({"metrics": metrics, "baseline_comparison": baseline_comparison, "label_shuffle_falsification": label_shuffle}),
        "findings": dict(FINDINGS_V9_13),
        "safety": dict(SAFETY_FLAGS_ML_V9_13),
        "limitations": EXPECTED_LIMITATIONS_ML_V9_13,
    }
    _write_outputs(root, report)
    return report


def prepare_h4_ml_frame_v9_13(dataset: pd.DataFrame) -> pd.DataFrame:
    return dataset[(dataset["label_valid"] == True) & (dataset["warmup_row"] == False)].reset_index(drop=True).copy()  # noqa: E712


def build_h4_model_scores_v9_13(dataset: pd.DataFrame, *, dataset_path: str, ml_run_id: str) -> pd.DataFrame:
    ml_frame = prepare_h4_ml_frame_v9_13(dataset)
    if ml_frame.empty:
        return pd.DataFrame(columns=ML_SCORE_COLUMNS_V9_13)
    train = ml_frame[ml_frame["split"] == "train"]
    score_frames: list[pd.DataFrame] = []
    feature_fingerprint = feature_columns_fingerprint_v9_13()
    for model_name in MODEL_NAMES_V9_13:
        result = fit_predict_model(model_name, train[ML_FEATURE_COLUMNS_V9_13], train[TARGET_NAME_V9_13].astype(str), ml_frame[ML_FEATURE_COLUMNS_V9_13])
        scores = ml_frame[["source", "venue", "market_type", "symbol", "timeframe", "event_ts", "close_ts", "decision_ts", "split", "walk_forward_group"]].copy()
        scores["ml_run_id"] = ml_run_id
        scores["model_name"] = model_name
        scores["target_name"] = TARGET_NAME_V9_13
        scores["dataset_path"] = dataset_path
        scores["feature_columns_fingerprint"] = feature_fingerprint
        scores["ml_schema_version"] = ML_SCHEMA_VERSION_V9_13
        scores["target_value"] = ml_frame[TARGET_NAME_V9_13].astype(str).to_numpy()
        scores["research_predicted_class"] = result.predicted_class.to_numpy()
        scores["research_probability_down"] = result.probabilities["DOWN"].to_numpy()
        scores["research_probability_flat"] = result.probabilities["FLAT"].to_numpy()
        scores["research_probability_up"] = result.probabilities["UP"].to_numpy()
        scores["prediction_available_ts"] = ml_frame["decision_ts"].to_numpy()
        scores["row_valid_for_ml"] = True
        scores["ml_null_count"] = scores.isna().sum(axis=1).astype(int)
        scores["ml_error_count"] = 0
        score_frames.append(scores[ML_SCORE_COLUMNS_V9_13])
    return pd.concat(score_frames, ignore_index=True)


def compute_label_shuffle_falsification_v9_13(dataset: pd.DataFrame, scores: pd.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {}
    ml_frame = prepare_h4_ml_frame_v9_13(dataset)
    train = ml_frame[ml_frame["split"] == "train"]
    evaluation = ml_frame[ml_frame["split"].isin(["validation", "test"])]
    if train.empty or evaluation.empty:
        return result
    shuffled_target = train[TARGET_NAME_V9_13].sample(frac=1.0, random_state=123).reset_index(drop=True)
    for model_name in ["logistic_regression", "decision_tree_depth_2"]:
        shuffled = fit_predict_model(model_name, train[ML_FEATURE_COLUMNS_V9_13], shuffled_target.astype(str), evaluation[ML_FEATURE_COLUMNS_V9_13])
        for split, split_frame in evaluation.groupby("split", sort=True):
            original = scores[(scores["model_name"] == model_name) & (scores["split"] == split)]
            original_acc = float((original["target_value"].astype(str).to_numpy() == original["research_predicted_class"].astype(str).to_numpy()).mean())
            mask = evaluation["split"].eq(split).to_numpy()
            shuffled_pred = shuffled.predicted_class.to_numpy()[mask]
            true = split_frame[TARGET_NAME_V9_13].astype(str).to_numpy()
            shuffled_acc = float((true == shuffled_pred).mean())
            result[f"{str(dataset['timeframe'].iloc[0])}.{model_name}.{split}"] = {
                "timeframe": str(dataset["timeframe"].iloc[0]),
                "model_name": model_name,
                "split": split,
                "original_accuracy": original_acc,
                "shuffled_accuracy": shuffled_acc,
                "delta_original_vs_shuffled": original_acc - shuffled_acc,
                "no_clear_edge_vs_shuffled_labels": (original_acc - shuffled_acc) < 0.02,
                "random_seed": 123,
            }
    return result


def baseline_comparison_v9_13(metrics: dict[str, Any]) -> dict[str, Any]:
    comparisons: dict[str, Any] = {}
    for key, item in metrics.items():
        if item["model_name"] not in {"logistic_regression", "decision_tree_depth_2"} or item["split"] not in {"validation", "test"}:
            continue
        baselines = [
            metric
            for metric in metrics.values()
            if metric["timeframe"] == item["timeframe"] and metric["split"] == item["split"] and metric["model_name"] in {"majority_class_baseline", "random_seeded_baseline"}
        ]
        best_macro = max((metric["macro_f1"] for metric in baselines), default=0.0)
        best_accuracy = max((metric["accuracy"] for metric in baselines), default=0.0)
        comparisons[key] = {
            "timeframe": item["timeframe"],
            "model_name": item["model_name"],
            "split": item["split"],
            "macro_f1": item["macro_f1"],
            "accuracy": item["accuracy"],
            "delta_macro_f1_vs_best_baseline": item["macro_f1"] - best_macro,
            "delta_accuracy_vs_best_baseline": item["accuracy"] - best_accuracy,
            "clear_win_vs_baseline": (item["macro_f1"] - best_macro) > 0.02,
        }
    return {
        "comparisons": comparisons,
        "clear_wins_count": int(sum(1 for item in comparisons.values() if item["clear_win_vs_baseline"])),
        "mean_delta_macro_f1_vs_best_baseline": float(sum(item["delta_macro_f1_vs_best_baseline"] for item in comparisons.values()) / max(len(comparisons), 1)),
    }


def compare_to_v9_8_v9_13(root: Path, metrics: dict[str, Any], label_shuffle: dict[str, Any], baseline_comparison: dict[str, Any]) -> dict[str, Any]:
    v9_8 = _read_json(root / V9_8_REPORT_PATH) if (root / V9_8_REPORT_PATH).exists() else {}
    v9_8_shuffle = v9_8.get("label_shuffle_falsification", {})
    v9_8_no_clear = int(sum(1 for item in v9_8_shuffle.values() if item.get("no_clear_edge_vs_shuffled_labels")))
    v9_13_no_clear = int(sum(1 for item in label_shuffle.values() if item.get("no_clear_edge_vs_shuffled_labels")))
    v9_8_mean_delta = _mean([item.get("delta_original_vs_shuffled", 0.0) for item in v9_8_shuffle.values()])
    v9_13_mean_delta = _mean([item.get("delta_original_vs_shuffled", 0.0) for item in label_shuffle.values()])
    v9_8_decision = v9_8.get("decision")
    return {
        "v9_8_decision": v9_8_decision,
        "v9_8_no_clear_edge_vs_shuffled_labels_count": v9_8_no_clear,
        "v9_13_no_clear_edge_vs_shuffled_labels_count": v9_13_no_clear,
        "no_clear_count_delta_v9_13_minus_v9_8": v9_13_no_clear - v9_8_no_clear,
        "v9_8_mean_delta_original_vs_shuffled": v9_8_mean_delta,
        "v9_13_mean_delta_original_vs_shuffled": v9_13_mean_delta,
        "distance_to_shuffled_improved_vs_v9_8": v9_13_mean_delta > v9_8_mean_delta and v9_13_no_clear <= v9_8_no_clear,
        "baseline_clear_wins_count_v9_13": baseline_comparison["clear_wins_count"],
        "interpretation": "Comparaison descriptive offline uniquement; V9.13 ne lance pas de walk-forward ni de backtest.",
    }


def decide_ml_v9_13(status: str, baseline_comparison: dict[str, Any], label_shuffle: dict[str, Any]) -> str:
    if status != "PASS":
        return "stop_h4_candidate_ml_failed"
    no_clear = [item for item in label_shuffle.values() if item.get("no_clear_edge_vs_shuffled_labels")]
    if no_clear:
        return "h4_offline_ml_completed_but_close_to_shuffled_labels"
    if baseline_comparison["clear_wins_count"] < 2:
        return "h4_offline_ml_completed_but_weak_vs_baselines"
    return "h4_offline_ml_diagnostic_completed"


def decide_global_v9_13(ml_decision: str, comparison_v9_8: dict[str, Any]) -> dict[str, Any]:
    if ml_decision == "h4_offline_ml_diagnostic_completed" and comparison_v9_8.get("distance_to_shuffled_improved_vs_v9_8"):
        decision = "h4_candidate_ready_for_strict_walk_forward_diagnostic"
        recommendation = "V9.14 - strict walk-forward diagnostic du label h4, si audit externe V9.13 valide."
    elif ml_decision == "h4_offline_ml_completed_but_close_to_shuffled_labels":
        decision = "h4_candidate_not_ready_refine_labels_again"
        recommendation = "Ne pas lancer automatiquement V9.14; analyser les cas proches des labels melanges et raffiner encore le label."
    else:
        decision = "h4_candidate_not_ready_feature_first"
        recommendation = "Prioriser un diagnostic features/labels avant walk-forward."
    return {
        "decision": decision,
        "recommendation": recommendation,
        "conservative_gate": True,
        "no_walk_forward_executed": True,
        "no_backtest_executed": True,
    }


def feature_leakage_scan_v9_13(columns: list[str]) -> dict[str, Any]:
    forbidden = [column for column in columns if any(term in column.casefold() for term in FORBIDDEN_FEATURE_TERMS_V9_13)]
    return {"passed": not forbidden, "forbidden_feature_columns_present": forbidden}


def metric_forbidden_scan_v9_13(payload: Any) -> dict[str, Any]:
    found: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if str(key).casefold() in FORBIDDEN_METRIC_TERMS_V9_13:
                    found.append(str(key))
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)
    return {"passed": not found, "forbidden_terms_present": sorted(set(found))}


def build_markdown_v9_13(report: dict[str, Any]) -> str:
    lines = [
        "# V9.13 - H4 label candidate offline ML diagnostic",
        "",
        "V9.13 entraine des baselines ML offline simples pour diagnostiquer le label h4. Les scores sont descriptifs, non actionnables et sans backtest.",
        "",
        f"- Decision ML : `{report['decision']}`.",
        f"- Decision globale : `{report['global_decision']['decision']}`.",
        f"- Target : `{report['target_name']}`.",
        f"- Features : `{report['feature_columns_count']}`.",
        "",
        "## Comparaison V9.8",
        f"- V9.8 no-clear shuffle : `{report['comparison_with_v9_8']['v9_8_no_clear_edge_vs_shuffled_labels_count']}`.",
        f"- V9.13 no-clear shuffle : `{report['comparison_with_v9_8']['v9_13_no_clear_edge_vs_shuffled_labels_count']}`.",
        f"- Distance shuffled amelioree : `{report['comparison_with_v9_8']['distance_to_shuffled_improved_vs_v9_8']}`.",
        "",
        "## Outputs",
    ]
    for timeframe, output in report["outputs"].items():
        lines.append(f"- `{timeframe}` : `{output['path']}` ({output['rows']} lignes).")
    lines.extend(["", "## Interdits maintenus", "- Aucun backtest.", "- Aucune strategie.", "- Aucun signal actionnable.", "- Aucun ordre.", "- Aucun modele persistant.", "- Aucun trading reel."])
    return "\n".join(lines) + "\n"


def get_h4_ml_score_path_v9_13(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v9_13/ml/h4_label_candidate"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_START_V9_13}_{WINDOW_END_V9_13}"
        / "ml-scores.parquet"
    )


def feature_columns_fingerprint_v9_13() -> str:
    payload = json.dumps(ML_FEATURE_COLUMNS_V9_13, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def input_block_v9_13(root: Path, path: Path, rows: int) -> dict[str, Any]:
    return {"path": path.relative_to(root).as_posix(), "rows": int(rows), "bytes": path.stat().st_size}


def output_block_v9_13(root: Path, path: Path, rows: int) -> dict[str, Any]:
    return {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "rows": int(rows), "format": "parquet"}


def stop_ml_report_v9_13(decision: str) -> dict[str, Any]:
    return {
        "version": VERSION_V9_13_ML,
        "status": "FAIL",
        "created_at_utc": utc_now_iso_v9_13(),
        "decision": decision,
        "findings": dict(FINDINGS_V9_13),
        "safety": dict(SAFETY_FLAGS_ML_V9_13),
        "limitations": EXPECTED_LIMITATIONS_ML_V9_13,
    }


def _write_outputs(root: Path, report: dict[str, Any]) -> None:
    _write_json(root / MANIFEST_PATH_ML_V9_13, report)
    _write_json(root / REPORT_JSON_PATH_ML_V9_13, report)
    _write_json(
        root / SCORES_JSON_PATH_ML_V9_13,
        {
            "version": VERSION_V9_13_ML,
            "ml_run_id": report.get("ml_run_id"),
            "outputs": report.get("outputs", {}),
            "metrics": report.get("metrics", {}),
            "baseline_comparison": report.get("baseline_comparison", {}),
            "label_shuffle_falsification": report.get("label_shuffle_falsification", {}),
            "comparison_with_v9_8": report.get("comparison_with_v9_8", {}),
        },
    )
    markdown = build_markdown_v9_13(report)
    for path in [REPORT_MD_PATH_ML_V9_13, SCORES_MD_PATH_ML_V9_13, DOC_PATH_ML_V9_13]:
        _write_text(root / path, markdown)


def _mean(values: list[float]) -> float:
    return float(sum(values) / max(len(values), 1))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def utc_now_iso_v9_13() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
