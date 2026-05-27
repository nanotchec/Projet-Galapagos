from __future__ import annotations

from typing import Any

from galapagos.ml.refined_strict_walk_forward_metrics import (
    compute_refined_strict_walk_forward_aggregate_metrics_v9_3,
    compute_refined_strict_walk_forward_metrics_v9_3,
)


def compute_refined_volnorm_strict_walk_forward_metrics_v9_9(scores) -> dict[str, Any]:
    return compute_refined_strict_walk_forward_metrics_v9_3(scores)


def compute_refined_volnorm_strict_walk_forward_aggregate_metrics_v9_9(metrics: dict[str, Any]) -> dict[str, Any]:
    return compute_refined_strict_walk_forward_aggregate_metrics_v9_3(metrics)
