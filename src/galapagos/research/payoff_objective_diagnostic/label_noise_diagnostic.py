"""Label noise diagnostic for payoff-objective failure."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def analyze_label_noise(analysis_frame: pd.DataFrame) -> dict[str, Any]:
    frame = analysis_frame.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    pre = frame[frame["timestamp"].dt.year < 2026].copy()
    recent = frame[frame["timestamp"].dt.year == 2026].copy()
    threshold = 0.001
    def _stats(sub: pd.DataFrame) -> dict[str, float]:
        net = pd.to_numeric(sub.get("net_return_label"), errors="coerce").fillna(0.0)
        gross = pd.to_numeric(sub.get("forward_return_12bar"), errors="coerce").fillna(0.0)
        sign_flip = float((np.sign(net) != np.sign(gross)).mean()) if len(sub) else 0.0
        return {
            "count": int(len(sub)),
            "mean_abs_return": float(net.abs().mean()) if len(net) else 0.0,
            "std_return": float(net.std()) if len(net) else 0.0,
            "near_zero_rate": float((net.abs() <= threshold).mean()) if len(net) else 0.0,
            "sign_flip_rate": sign_flip,
            "signal_to_noise_proxy": float(net.abs().mean() / (net.std() + 1e-9)) if len(net) else 0.0,
        }
    pre_stats = _stats(pre)
    recent_stats = _stats(recent)
    if recent_stats["near_zero_rate"] > 0.35 or recent_stats["signal_to_noise_proxy"] < pre_stats["signal_to_noise_proxy"] * 0.9:
        status = "PAYOFF_LABELS_HIGH_NOISE"
    elif recent_stats["near_zero_rate"] > 0.25:
        status = "PAYOFF_LABELS_MODERATE_NOISE"
    else:
        status = "PAYOFF_LABEL_NOISE_DIAGNOSTIC_LIMITED"
    return {
        "label_noise_status": status,
        "pre_2026": pre_stats,
        "2026": recent_stats,
        "threshold": threshold,
    }

