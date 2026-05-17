from __future__ import annotations

from galapagos.indicators.derivatives_indicators import summarize_derivatives
from galapagos.strategies.breakout import breakout_candidate
from galapagos.strategies.derivatives_filters import derivatives_filter
from galapagos.strategies.mean_reversion import mean_reversion_candidate
from galapagos.strategies.momentum import momentum_candidate
from galapagos.strategies.no_trade import no_trade_scenario


def build_scenarios(indicators: dict, regime: dict, derivatives: dict) -> list[dict]:
    derivatives_summary = summarize_derivatives(derivatives)
    scenarios = [
        no_trade_scenario("Baseline option when edge is unclear or data is degraded."),
        breakout_candidate(indicators, regime),
        momentum_candidate(regime),
        mean_reversion_candidate(regime),
        derivatives_filter(derivatives_summary),
        {"strategy": "volatility_regime", "regime": regime.get("volatility_regime")},
    ]
    return scenarios

