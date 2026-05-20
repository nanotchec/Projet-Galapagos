from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file
from galapagos.datasets.schemas import get_dataset_gold_path
from galapagos.ml.offline_baselines import fit_predict_model
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V2_8,
    ML_SCHEMA_VERSION,
    ML_SCORE_COLUMNS_V2_8,
    MODEL_NAMES,
    TARGET_NAME,
    get_feature_columns_sha256,
)


def prepare_ml_frame(dataset: pd.DataFrame) -> pd.DataFrame:
    frame = dataset[(dataset["label_valid_h1"] == True) & (dataset["warmup_row"] == False)].copy()  # noqa: E712
    return frame.reset_index(drop=True)


def get_training_slices(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {split: frame[frame["split"] == split].copy() for split in ["train", "validation", "test"]}


def build_model_scores(
    dataset: pd.DataFrame,
    *,
    dataset_sha256: str,
    ml_run_id: str,
) -> pd.DataFrame:
    ml_frame = prepare_ml_frame(dataset)
    slices = get_training_slices(ml_frame)
    train = slices["train"]
    if train.empty:
        return pd.DataFrame(columns=ML_SCORE_COLUMNS_V2_8)

    score_frames: list[pd.DataFrame] = []
    train_features = train[ALLOWED_FEATURE_COLUMNS_V2_8]
    train_target = train[TARGET_NAME].astype(str)
    feature_columns_sha256 = get_feature_columns_sha256()

    for model_name in MODEL_NAMES:
        for split_name, split_frame in slices.items():
            if split_frame.empty:
                continue
            result = fit_predict_model(
                model_name,
                train_features,
                train_target,
                split_frame[ALLOWED_FEATURE_COLUMNS_V2_8],
            )
            scores = split_frame[
                ["source", "venue", "market_type", "symbol", "timeframe", "event_ts", "close_ts", "decision_ts", "split"]
            ].copy()
            scores["ml_run_id"] = ml_run_id
            scores["model_name"] = model_name
            scores["target_name"] = TARGET_NAME
            scores["dataset_sha256"] = dataset_sha256
            scores["feature_columns_sha256"] = feature_columns_sha256
            scores["ml_schema_version"] = ML_SCHEMA_VERSION
            scores["target_value"] = split_frame[TARGET_NAME].astype(str).to_numpy()
            scores["research_predicted_class"] = result.predicted_class.to_numpy()
            scores["research_probability_down"] = result.probabilities["DOWN"].to_numpy()
            scores["research_probability_flat"] = result.probabilities["FLAT"].to_numpy()
            scores["research_probability_up"] = result.probabilities["UP"].to_numpy()
            scores["prediction_available_ts"] = split_frame["decision_ts"].to_numpy()
            scores["row_valid_for_ml"] = True
            scores["ml_null_count"] = scores.isna().sum(axis=1).astype(int)
            scores["ml_error_count"] = 0
            score_frames.append(scores[ML_SCORE_COLUMNS_V2_8])

    return pd.concat(score_frames, ignore_index=True)


def get_input_dataset_blocks(root, timeframes: list[str]) -> dict[str, dict[str, Any]]:
    blocks: dict[str, dict[str, Any]] = {}
    for timeframe in timeframes:
        path = get_dataset_gold_path(root, timeframe)
        frame = pd.read_parquet(path)
        blocks[timeframe] = {
            "path": str(path.relative_to(root)),
            "sha256": sha256_file(path),
            "rows": len(frame),
        }
    return blocks
