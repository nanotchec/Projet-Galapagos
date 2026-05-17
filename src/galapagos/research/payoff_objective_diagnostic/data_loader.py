"""Load inputs for the payoff-objective failure diagnostic."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.research.payoff_aware_objective.data_loader import build_analysis_frame
from galapagos.research.payoff_aware_objective.target_builder import build_targets


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _normalize_timestamp(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, utc=True)


def _looks_mock_or_scratch(path: Path) -> bool:
    lowered = str(path).lower()
    return any(token in lowered for token in ["mock", "scratch", "/dev/null", ".gemini/antigravity/brain"])


def load_failure_diagnostic_inputs(
    *,
    predictions_path: str | Path,
    dataset_path: str | Path,
    intrabar_path: str | Path,
    payoff_summary_path: str | Path,
    payoff_walk_forward_path: str | Path,
    payoff_baseline_path: str | Path,
    canonical_summary_path: str | Path,
    diagnostic_summary_path: str | Path,
) -> dict[str, Any]:
    """Load real inputs and the V1.40.1 payoff-objective artefacts."""
    paths = [Path(p) for p in [predictions_path, dataset_path, intrabar_path, payoff_summary_path, payoff_walk_forward_path, payoff_baseline_path, canonical_summary_path, diagnostic_summary_path]]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required payoff diagnostic inputs: {missing}")
    if any(_looks_mock_or_scratch(path) for path in paths[:3]):
        raise ValueError("Mock or scratch path detected in payoff diagnostic inputs")

    predictions = pd.read_parquet(predictions_path)
    dataset = pd.read_parquet(dataset_path)
    intrabar = pd.read_parquet(intrabar_path)

    for frame in [predictions, dataset]:
        frame["timestamp"] = _normalize_timestamp(frame["timestamp"])
    if "available_timestamp" in dataset.columns:
        dataset["available_timestamp"] = _normalize_timestamp(dataset["available_timestamp"])
    if "timestamp" in intrabar.columns:
        intrabar["timestamp"] = _normalize_timestamp(intrabar["timestamp"])

    analysis_frame = build_analysis_frame(predictions, dataset)
    labeled_frame, target_report = build_targets(analysis_frame)
    analysis_ready = labeled_frame[labeled_frame["analysis_ready"]].copy()
    analysis_ready["timestamp"] = pd.to_datetime(analysis_ready["timestamp"], utc=True)
    analysis_ready = analysis_ready.sort_values("timestamp").reset_index(drop=True)

    return {
        "predictions": predictions,
        "dataset": dataset,
        "intrabar": intrabar,
        "paths": {
            "predictions_path": str(predictions_path),
            "dataset_path": str(dataset_path),
            "intrabar_path": str(intrabar_path),
            "payoff_summary_path": str(payoff_summary_path),
            "payoff_walk_forward_path": str(payoff_walk_forward_path),
            "payoff_baseline_path": str(payoff_baseline_path),
            "canonical_summary_path": str(canonical_summary_path),
            "diagnostic_summary_path": str(diagnostic_summary_path),
        },
        "analysis_frame": analysis_ready,
        "payoff_summary": _load_json(payoff_summary_path),
        "payoff_walk_forward": _load_json(payoff_walk_forward_path),
        "payoff_baseline": _load_json(payoff_baseline_path),
        "canonical_summary": _load_json(canonical_summary_path),
        "diagnostic_summary": _load_json(diagnostic_summary_path),
        "target_report": target_report,
    }
