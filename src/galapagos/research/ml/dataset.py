"""ML dataset loading and preparation for research."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from galapagos.research.ml.feature_sets import build_ohlcv_basic_features
from galapagos.research.ml.targets import build_ml_targets


def load_ml_dataset(
    dataset_path: str | Path,
    *,
    cost_threshold: float = 0.003,
) -> tuple[pd.DataFrame | None, dict]:
    """Load research dataset and build ML targets + features.

    Returns (dataset_or_None, report_dict).
    """
    path = Path(dataset_path)
    if not path.exists():
        return None, {
            "status": "missing_dataset",
            "path": str(path),
            "error": f"Dataset not found: {path}",
        }
    try:
        raw = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001
        return None, {
            "status": "load_error",
            "path": str(path),
            "error": str(exc),
        }
    raw = raw.sort_values("timestamp").reset_index(drop=True)
    dataset = build_ohlcv_basic_features(raw)
    dataset = build_ml_targets(dataset, cost_threshold=cost_threshold)
    report = {
        "status": "loaded",
        "path": str(path),
        "rows": len(dataset),
        "columns": len(dataset.columns),
        "period_start": str(dataset["timestamp"].iloc[0]) if len(dataset) else None,
        "period_end": str(dataset["timestamp"].iloc[-1]) if len(dataset) else None,
    }
    return dataset, report
