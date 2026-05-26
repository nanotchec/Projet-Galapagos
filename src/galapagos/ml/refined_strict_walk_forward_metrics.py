from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.ml.strict_walk_forward_metrics import (
    compute_strict_walk_forward_aggregate_metrics_v8_7,
    compute_strict_walk_forward_metrics_v8_7,
)


def compute_refined_strict_walk_forward_metrics_v9_3(scores: pd.DataFrame) -> dict[str, Any]:
    return compute_strict_walk_forward_metrics_v8_7(scores)


def compute_refined_strict_walk_forward_aggregate_metrics_v9_3(metrics: dict[str, Any]) -> dict[str, Any]:
    return compute_strict_walk_forward_aggregate_metrics_v8_7(metrics)
