from __future__ import annotations


def size_from_risk(
    capital: float,
    risk_fraction: float,
    entry_price: float,
    stop_loss: float,
) -> float:
    risk_amount = capital * risk_fraction
    per_unit_risk = abs(entry_price - stop_loss)
    if risk_amount <= 0 or per_unit_risk <= 0:
        return 0.0
    return risk_amount / per_unit_risk
