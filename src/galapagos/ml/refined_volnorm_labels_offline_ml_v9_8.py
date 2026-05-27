from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.datasets.refined_volnorm_labels_dataset_v9_7_schemas import (
    FEATURE_COLUMNS_V9_7,
    MANIFEST_PATH_V9_7,
    TARGET_NAME_V9_7,
    TIMEFRAMES_V9_7,
    WINDOW_END_V9_7,
    WINDOW_START_V9_7,
    get_refined_volnorm_dataset_path_v9_7,
    get_refined_volnorm_split_path_v9_7,
)
from galapagos.ml.offline_baselines import fit_predict_model
from galapagos.ml.refined_volnorm_labels_offline_ml_v9_8_metrics import (
    compute_refined_volnorm_classification_metrics_v9_8,
    compute_refined_volnorm_walk_forward_metrics_v9_8,
)
from galapagos.ml.refined_volnorm_labels_offline_ml_v9_8_quality import assess_refined_volnorm_ml_quality_v9_8


VERSION_V9_8 = "V9.8"
ML_SCHEMA_VERSION_V9_8 = "V9.8"
TARGET_NAME_V9_8 = TARGET_NAME_V9_7
TIMEFRAMES_V9_8 = TIMEFRAMES_V9_7
MODEL_NAMES_V9_8 = ["majority_class_baseline", "random_seeded_baseline", "logistic_regression", "decision_tree_depth_2"]
TARGET_CLASSES_V9_8 = ["DOWN", "FLAT", "UP"]
ALLOWED_FEATURE_COLUMNS_V9_8 = [column for column in FEATURE_COLUMNS_V9_7 if column not in {"warmup_row", "refined_feature_null_count", "refined_feature_error_count"}]
ML_SCORE_COLUMNS_V9_8 = [
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
    "dataset_sha256",
    "feature_columns_sha256",
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
FORBIDDEN_FEATURE_TERMS_V9_8 = ["future_", "label_", "direction_", "up_down_flat_", "target", "split", "walk_forward_group", "prediction", "signal", "trading_signal", "order", "pnl", "backtest"]
FORBIDDEN_OUTPUT_COLUMNS_V9_8 = ["trading_signal", "signal", "order", "strategy", "pnl", "profit", "backtest"]
FORBIDDEN_METRIC_TERMS_V9_8 = ["pnl", "sharpe", "drawdown", "equity_curve", "profit_factor"]
MANIFEST_PATH_V9_8 = Path("reports/manifests/refined_volnorm_labels_offline_ml_v9_8_manifest.json")
REPORT_JSON_PATH_V9_8 = Path("reports/ml/refined_volnorm_labels_offline_ml_v9_8.json")
REPORT_MD_PATH_V9_8 = Path("reports/ml/refined_volnorm_labels_offline_ml_v9_8.md")
SCORES_JSON_PATH_V9_8 = Path("reports/ml/refined_volnorm_labels_offline_scores_v9_8.json")
SCORES_MD_PATH_V9_8 = Path("reports/ml/refined_volnorm_labels_offline_scores_v9_8.md")
DOC_PATH_V9_8 = Path("docs/refined_volnorm_labels_offline_ml_v9_8.md")
SAFETY_FLAGS_V9_8 = {
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
}
EXPECTED_LIMITATIONS_V9_8 = [
    "V9.8 entraine uniquement des baselines ML offline simples sur le dataset V9.7 avec labels volatility-normalized.",
    "V9.8 produit des scores research_* descriptifs, sans modele persistant, sans backtest, sans strategie, sans signal actionnable et sans ordre.",
]


def run_refined_volnorm_labels_offline_ml_v9_8(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    dataset_manifest = _read_json(root / MANIFEST_PATH_V9_7)
    ml_run_id = f"v9_8_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    outputs: dict[str, dict[str, Any]] = {}
    input_datasets: dict[str, dict[str, Any]] = {}
    input_splits: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    metrics: dict[str, Any] = {}
    walk_forward_metrics: dict[str, Any] = {}
    label_shuffle: dict[str, Any] = {}
    status = "PASS"
    for timeframe in TIMEFRAMES_V9_8:
        dataset_path = get_refined_volnorm_dataset_path_v9_7(root, timeframe)
        split_path = get_refined_volnorm_split_path_v9_7(root, timeframe)
        dataset = read_parquet(dataset_path)
        scores = build_refined_volnorm_model_scores_v9_8(dataset, dataset_sha256=sha256_file(dataset_path), ml_run_id=ml_run_id)
        score_path = get_refined_volnorm_ml_score_path_v9_8(root, timeframe)
        write_parquet(scores, score_path)
        outputs[timeframe] = _output_block(root, score_path, len(scores))
        input_datasets[timeframe] = _input_block(root, dataset_path, sha256_file(dataset_path), len(dataset))
        input_splits[timeframe] = _input_block(root, split_path, sha256_file(split_path), len(read_parquet(split_path)))
        quality[timeframe] = assess_refined_volnorm_ml_quality_v9_8(dataset, scores, timeframe)
        if quality[timeframe]["errors"]:
            status = "FAIL"
        metrics.update(compute_refined_volnorm_classification_metrics_v9_8(scores))
        walk_forward_metrics.update(compute_refined_volnorm_walk_forward_metrics_v9_8(scores))
        label_shuffle.update(compute_label_shuffle_falsification_v9_8(dataset, scores))
    decision = decide_v9_8(metrics, label_shuffle, status)
    report = {
        "version": VERSION_V9_8,
        "status": status,
        "created_at_utc": utc_now_iso(),
        "ml_run_id": ml_run_id,
        "decision": decision,
        "input_dataset_manifest": {"path": MANIFEST_PATH_V9_7.as_posix(), "sha256": sha256_file(root / MANIFEST_PATH_V9_7), "window_start": WINDOW_START_V9_7, "window_end": WINDOW_END_V9_7, "total_days": 366},
        "input_datasets": input_datasets,
        "input_splits": input_splits,
        "outputs": outputs,
        "target_name": TARGET_NAME_V9_8,
        "feature_columns": ALLOWED_FEATURE_COLUMNS_V9_8,
        "feature_columns_count": len(ALLOWED_FEATURE_COLUMNS_V9_8),
        "models": MODEL_NAMES_V9_8,
        "metrics": metrics,
        "walk_forward_metrics": walk_forward_metrics,
        "label_shuffle_falsification": label_shuffle,
        "quality": quality,
        "feature_leakage_scan": feature_leakage_scan_v9_8(ALLOWED_FEATURE_COLUMNS_V9_8),
        "metric_forbidden_scan": metric_forbidden_scan_v9_8({"metrics": metrics, "walk_forward_metrics": walk_forward_metrics, "label_shuffle_falsification": label_shuffle}),
        "findings": _findings(),
        "safety": dict(SAFETY_FLAGS_V9_8),
        "limitations": EXPECTED_LIMITATIONS_V9_8,
    }
    _write_json(root / MANIFEST_PATH_V9_8, report)
    _write_json(root / REPORT_JSON_PATH_V9_8, report)
    _write_json(root / SCORES_JSON_PATH_V9_8, {"version": VERSION_V9_8, "ml_run_id": ml_run_id, "outputs": outputs, "metrics": metrics, "walk_forward_metrics": walk_forward_metrics, "label_shuffle_falsification": label_shuffle})
    markdown = build_markdown_v9_8(report)
    for path in [REPORT_MD_PATH_V9_8, SCORES_MD_PATH_V9_8, DOC_PATH_V9_8]:
        _write_text(root / path, markdown)
    return report


def prepare_refined_volnorm_ml_frame_v9_8(dataset: pd.DataFrame) -> pd.DataFrame:
    return dataset[(dataset["label_valid_volnorm_h1"] == True) & (dataset["warmup_row"] == False)].reset_index(drop=True).copy()  # noqa: E712


def build_refined_volnorm_model_scores_v9_8(dataset: pd.DataFrame, *, dataset_sha256: str, ml_run_id: str) -> pd.DataFrame:
    ml_frame = prepare_refined_volnorm_ml_frame_v9_8(dataset)
    if ml_frame.empty:
        return pd.DataFrame(columns=ML_SCORE_COLUMNS_V9_8)
    train = ml_frame[ml_frame["split"] == "train"]
    score_frames: list[pd.DataFrame] = []
    feature_columns_sha = get_feature_columns_sha256_v9_8()
    for model_name in MODEL_NAMES_V9_8:
        result = fit_predict_model(model_name, train[ALLOWED_FEATURE_COLUMNS_V9_8], train[TARGET_NAME_V9_8].astype(str), ml_frame[ALLOWED_FEATURE_COLUMNS_V9_8])
        scores = ml_frame[["source", "venue", "market_type", "symbol", "timeframe", "event_ts", "close_ts", "decision_ts", "split", "walk_forward_group"]].copy()
        scores["ml_run_id"] = ml_run_id
        scores["model_name"] = model_name
        scores["target_name"] = TARGET_NAME_V9_8
        scores["dataset_sha256"] = dataset_sha256
        scores["feature_columns_sha256"] = feature_columns_sha
        scores["ml_schema_version"] = ML_SCHEMA_VERSION_V9_8
        scores["target_value"] = ml_frame[TARGET_NAME_V9_8].astype(str).to_numpy()
        scores["research_predicted_class"] = result.predicted_class.to_numpy()
        scores["research_probability_down"] = result.probabilities["DOWN"].to_numpy()
        scores["research_probability_flat"] = result.probabilities["FLAT"].to_numpy()
        scores["research_probability_up"] = result.probabilities["UP"].to_numpy()
        scores["prediction_available_ts"] = ml_frame["decision_ts"].to_numpy()
        scores["row_valid_for_ml"] = True
        scores["ml_null_count"] = scores.isna().sum(axis=1).astype(int)
        scores["ml_error_count"] = 0
        score_frames.append(scores[ML_SCORE_COLUMNS_V9_8])
    return pd.concat(score_frames, ignore_index=True)


def compute_label_shuffle_falsification_v9_8(dataset: pd.DataFrame, scores: pd.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {}
    ml_frame = prepare_refined_volnorm_ml_frame_v9_8(dataset)
    train = ml_frame[ml_frame["split"] == "train"]
    evaluation = ml_frame[ml_frame["split"].isin(["validation", "test"])]
    if train.empty or evaluation.empty:
        return result
    shuffled_target = train[TARGET_NAME_V9_8].sample(frac=1.0, random_state=123).reset_index(drop=True)
    for model_name in ["logistic_regression", "decision_tree_depth_2"]:
        shuffled = fit_predict_model(model_name, train[ALLOWED_FEATURE_COLUMNS_V9_8], shuffled_target.astype(str), evaluation[ALLOWED_FEATURE_COLUMNS_V9_8])
        for split, split_frame in evaluation.groupby("split", sort=True):
            original = scores[(scores["model_name"] == model_name) & (scores["split"] == split)]
            original_acc = float((original["target_value"].astype(str).to_numpy() == original["research_predicted_class"].astype(str).to_numpy()).mean())
            mask = evaluation["split"].eq(split).to_numpy()
            shuffled_pred = shuffled.predicted_class.to_numpy()[mask]
            true = split_frame[TARGET_NAME_V9_8].astype(str).to_numpy()
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


def decide_v9_8(metrics: dict[str, Any], label_shuffle: dict[str, Any], status: str) -> str:
    if status != "PASS":
        return "stop_refined_branch_ml_failed"
    if any(item.get("no_clear_edge_vs_shuffled_labels") for item in label_shuffle.values()):
        return "offline_ml_completed_but_close_to_shuffled_labels"
    learned_validation = [item for item in metrics.values() if item["model_name"] in {"logistic_regression", "decision_tree_depth_2"} and item["split"] in {"validation", "test"}]
    if learned_validation and max(item["macro_f1"] for item in learned_validation) < 0.40:
        return "offline_ml_completed_but_weak_vs_baselines"
    return "offline_ml_completed_volnorm_labels"


def feature_leakage_scan_v9_8(columns: list[str]) -> dict[str, Any]:
    forbidden = [column for column in columns if any(term in column.casefold() for term in FORBIDDEN_FEATURE_TERMS_V9_8)]
    return {"passed": not forbidden, "forbidden_feature_columns_present": forbidden}


def metric_forbidden_scan_v9_8(payload: Any) -> dict[str, Any]:
    found: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if str(key).casefold() in FORBIDDEN_METRIC_TERMS_V9_8:
                    found.append(str(key))
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)
    return {"passed": not found, "forbidden_terms_present": sorted(set(found))}


def build_markdown_v9_8(report: dict[str, Any]) -> str:
    lines = [
        "# V9.8 - ML offline avec labels volatility-normalized",
        "",
        "V9.8 entraine des baselines ML offline simples. Les scores sont descriptifs, non actionnables et sans backtest.",
        "",
        f"- Decision : `{report['decision']}`.",
        f"- Cible : `{report['target_name']}`.",
        f"- Features : `{report['feature_columns_count']}`.",
        "",
        "## Outputs",
    ]
    for timeframe, output in report["outputs"].items():
        lines.append(f"- `{timeframe}` : `{output['path']}` ({output['rows']} lignes).")
    lines.extend(["", "## Interdits maintenus", "", "- Aucun backtest.", "- Aucune strategie.", "- Aucun signal actionnable.", "- Aucun ordre.", "- Aucun modele persistant.", "- Aucun trading reel."])
    return "\n".join(lines) + "\n"


def get_refined_volnorm_ml_score_path_v9_8(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v9_8/ml/refined_volnorm_labels"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_START_V9_7}_{WINDOW_END_V9_7}"
        / "ml-scores.parquet"
    )


def get_feature_columns_sha256_v9_8() -> str:
    payload = json.dumps(ALLOWED_FEATURE_COLUMNS_V9_8, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _findings() -> dict[str, bool]:
    return {
        "robust_edge_claimed": False,
        "strategy_validated": False,
        "backtest_performed": False,
        "actionable_signal_produced": False,
        "walk_forward_validated_for_trading": False,
        "trading_allowed": False,
        "paper_live_allowed": False,
        "real_trading_allowed": False,
    }


def _input_block(root: Path, path: Path, digest: str, rows: int) -> dict[str, Any]:
    return {"path": path.relative_to(root).as_posix(), "sha256": digest, "rows": int(rows)}


def _output_block(root: Path, path: Path, rows: int) -> dict[str, Any]:
    return {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path), "bytes": path.stat().st_size, "rows": int(rows), "format": "parquet"}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
