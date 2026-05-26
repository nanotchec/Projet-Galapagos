from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.testing import assert_frame_equal

from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.datasets.refined_ohlcv_trades_window_validation import validate_refined_ohlcv_trades_offline_supervised_dataset_v9_1
from galapagos.datasets.schemas import MANIFEST_PATH_V9_1, SPLIT_COLUMNS_V9_1
from galapagos.ml.offline_baselines import fit_predict_model
from galapagos.ml.refined_ohlcv_trades_window_metrics import (
    compute_refined_ohlcv_trades_classification_metrics_v9_2,
    compute_refined_ohlcv_trades_walk_forward_metrics_v9_2,
)
from galapagos.ml.refined_ohlcv_trades_window_quality import assess_refined_ohlcv_trades_ml_quality_v9_2
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V9_2,
    DOC_PATH_V9_2,
    EXPECTED_LIMITATIONS_V9_2,
    MANIFEST_PATH_V9_2,
    ML_SCHEMA_VERSION_V9_2,
    ML_SCORE_COLUMNS_V9_2,
    MODEL_NAMES_V9_2,
    REPORT_JSON_PATH_V9_2,
    REPORT_MD_PATH_V9_2,
    SAFETY_FLAGS_V9_2,
    SCORES_JSON_PATH_V9_2,
    SCORES_MD_PATH_V9_2,
    TARGET_NAME_V9_2,
    TIMEFRAMES_V9_2,
    VERSION_V9_2,
    get_feature_columns_sha256_v9_2,
    get_refined_ohlcv_trades_ml_score_path_v9_2,
)


def run_refined_ohlcv_trades_offline_ml_research_v9_2(
    root: Path = Path("."),
    *,
    validate_dataset: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_dataset:
        _validate_dataset_layer(root)

    dataset_manifest = load_v9_1_dataset_manifest(root)
    window = _input_window(dataset_manifest)
    window_start = window["window_start"]
    window_end = window["window_end"]
    total_days = int(window["total_days"])

    created_at = utc_now_iso()
    ml_run_id = f"v9_2_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    input_datasets: dict[str, dict[str, Any]] = {}
    input_splits: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    metrics: dict[str, Any] = {}
    walk_forward_metrics: dict[str, Any] = {}
    quality: dict[str, dict[str, Any]] = {}
    sanity_checks: dict[str, dict[str, Any]] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V9_2:
        dataset_path = input_dataset_path(root, timeframe, dataset_manifest)
        split_path = input_split_path(root, timeframe, dataset_manifest)
        score_path = score_output_path(root, timeframe, window_start, window_end)
        dataset = read_parquet(dataset_path)
        splits = read_parquet(split_path)
        dataset_for_ml = validate_split_alignment_v9_2(dataset, splits)
        dataset_sha = sha256_file(dataset_path)

        scores = build_refined_ohlcv_trades_model_scores_v9_2(dataset_for_ml, dataset_sha256=dataset_sha, ml_run_id=ml_run_id)
        write_parquet(scores, score_path)

        input_datasets[timeframe] = _input_block(root, dataset_path, dataset_sha, len(dataset))
        input_splits[timeframe] = _input_block(root, split_path, sha256_file(split_path), len(splits))
        outputs[timeframe] = _output_block(root, score_path, len(scores))
        quality[timeframe] = assess_refined_ohlcv_trades_ml_quality_v9_2(dataset_for_ml, scores, timeframe)
        if quality[timeframe]["errors"]:
            status = "FAIL"
        sanity_checks[timeframe] = _sanity_from_quality(quality[timeframe])
        metrics.update(compute_refined_ohlcv_trades_classification_metrics_v9_2(scores))
        walk_forward_metrics.update(compute_refined_ohlcv_trades_walk_forward_metrics_v9_2(scores))

    manifest = {
        "version": VERSION_V9_2,
        "status": status,
        "created_at_utc": created_at,
        "ml_run_id": ml_run_id,
        "input_dataset_manifest": {
            "path": MANIFEST_PATH_V9_1.as_posix(),
            "sha256": sha256_file(root / MANIFEST_PATH_V9_1),
            "window_start": window_start,
            "window_end": window_end,
            "total_days": total_days,
            "feature_columns_count": int(dataset_manifest["feature_columns_count"]),
        },
        "input_datasets": input_datasets,
        "input_splits": input_splits,
        "outputs": outputs,
        "target_name": TARGET_NAME_V9_2,
        "feature_columns": ALLOWED_FEATURE_COLUMNS_V9_2,
        "feature_columns_count": len(ALLOWED_FEATURE_COLUMNS_V9_2),
        "models": MODEL_NAMES_V9_2,
        "metrics": metrics,
        "walk_forward_metrics": walk_forward_metrics,
        "sanity_checks": sanity_checks,
        "quality": quality,
        "safety": SAFETY_FLAGS_V9_2,
        "limitations": EXPECTED_LIMITATIONS_V9_2,
    }

    _write_json(root / MANIFEST_PATH_V9_2, manifest)
    _write_json(root / REPORT_JSON_PATH_V9_2, manifest)
    _write_json(root / SCORES_JSON_PATH_V9_2, _scores_report(manifest))
    markdown = build_refined_ohlcv_trades_ml_markdown_v9_2(manifest)
    _write_text(root / REPORT_MD_PATH_V9_2, markdown)
    _write_text(root / SCORES_MD_PATH_V9_2, markdown)
    _write_text(root / DOC_PATH_V9_2, markdown)
    return manifest


def prepare_refined_ohlcv_trades_ml_frame_v9_2(dataset: pd.DataFrame) -> pd.DataFrame:
    frame = dataset[(dataset["label_valid_h1"] == True) & (dataset["warmup_row"] == False)].copy()  # noqa: E712
    return frame.reset_index(drop=True)


def validate_split_alignment_v9_2(dataset: pd.DataFrame, splits: pd.DataFrame) -> pd.DataFrame:
    missing_dataset = [column for column in SPLIT_COLUMNS_V9_1 if column not in dataset.columns]
    missing_splits = [column for column in SPLIT_COLUMNS_V9_1 if column not in splits.columns]
    if missing_dataset or missing_splits:
        raise ValueError(f"V9.2 split alignment missing dataset={missing_dataset}, missing_splits={missing_splits}")
    try:
        assert_frame_equal(
            dataset[SPLIT_COLUMNS_V9_1].reset_index(drop=True),
            splits[SPLIT_COLUMNS_V9_1].reset_index(drop=True),
            check_dtype=False,
        )
    except AssertionError as exc:
        raise ValueError("V9.2 dataset and split files are not aligned") from exc
    if dataset["walk_forward_group"].isna().any():
        raise ValueError("V9.2 dataset contains null walk_forward_group values")
    return dataset.copy()


def get_refined_ohlcv_trades_training_slices_v9_2(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {split: frame[frame["split"] == split].copy() for split in ["train", "validation", "test"]}


def build_refined_ohlcv_trades_model_scores_v9_2(
    dataset: pd.DataFrame,
    *,
    dataset_sha256: str,
    ml_run_id: str,
) -> pd.DataFrame:
    ml_frame = prepare_refined_ohlcv_trades_ml_frame_v9_2(dataset)
    slices = get_refined_ohlcv_trades_training_slices_v9_2(ml_frame)
    train = slices["train"]
    if train.empty:
        return pd.DataFrame(columns=ML_SCORE_COLUMNS_V9_2)

    score_frames: list[pd.DataFrame] = []
    train_features = train[ALLOWED_FEATURE_COLUMNS_V9_2]
    train_target = train[TARGET_NAME_V9_2].astype(str)
    score_features = ml_frame[ALLOWED_FEATURE_COLUMNS_V9_2]
    feature_columns_sha256 = get_feature_columns_sha256_v9_2()

    for model_name in MODEL_NAMES_V9_2:
        result = fit_predict_model(
            model_name,
            train_features,
            train_target,
            score_features,
        )
        scores = ml_frame[
            [
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
            ]
        ].copy()
        scores["ml_run_id"] = ml_run_id
        scores["model_name"] = model_name
        scores["target_name"] = TARGET_NAME_V9_2
        scores["dataset_sha256"] = dataset_sha256
        scores["feature_columns_sha256"] = feature_columns_sha256
        scores["ml_schema_version"] = ML_SCHEMA_VERSION_V9_2
        scores["target_value"] = ml_frame[TARGET_NAME_V9_2].astype(str).to_numpy()
        scores["research_predicted_class"] = result.predicted_class.to_numpy()
        scores["research_probability_down"] = result.probabilities["DOWN"].to_numpy()
        scores["research_probability_flat"] = result.probabilities["FLAT"].to_numpy()
        scores["research_probability_up"] = result.probabilities["UP"].to_numpy()
        scores["prediction_available_ts"] = ml_frame["decision_ts"].to_numpy()
        scores["row_valid_for_ml"] = True
        scores["ml_null_count"] = scores.isna().sum(axis=1).astype(int)
        scores["ml_error_count"] = 0
        score_frames.append(scores[ML_SCORE_COLUMNS_V9_2])

    return pd.concat(score_frames, ignore_index=True)


def build_refined_ohlcv_trades_ml_markdown_v9_2(manifest: dict[str, Any]) -> str:
    lines = [
        "# Rapport qualite - V9.2 ML offline raffine OHLCV + trades",
        "",
        "V9.2 entraine des baselines ML offline simples sur le dataset raffine V9.1.",
        "Ces sorties sont des scores de recherche descriptifs, non actionnables et sans usage de trading.",
        "",
        "## Fenetre",
        "",
        f"- Debut : `{manifest['input_dataset_manifest']['window_start']}`.",
        f"- Fin : `{manifest['input_dataset_manifest']['window_end']}`.",
        f"- Jours : `{manifest['input_dataset_manifest']['total_days']}`.",
        "",
        "## Cible et modeles",
        "",
        f"- Cible : `{manifest['target_name']}`.",
        f"- Modeles : `{', '.join(manifest['models'])}`.",
        f"- Features ML : `{manifest['feature_columns_count']}` features raffinees selectionnees.",
        "- `walk_forward_group` est conserve pour les metriques descriptives, jamais utilise comme feature.",
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
                f"  - groupes walk-forward : `{len(item['walk_forward_groups'])}`.",
            ]
        )
    lines.extend(
        [
            "",
            "## Interdits maintenus",
            "",
            "- V9.2 ne valide aucune strategie.",
            "- V9.2 ne produit aucun backtest.",
            "- V9.2 ne produit aucun signal de trading.",
            "- V9.2 ne produit aucun ordre.",
            "- V9.2 ne persiste aucun modele.",
            "- V9.2 n'autorise aucun paper live ni trading reel.",
            "",
            "Les metriques sont descriptives et non actionnables.",
        ]
    )
    return "\n".join(lines) + "\n"


def load_v9_1_dataset_manifest(root: Path = Path(".")) -> dict[str, Any]:
    return json.loads((root.resolve() / MANIFEST_PATH_V9_1).read_text(encoding="utf-8"))


def input_dataset_path(root: Path, timeframe: str, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest or load_v9_1_dataset_manifest(root)
    return root.resolve() / manifest["outputs"][timeframe]["path"]


def input_split_path(root: Path, timeframe: str, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest or load_v9_1_dataset_manifest(root)
    return root.resolve() / manifest["splits"][timeframe]["path"]


def score_output_path(root: Path, timeframe: str, window_start: str, window_end: str) -> Path:
    return get_refined_ohlcv_trades_ml_score_path_v9_2(root.resolve(), timeframe, window_start, window_end)


def _validate_dataset_layer(root: Path) -> None:
    result = validate_refined_ohlcv_trades_offline_supervised_dataset_v9_1(root)
    if not result["passed"]:
        raise RuntimeError(f"V9.1 validation failed before V9.2: {result['errors']}")


def _input_window(dataset_manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "window_start": dataset_manifest["input_features_manifest"]["window_start"],
        "window_end": dataset_manifest["input_features_manifest"]["window_end"],
        "total_days": dataset_manifest["input_features_manifest"]["total_days"],
    }


def _input_block(root: Path, path: Path, sha256: str, rows: int) -> dict[str, Any]:
    return {"path": path.relative_to(root).as_posix(), "sha256": sha256, "rows": int(rows)}


def _output_block(root: Path, path: Path, rows: int) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": int(rows),
        "format": "parquet",
    }


def _sanity_from_quality(quality: dict[str, Any]) -> dict[str, Any]:
    return {
        "train_rows": quality["train_rows"],
        "validation_rows": quality["validation_rows"],
        "test_rows": quality["test_rows"],
        "target_classes_seen_train": [],
        "target_classes_seen_validation": [],
        "target_classes_seen_test": [],
        "no_shuffle_confirmed": quality["no_shuffle_confirmed"],
        "forbidden_feature_columns_present": quality["forbidden_feature_columns_present"],
        "forbidden_output_columns_present": quality["forbidden_output_columns_present"],
    }


def _scores_report(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": manifest["version"],
        "ml_run_id": manifest["ml_run_id"],
        "outputs": manifest["outputs"],
        "metrics": manifest["metrics"],
        "walk_forward_metrics": manifest["walk_forward_metrics"],
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
