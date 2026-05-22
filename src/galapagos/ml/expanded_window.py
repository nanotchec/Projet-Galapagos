from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.datasets.expanded_window_validation import validate_expanded_offline_supervised_dataset_v3_8
from galapagos.datasets.schemas import get_dataset_v3_8_path, get_split_v3_8_path
from galapagos.ml.expanded_window_metrics import compute_expanded_classification_metrics_v3_9
from galapagos.ml.expanded_window_quality import assess_expanded_ml_quality_v3_9
from galapagos.ml.offline_baselines import fit_predict_model
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V3_9,
    DOC_PATH_V3_9,
    EXPECTED_LIMITATIONS_V3_9,
    MANIFEST_PATH_V3_9,
    ML_SCHEMA_VERSION_V3_9,
    ML_SCORE_COLUMNS_V3_9,
    MODEL_NAMES_V3_9,
    REPORT_JSON_PATH_V3_9,
    REPORT_MD_PATH_V3_9,
    SAFETY_FLAGS_V3_9,
    SCORES_JSON_PATH_V3_9,
    SCORES_MD_PATH_V3_9,
    TARGET_NAME_V3_9,
    TIMEFRAMES_V3_9,
    VERSION_V3_9,
    get_expanded_ml_score_path_v3_9,
    get_feature_columns_sha256_v3_9,
)


def run_expanded_offline_ml_research_v3_9(
    root: Path = Path("."),
    *,
    validate_dataset: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_dataset:
        _validate_dataset_layer(root)

    created_at = utc_now_iso()
    ml_run_id = f"v3_9_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    input_datasets: dict[str, dict[str, Any]] = {}
    input_splits: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    sanity_checks: dict[str, dict[str, Any]] = {}
    all_scores: list[pd.DataFrame] = []
    status = "PASS"

    for timeframe in TIMEFRAMES_V3_9:
        dataset_path = get_dataset_v3_8_path(root, timeframe)
        split_path = get_split_v3_8_path(root, timeframe)
        score_path = get_expanded_ml_score_path_v3_9(root, timeframe)
        dataset = read_parquet(dataset_path)
        splits = read_parquet(split_path)
        dataset_sha = sha256_file(dataset_path)

        scores = build_expanded_model_scores_v3_9(dataset, dataset_sha256=dataset_sha, ml_run_id=ml_run_id)
        write_parquet(scores, score_path)
        all_scores.append(scores)

        input_datasets[timeframe] = _input_block(root, dataset_path, dataset_sha, len(dataset))
        input_splits[timeframe] = _input_block(root, split_path, sha256_file(split_path), len(splits))
        outputs[timeframe] = _output_block(root, score_path, len(scores))
        quality[timeframe] = assess_expanded_ml_quality_v3_9(dataset, scores, timeframe)
        if quality[timeframe]["errors"]:
            status = "FAIL"
        sanity_checks[timeframe] = _sanity_from_quality(dataset, quality[timeframe])

    non_empty_scores = [frame for frame in all_scores if not frame.empty]
    metrics = compute_expanded_classification_metrics_v3_9(pd.concat(non_empty_scores, ignore_index=True))
    manifest = {
        "version": VERSION_V3_9,
        "status": status,
        "created_at_utc": created_at,
        "ml_run_id": ml_run_id,
        "input_datasets": input_datasets,
        "input_splits": input_splits,
        "outputs": outputs,
        "target_name": TARGET_NAME_V3_9,
        "feature_columns": ALLOWED_FEATURE_COLUMNS_V3_9,
        "models": MODEL_NAMES_V3_9,
        "metrics": metrics,
        "sanity_checks": sanity_checks,
        "quality": quality,
        "safety": SAFETY_FLAGS_V3_9,
        "limitations": EXPECTED_LIMITATIONS_V3_9,
    }

    _write_json(root / MANIFEST_PATH_V3_9, manifest)
    _write_json(root / REPORT_JSON_PATH_V3_9, manifest)
    _write_json(root / SCORES_JSON_PATH_V3_9, _scores_report(manifest))
    markdown = build_expanded_ml_markdown_v3_9(manifest)
    _write_text(root / REPORT_MD_PATH_V3_9, markdown)
    _write_text(root / SCORES_MD_PATH_V3_9, markdown)
    _write_text(root / DOC_PATH_V3_9, markdown)
    return manifest


def prepare_expanded_ml_frame_v3_9(dataset: pd.DataFrame) -> pd.DataFrame:
    frame = dataset[(dataset["label_valid_h1"] == True) & (dataset["warmup_row"] == False)].copy()  # noqa: E712
    return frame.reset_index(drop=True)


def get_expanded_training_slices_v3_9(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {split: frame[frame["split"] == split].copy() for split in ["train", "validation", "test"]}


def build_expanded_model_scores_v3_9(
    dataset: pd.DataFrame,
    *,
    dataset_sha256: str,
    ml_run_id: str,
) -> pd.DataFrame:
    ml_frame = prepare_expanded_ml_frame_v3_9(dataset)
    slices = get_expanded_training_slices_v3_9(ml_frame)
    train = slices["train"]
    if train.empty:
        return pd.DataFrame(columns=ML_SCORE_COLUMNS_V3_9)

    score_frames: list[pd.DataFrame] = []
    train_features = train[ALLOWED_FEATURE_COLUMNS_V3_9]
    train_target = train[TARGET_NAME_V3_9].astype(str)
    feature_columns_sha256 = get_feature_columns_sha256_v3_9()

    for model_name in MODEL_NAMES_V3_9:
        for split_name, split_frame in slices.items():
            if split_frame.empty:
                continue
            result = fit_predict_model(
                model_name,
                train_features,
                train_target,
                split_frame[ALLOWED_FEATURE_COLUMNS_V3_9],
            )
            scores = split_frame[
                ["source", "venue", "market_type", "symbol", "timeframe", "event_ts", "close_ts", "decision_ts", "split"]
            ].copy()
            scores["ml_run_id"] = ml_run_id
            scores["model_name"] = model_name
            scores["target_name"] = TARGET_NAME_V3_9
            scores["dataset_sha256"] = dataset_sha256
            scores["feature_columns_sha256"] = feature_columns_sha256
            scores["ml_schema_version"] = ML_SCHEMA_VERSION_V3_9
            scores["target_value"] = split_frame[TARGET_NAME_V3_9].astype(str).to_numpy()
            scores["research_predicted_class"] = result.predicted_class.to_numpy()
            scores["research_probability_down"] = result.probabilities["DOWN"].to_numpy()
            scores["research_probability_flat"] = result.probabilities["FLAT"].to_numpy()
            scores["research_probability_up"] = result.probabilities["UP"].to_numpy()
            scores["prediction_available_ts"] = split_frame["decision_ts"].to_numpy()
            scores["row_valid_for_ml"] = True
            scores["ml_null_count"] = scores.isna().sum(axis=1).astype(int)
            scores["ml_error_count"] = 0
            score_frames.append(scores[ML_SCORE_COLUMNS_V3_9])

    return pd.concat(score_frames, ignore_index=True)


def build_expanded_ml_markdown_v3_9(manifest: dict[str, Any]) -> str:
    lines = [
        "# Rapport qualite - V3.9 ML offline 90 jours",
        "",
        "## Objectif",
        "",
        "V3.9 entraine des baselines ML offline simples sur le dataset 90 jours V3.8 valide.",
        "Ces sorties sont des scores de recherche descriptifs, non actionnables et sans usage de trading.",
        "",
        "## Cible et modeles",
        "",
        f"- Cible : `{manifest['target_name']}`.",
        f"- Modeles : `{', '.join(manifest['models'])}`.",
        "- Features : colonnes causales V3.6 autorisees uniquement.",
        "",
        "## Outputs",
        "",
    ]
    for timeframe, output in manifest["outputs"].items():
        item = manifest["quality"][timeframe]
        lines.extend(
            [
                f"- `{timeframe}` scores : `{output['path']}` ({output['rows']} lignes).",
                f"  - lignes ML utilisees : `{item['rows_used_for_ml']}`.",
                f"  - train/validation/test : `{item['train_rows']}` / `{item['validation_rows']}` / `{item['test_rows']}`.",
            ]
        )
    lines.extend(
        [
            "",
            "## Sanity checks",
            "",
            "- La cible unique est `up_down_flat_h1`.",
            "- Les lignes `warmup_row = true` et `label_valid_h1 = false` sont exclues.",
            "- Les features `future_*`, `label_*`, `direction_*`, `up_down_flat_*`, `split`, `signal`, `order`, `strategy`, `pnl` et `backtest` sont interdites.",
            "- Les sorties sont nommees `research_*` et ne sont pas des signaux.",
            "- Les metriques sont descriptives : accuracy, balanced accuracy, macro F1, precision/rappel par classe et matrices de confusion.",
            "",
            "## Limitations",
            "",
            *[f"- {item}" for item in manifest["limitations"]],
            "",
            "## Non-usage warnings",
            "",
            "- V3.9 ne valide aucune strategie.",
            "- V3.9 ne produit aucun backtest.",
            "- V3.9 ne produit aucun signal de trading.",
            "- V3.9 ne produit aucun ordre.",
            "- V3.9 n'autorise aucun paper live.",
            "- V3.9 n'autorise aucun trading reel.",
            "- Les metriques sont descriptives et non actionnables.",
        ]
    )
    return "\n".join(lines) + "\n"


def _validate_dataset_layer(root: Path) -> None:
    result = validate_expanded_offline_supervised_dataset_v3_8(root)
    if not result["passed"]:
        raise RuntimeError(f"V3.8 dataset validation failed before V3.9: {result['errors']}")


def _input_block(root: Path, path: Path, sha256: str, rows: int) -> dict[str, Any]:
    return {"path": str(path.relative_to(root)), "sha256": sha256, "rows": int(rows)}


def _output_block(root: Path, path: Path, rows: int) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(root)),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": int(rows),
        "format": "parquet",
    }


def _sanity_from_quality(dataset: pd.DataFrame, quality: dict[str, Any]) -> dict[str, Any]:
    used = prepare_expanded_ml_frame_v3_9(dataset)
    return {
        "train_rows": quality["train_rows"],
        "validation_rows": quality["validation_rows"],
        "test_rows": quality["test_rows"],
        "target_classes_seen_train": _target_classes(used, "train"),
        "target_classes_seen_validation": _target_classes(used, "validation"),
        "target_classes_seen_test": _target_classes(used, "test"),
        "no_shuffle_confirmed": quality["no_shuffle_confirmed"],
        "forbidden_feature_columns_present": quality["forbidden_feature_columns_present"],
        "forbidden_output_columns_present": quality["forbidden_output_columns_present"],
    }


def _target_classes(frame: pd.DataFrame, split: str) -> list[str]:
    return sorted(frame[frame["split"] == split][TARGET_NAME_V3_9].dropna().astype(str).unique().tolist())


def _scores_report(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": manifest["version"],
        "ml_run_id": manifest["ml_run_id"],
        "outputs": manifest["outputs"],
        "metrics": manifest["metrics"],
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
