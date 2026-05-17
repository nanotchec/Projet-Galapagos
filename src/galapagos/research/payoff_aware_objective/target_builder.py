"""Target construction entrypoint for payoff-aware objective research."""
from __future__ import annotations

from typing import Any

import pandas as pd

from .payoff_labeler import build_payoff_labels


def build_targets(frame: pd.DataFrame, *, default_cost_pct: float = 0.001) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build label-only targets used for exploratory objective training."""
    labeled, report = build_payoff_labels(frame, default_cost_pct=default_cost_pct)
    report["target_builder_status"] = "PAYOFF_OBJECTIVE_TARGET_BUILDER_COMPLETE"
    report["labels_only"] = True
    return labeled, report

