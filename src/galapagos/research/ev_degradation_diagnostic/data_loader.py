from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.research.calibration_ev.prediction_frame_builder import build_prediction_frames
from galapagos.research.ev_net_research.canonical_ev_feature_rebuilder import rebuild_canonical_ev_features


def _reject_non_real_path(path: str) -> None:
    normalized = path.replace("\\", "/").lower()
    forbidden = ["/dev/null", "tmp", "scratch", ".gemini/antigravity/brain", "mock", "placeholder"]
    if any(token in normalized for token in forbidden):
        raise ValueError(f"Rejected non-real path: {path}")


def load_ev_degradation_inputs(
    *,
    predictions_path: str,
    dataset_path: str,
    intrabar_path: str,
    ev_summary_path: str,
    ev_evaluation_path: str,
    ev_feature_rebuild_path: str,
    canonical_summary_path: str,
) -> dict[str, Any]:
    for path in [predictions_path, dataset_path, intrabar_path, ev_summary_path, ev_evaluation_path, ev_feature_rebuild_path, canonical_summary_path]:
        _reject_non_real_path(path)
    paths = [Path(p) for p in [predictions_path, dataset_path, intrabar_path, ev_summary_path, ev_evaluation_path, ev_feature_rebuild_path, canonical_summary_path]]
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required real input files: {missing}")

    pred_df = pd.read_parquet(predictions_path)
    ds_df = pd.read_parquet(dataset_path)
    pred_df["timestamp"] = pd.to_datetime(pred_df["timestamp"], utc=True).dt.tz_convert(None)
    ds_df["timestamp"] = pd.to_datetime(ds_df["timestamp"], utc=True).dt.tz_convert(None)
    common_cols = [c for c in ds_df.columns if c in pred_df.columns and c != "timestamp"]
    merged = pd.merge(pred_df, ds_df[[c for c in ds_df.columns if c not in common_cols]], on="timestamp", how="inner")

    input_guard = _load_json(Path(canonical_summary_path))
    ev_summary = _load_json(Path(ev_summary_path))
    ev_eval = _load_json(Path(ev_evaluation_path))
    ev_rebuild = _load_json(Path(ev_feature_rebuild_path))

    rebuilt, rebuild_stats = rebuild_canonical_ev_features(merged)
    selection_frame, outcome_frame, integrity = build_prediction_frames(rebuilt)
    return {
        "predictions": pred_df,
        "dataset": ds_df,
        "merged": merged,
        "rebuilt": rebuilt,
        "selection_frame": selection_frame,
        "outcome_frame": outcome_frame,
        "integrity": integrity,
        "input_guard": input_guard,
        "ev_summary": ev_summary,
        "ev_evaluation": ev_eval,
        "ev_feature_rebuild": ev_rebuild,
        "rebuild_stats": rebuild_stats,
    }


def _load_json(path: Path) -> dict[str, Any]:
    import json

    return json.loads(path.read_text(encoding="utf-8"))
