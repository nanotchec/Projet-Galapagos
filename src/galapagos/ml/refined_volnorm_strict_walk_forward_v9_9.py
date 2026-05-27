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
)
from galapagos.ml.offline_baselines import fit_predict_model
from galapagos.ml.refined_strict_walk_forward import (
    WALK_FORWARD_POLICY_V9_3,
    build_refined_strict_walk_forward_folds_v9_3,
)
from galapagos.ml.refined_volnorm_strict_walk_forward_v9_9_metrics import (
    compute_refined_volnorm_strict_walk_forward_aggregate_metrics_v9_9,
    compute_refined_volnorm_strict_walk_forward_metrics_v9_9,
)
from galapagos.ml.refined_volnorm_strict_walk_forward_v9_9_quality import assess_refined_volnorm_strict_walk_forward_quality_v9_9
from galapagos.ml.refined_volnorm_labels_offline_ml_v9_8 import (
    ALLOWED_FEATURE_COLUMNS_V9_8,
    FORBIDDEN_METRIC_TERMS_V9_8,
    ML_SCORE_COLUMNS_V9_8,
    MODEL_NAMES_V9_8,
    TARGET_CLASSES_V9_8,
    feature_leakage_scan_v9_8,
    metric_forbidden_scan_v9_8,
)


VERSION_V9_9 = "V9.9"
ML_SCHEMA_VERSION_V9_9 = "V9.9"
TARGET_NAME_V9_9 = TARGET_NAME_V9_7
TIMEFRAMES_V9_9 = TIMEFRAMES_V9_7
MODEL_NAMES_V9_9 = MODEL_NAMES_V9_8
ALLOWED_FEATURE_COLUMNS_V9_9 = ALLOWED_FEATURE_COLUMNS_V9_8
ML_SCORE_COLUMNS_V9_9 = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "timeframe",
    "event_ts",
    "close_ts",
    "decision_ts",
    "fold_id",
    "fold_role",
    "fold_order",
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
WALK_FORWARD_FOLD_COLUMNS_V9_9 = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "timeframe",
    "event_ts",
    "fold_id",
    "fold_role",
    "fold_order",
    "is_embargoed",
    "is_purged",
    "walk_forward_policy_version",
]
MANIFEST_PATH_V9_9 = Path("reports/manifests/refined_volnorm_strict_walk_forward_v9_9_manifest.json")
REPORT_JSON_PATH_V9_9 = Path("reports/ml/refined_volnorm_strict_walk_forward_v9_9.json")
REPORT_MD_PATH_V9_9 = Path("reports/ml/refined_volnorm_strict_walk_forward_v9_9.md")
SCORES_JSON_PATH_V9_9 = Path("reports/ml/refined_volnorm_strict_walk_forward_scores_v9_9.json")
SCORES_MD_PATH_V9_9 = Path("reports/ml/refined_volnorm_strict_walk_forward_scores_v9_9.md")
DOC_PATH_V9_9 = Path("docs/refined_volnorm_strict_walk_forward_v9_9.md")
SAFETY_FLAGS_V9_9 = {
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
EXPECTED_LIMITATIONS_V9_9 = [
    "V9.9 execute une validation walk-forward stricte offline sur le dataset V9.7.",
    "V9.9 ne produit aucun backtest, aucune strategie, aucun signal actionnable, aucun ordre et aucun modele persistant.",
]


def run_refined_volnorm_strict_walk_forward_v9_9(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    dataset_manifest = _read_json(root / MANIFEST_PATH_V9_7)
    run_id = f"v9_9_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    input_datasets: dict[str, Any] = {}
    outputs = {"scores": {}, "folds": {}}
    folds_summary: dict[str, Any] = {}
    metrics: dict[str, Any] = {}
    aggregate_metrics: dict[str, Any] = {}
    label_shuffle: dict[str, Any] = {}
    quality: dict[str, Any] = {}
    status = "PASS"
    for timeframe in TIMEFRAMES_V9_9:
        dataset_path = get_refined_volnorm_dataset_path_v9_7(root, timeframe)
        dataset_sha = sha256_file(dataset_path)
        dataset = read_parquet(dataset_path).sort_values("event_ts").reset_index(drop=True)
        folds = build_refined_strict_walk_forward_folds_v9_3(dataset, WINDOW_START_V9_7, WINDOW_END_V9_7)
        scores = build_refined_volnorm_walk_forward_scores_v9_9(dataset, folds, dataset_sha256=dataset_sha, ml_run_id=run_id)
        fold_metrics = compute_refined_volnorm_strict_walk_forward_metrics_v9_9(scores)
        metrics.update(fold_metrics)
        aggregate_metrics.update(compute_refined_volnorm_strict_walk_forward_aggregate_metrics_v9_9(fold_metrics))
        label_shuffle.update(compute_label_shuffle_falsification_v9_9(dataset, folds, fold_metrics))
        score_path = get_refined_volnorm_walk_forward_score_path_v9_9(root, timeframe)
        folds_path = get_refined_volnorm_walk_forward_folds_path_v9_9(root, timeframe)
        write_parquet(scores, score_path)
        write_parquet(folds[WALK_FORWARD_FOLD_COLUMNS_V9_9], folds_path)
        input_datasets[timeframe] = _input_block(root, dataset_path, dataset_sha, len(dataset))
        outputs["scores"][timeframe] = _output_block(root, score_path, len(scores))
        outputs["folds"][timeframe] = _output_block(root, folds_path, len(folds))
        folds_summary[timeframe] = summarize_folds_v9_9(folds)
        quality[timeframe] = assess_refined_volnorm_strict_walk_forward_quality_v9_9(dataset, folds, scores, timeframe)
        if quality[timeframe]["errors"]:
            status = "FAIL"
    comparison = compare_to_static_split_v9_8(root, aggregate_metrics)
    report = {
        "version": VERSION_V9_9,
        "status": status,
        "created_at_utc": utc_now_iso(),
        "walk_forward_run_id": run_id,
        "decision": decide_v9_9(aggregate_metrics, label_shuffle, status),
        "input_dataset_manifest": {"path": MANIFEST_PATH_V9_7.as_posix(), "sha256": sha256_file(root / MANIFEST_PATH_V9_7), "window_start": WINDOW_START_V9_7, "window_end": WINDOW_END_V9_7, "total_days": 366},
        "input_datasets": input_datasets,
        "walk_forward_policy": WALK_FORWARD_POLICY_V9_3,
        "folds": folds_summary,
        "outputs": outputs,
        "target_name": TARGET_NAME_V9_9,
        "feature_columns": ALLOWED_FEATURE_COLUMNS_V9_9,
        "feature_columns_count": len(ALLOWED_FEATURE_COLUMNS_V9_9),
        "models": MODEL_NAMES_V9_9,
        "metrics": metrics,
        "aggregate_metrics": aggregate_metrics,
        "label_shuffle_falsification": label_shuffle,
        "comparison_to_static_split_v9_8": comparison,
        "feature_leakage_scan": feature_leakage_scan_v9_8(ALLOWED_FEATURE_COLUMNS_V9_9),
        "metric_forbidden_scan": metric_forbidden_scan_v9_8({"metrics": metrics, "aggregate_metrics": aggregate_metrics, "label_shuffle_falsification": label_shuffle}),
        "findings": _findings(),
        "quality": quality,
        "safety": SAFETY_FLAGS_V9_9,
        "limitations": EXPECTED_LIMITATIONS_V9_9,
    }
    _write_json(root / MANIFEST_PATH_V9_9, report)
    _write_json(root / REPORT_JSON_PATH_V9_9, report)
    _write_json(root / SCORES_JSON_PATH_V9_9, {"version": VERSION_V9_9, "walk_forward_run_id": run_id, "outputs": outputs, "metrics": metrics, "aggregate_metrics": aggregate_metrics, "label_shuffle_falsification": label_shuffle})
    markdown = build_markdown_v9_9(report)
    for path in [REPORT_MD_PATH_V9_9, SCORES_MD_PATH_V9_9, DOC_PATH_V9_9]:
        _write_text(root / path, markdown)
    return report


def prepare_refined_volnorm_walk_forward_ml_frame_v9_9(merged: pd.DataFrame) -> pd.DataFrame:
    return merged[
        (merged["label_valid_volnorm_h1"] == True)
        & (merged["warmup_row"] == False)
        & (merged["is_embargoed"] == False)
        & (merged["is_purged"] == False)
    ].reset_index(drop=True).copy()  # noqa: E712


def build_refined_volnorm_walk_forward_scores_v9_9(dataset: pd.DataFrame, folds: pd.DataFrame, *, dataset_sha256: str, ml_run_id: str) -> pd.DataFrame:
    merged = folds.merge(dataset, on=["source", "venue", "market_type", "symbol", "timeframe", "event_ts"], how="left", validate="many_to_one")
    merged = prepare_refined_volnorm_walk_forward_ml_frame_v9_9(merged)
    score_frames: list[pd.DataFrame] = []
    feature_sha = get_feature_columns_sha256_v9_9()
    for _fold_id, fold_frame in merged.groupby("fold_id", sort=True):
        train = fold_frame[fold_frame["fold_role"] == "train"]
        if train.empty:
            continue
        for model_name in MODEL_NAMES_V9_9:
            result = fit_predict_model(model_name, train[ALLOWED_FEATURE_COLUMNS_V9_9], train[TARGET_NAME_V9_9].astype(str), fold_frame[ALLOWED_FEATURE_COLUMNS_V9_9])
            scores = fold_frame[["source", "venue", "market_type", "symbol", "timeframe", "event_ts", "close_ts", "decision_ts", "fold_id", "fold_role", "fold_order"]].copy()
            scores["ml_run_id"] = ml_run_id
            scores["model_name"] = model_name
            scores["target_name"] = TARGET_NAME_V9_9
            scores["dataset_sha256"] = dataset_sha256
            scores["feature_columns_sha256"] = feature_sha
            scores["ml_schema_version"] = ML_SCHEMA_VERSION_V9_9
            scores["target_value"] = fold_frame[TARGET_NAME_V9_9].astype(str).to_numpy()
            scores["research_predicted_class"] = result.predicted_class.to_numpy()
            scores["research_probability_down"] = result.probabilities["DOWN"].to_numpy()
            scores["research_probability_flat"] = result.probabilities["FLAT"].to_numpy()
            scores["research_probability_up"] = result.probabilities["UP"].to_numpy()
            scores["prediction_available_ts"] = fold_frame["decision_ts"].to_numpy()
            scores["row_valid_for_ml"] = True
            scores["ml_null_count"] = scores.isna().sum(axis=1).astype(int)
            scores["ml_error_count"] = 0
            score_frames.append(scores[ML_SCORE_COLUMNS_V9_9])
    return pd.concat(score_frames, ignore_index=True) if score_frames else pd.DataFrame(columns=ML_SCORE_COLUMNS_V9_9)


def compute_label_shuffle_falsification_v9_9(dataset: pd.DataFrame, folds: pd.DataFrame, original_metrics: dict[str, Any]) -> dict[str, Any]:
    merged = folds.merge(dataset, on=["source", "venue", "market_type", "symbol", "timeframe", "event_ts"], how="left", validate="many_to_one")
    merged = prepare_refined_volnorm_walk_forward_ml_frame_v9_9(merged)
    result: dict[str, Any] = {}
    for (fold_id, fold_order), fold_frame in merged.groupby(["fold_id", "fold_order"], sort=True):
        train = fold_frame[fold_frame["fold_role"] == "train"]
        eval_frame = fold_frame[fold_frame["fold_role"].isin(["validation", "test"])]
        if train.empty or eval_frame.empty:
            continue
        shuffled_target = train[TARGET_NAME_V9_9].sample(frac=1.0, random_state=123 + int(fold_order)).reset_index(drop=True)
        for model_name in ["logistic_regression", "decision_tree_depth_2"]:
            pred = fit_predict_model(model_name, train[ALLOWED_FEATURE_COLUMNS_V9_9], shuffled_target.astype(str), eval_frame[ALLOWED_FEATURE_COLUMNS_V9_9])
            for role, role_frame in eval_frame.groupby("fold_role", sort=True):
                mask = eval_frame["fold_role"].eq(role).to_numpy()
                y_true = role_frame[TARGET_NAME_V9_9].astype(str).to_numpy()
                shuffled_acc = float((y_true == pred.predicted_class.to_numpy()[mask]).mean())
                key = f"{str(dataset['timeframe'].iloc[0])}.{model_name}.{fold_id}.{role}"
                original_acc = original_metrics.get(key, {}).get("accuracy", 0.0)
                result[key] = {
                    "timeframe": str(dataset["timeframe"].iloc[0]),
                    "model_name": model_name,
                    "fold_id": fold_id,
                    "fold_order": int(fold_order),
                    "fold_role": role,
                    "original_accuracy": float(original_acc),
                    "shuffled_accuracy": shuffled_acc,
                    "delta_original_vs_shuffled": float(original_acc - shuffled_acc),
                    "no_clear_edge_vs_shuffled_labels": float(original_acc - shuffled_acc) < 0.02,
                    "random_seed": 123 + int(fold_order),
                }
    return result


def summarize_folds_v9_9(folds: pd.DataFrame) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for (fold_id, fold_order), group in folds.groupby(["fold_id", "fold_order"], sort=True):
        item: dict[str, Any] = {"fold_id": fold_id, "fold_order": int(fold_order)}
        for role in ["train", "validation", "test"]:
            role_group = group[group["fold_role"] == role]
            ts = pd.to_datetime(role_group["event_ts"], utc=True)
            item[f"{role}_start"] = ts.min().date().isoformat()
            item[f"{role}_end"] = ts.max().date().isoformat()
            item[f"{role}_rows"] = int(len(role_group))
        item["purged_rows"] = int(group["is_purged"].sum())
        item["embargoed_rows"] = int(group["is_embargoed"].sum())
        summary.append(item)
    return summary


def compare_to_static_split_v9_8(root: Path, aggregate_metrics: dict[str, Any]) -> dict[str, Any]:
    path = root / "reports/manifests/refined_volnorm_labels_offline_ml_v9_8_manifest.json"
    if not path.exists():
        return {"available": False, "warning": "V9.8 manifest absent"}
    v98 = _read_json(path)
    return {
        "available": True,
        "comparison_type": "descriptive_static_split_vs_strict_walk_forward",
        "warning": "V9.8 static split and V9.9 strict walk-forward are not identical validation designs.",
        "v9_8_decision": v98.get("decision"),
        "v9_9_aggregate_metric_keys": sorted(aggregate_metrics)[:20],
    }


def decide_v9_9(aggregate_metrics: dict[str, Any], label_shuffle: dict[str, Any], status: str) -> str:
    if status != "PASS":
        return "stop_refined_branch_walk_forward_failed"
    if any(item.get("no_clear_edge_vs_shuffled_labels") for item in label_shuffle.values()):
        return "strict_walk_forward_completed_but_close_to_shuffled_labels"
    unstable = [item for item in aggregate_metrics.values() if item.get("std_test_accuracy", 0.0) > 0.10 or item.get("weak_folds")]
    if unstable:
        return "strict_walk_forward_completed_but_unstable"
    return "strict_walk_forward_completed_volnorm_labels"


def build_markdown_v9_9(report: dict[str, Any]) -> str:
    lines = [
        "# V9.9 - Strict walk-forward avec labels volatility-normalized",
        "",
        "V9.9 est une validation offline stricte. Ce n'est pas un backtest et ne produit aucun signal actionnable.",
        "",
        f"- Decision : `{report['decision']}`.",
        f"- Cible : `{report['target_name']}`.",
    ]
    for timeframe, folds in report["folds"].items():
        lines.append(f"- `{timeframe}` : `{len(folds)}` folds.")
    lines.extend(["", "## Interdits maintenus", "", "- Aucun backtest.", "- Aucune strategie.", "- Aucun signal actionnable.", "- Aucun ordre.", "- Aucun modele persistant.", "- Aucun trading reel."])
    return "\n".join(lines) + "\n"


def get_refined_volnorm_walk_forward_score_path_v9_9(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v9_9/ml/refined_volnorm_strict_walk_forward"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_START_V9_7}_{WINDOW_END_V9_7}"
        / "walk_forward_scores.parquet"
    )


def get_refined_volnorm_walk_forward_folds_path_v9_9(root: Path, timeframe: str) -> Path:
    return get_refined_volnorm_walk_forward_score_path_v9_9(root, timeframe).with_name("folds.parquet")


def get_feature_columns_sha256_v9_9() -> str:
    return hashlib.sha256(json.dumps(ALLOWED_FEATURE_COLUMNS_V9_9, separators=(",", ":"), sort_keys=False).encode("utf-8")).hexdigest()


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
