from __future__ import annotations

from typing import Any


def decompose_losses(diags: dict[str, Any]) -> dict[str, Any]:
    gap = diags.get("ev_realization_gap", {})
    payoff = diags.get("payoff_degradation", {})
    calibration = diags.get("calibration_degradation", {})
    cost = diags.get("cost_drag_diagnostic", {})
    probability = diags.get("probability_distribution_shift", {})
    ev_shift = diags.get("ev_distribution_shift", {})
    feature = diags.get("feature_distribution_shift", {})
    regime = diags.get("regime_diagnostic", {})
    concentration = diags.get("trade_concentration", {})

    primary = "EV_PROXY_OVERESTIMATES_2026"
    if gap.get("ev_realization_gap_status") == "EV_PROXY_OVERESTIMATES_2026":
        primary = "EV_PROXY_OVERESTIMATES_2026"
    elif payoff.get("payoff_degradation_status") == "PAYOFF_ASYMMETRY_DEGRADED_2026":
        primary = "PAYOFF_ASYMMETRY_DEGRADED_2026"
    elif regime.get("regime_degradation_status") == "REGIME_EXPLAINS_DEGRADATION":
        primary = "REGIME_EXPLAINS_DEGRADATION"
    elif cost.get("cost_drag_status") == "COSTS_TURN_EDGE_NEGATIVE":
        primary = "COSTS_TURN_EDGE_NEGATIVE"

    secondary = []
    for label, payload in [
        ("PAYOFF_ASYMMETRY_DEGRADED_2026", payoff),
        ("CALIBRATION_STABLE_BUT_PAYOFF_DEGRADED", calibration),
        ("COST_DRAG_NOT_PRIMARY_DRIVER", cost),
        ("PROBABILITY_DISTRIBUTION_SHIFT_DETECTED", probability),
        ("EV_DISTRIBUTION_SHIFT_DETECTED", ev_shift),
        ("FEATURE_DISTRIBUTION_SHIFT_DETECTED", feature),
        ("REGIME_NOT_PRIMARY_DRIVER", regime),
        ("LOSSES_CONCENTRATED_IN_OUTLIERS", concentration),
    ]:
        status = next((v for k, v in payload.items() if k.endswith("_status")), None)
        if status and status != primary and status not in secondary:
            secondary.append(status)
    return {
        "primary_driver": primary,
        "secondary_drivers": secondary[:5],
        "loss_decomposition_status": "LOSS_DECOMPOSITION_COMPLETED" if primary else "LOSS_DECOMPOSITION_INCONCLUSIVE",
    }
