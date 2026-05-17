from __future__ import annotations

from typing import Any

PROVIDERS = [
    {
        "provider": "Binance public",
        "monthly_cost": "free",
        "funding_history": "partial",
        "open_interest_history": "partial",
        "liquidations_history": "limited_or_unavailable",
        "long_short_ratio": "history_limited",
        "taker_buy_sell": "history_limited",
        "basis_premium": "snapshot_or_partial",
        "btc_etf_flows": "no",
        "multi_exchange_aggregate": "no",
        "historical_depth": "medium",
        "granularity": "good",
        "api_usability": "good",
        "rate_limits": "public limits",
        "free_tier": True,
        "notes": (
            "Best free starting point, but not enough for full liquidation/"
            "multi-exchange research."
        ),
    },
    {
        "provider": "Bybit public",
        "monthly_cost": "free",
        "funding_history": "partial",
        "open_interest_history": "partial",
        "liquidations_history": "limited_or_unavailable",
        "long_short_ratio": "not_supported_here",
        "taker_buy_sell": "not_supported_here",
        "basis_premium": "snapshot_or_partial",
        "btc_etf_flows": "no",
        "multi_exchange_aggregate": "no",
        "historical_depth": "medium",
        "granularity": "good",
        "api_usability": "good",
        "rate_limits": "public limits",
        "free_tier": True,
        "notes": "Complements Binance for funding and OI, but public breadth is limited.",
    },
    {
        "provider": "CoinGlass",
        "monthly_cost": "requires manual check",
        "funding_history": "yes",
        "open_interest_history": "yes",
        "liquidations_history": "yes",
        "long_short_ratio": "yes",
        "taker_buy_sell": "unknown",
        "basis_premium": "yes",
        "btc_etf_flows": "yes",
        "multi_exchange_aggregate": "yes",
        "historical_depth": "provider_plan_dependent",
        "granularity": "provider_plan_dependent",
        "api_usability": "unknown_until_tested",
        "rate_limits": "plan dependent",
        "free_tier": False,
        "notes": "Watchlist only; purchase needs a public-data signal candidate first.",
    },
    {
        "provider": "CryptoQuant",
        "monthly_cost": "requires manual check",
        "funding_history": "yes",
        "open_interest_history": "yes",
        "liquidations_history": "yes",
        "long_short_ratio": "yes",
        "taker_buy_sell": "unknown",
        "basis_premium": "unknown",
        "btc_etf_flows": "unknown",
        "multi_exchange_aggregate": "yes",
        "historical_depth": "deep",
        "granularity": "provider_plan_dependent",
        "api_usability": "requires manual check",
        "rate_limits": "plan dependent",
        "free_tier": False,
        "notes": "Potentially strong on on-chain/exchange derivatives; price must be checked.",
    },
    {
        "provider": "Kaiko",
        "monthly_cost": "requires manual check",
        "funding_history": "yes",
        "open_interest_history": "yes",
        "liquidations_history": "unknown",
        "long_short_ratio": "unknown",
        "taker_buy_sell": "yes",
        "basis_premium": "yes",
        "btc_etf_flows": "unknown",
        "multi_exchange_aggregate": "yes",
        "historical_depth": "deep",
        "granularity": "high",
        "api_usability": "professional",
        "rate_limits": "contract dependent",
        "free_tier": False,
        "notes": "Institutional quality, likely overkill until signal is proven.",
    },
    {
        "provider": "Glassnode",
        "monthly_cost": "requires manual check",
        "funding_history": "partial",
        "open_interest_history": "partial",
        "liquidations_history": "unknown",
        "long_short_ratio": "unknown",
        "taker_buy_sell": "unknown",
        "basis_premium": "partial",
        "btc_etf_flows": "unknown",
        "multi_exchange_aggregate": "partial",
        "historical_depth": "deep",
        "granularity": "daily_to_intraday_plan_dependent",
        "api_usability": "good",
        "rate_limits": "plan dependent",
        "free_tier": "limited",
        "notes": "More useful if macro/on-chain context becomes central.",
    },
    {
        "provider": "CCData",
        "monthly_cost": "requires manual check",
        "funding_history": "yes",
        "open_interest_history": "yes",
        "liquidations_history": "unknown",
        "long_short_ratio": "unknown",
        "taker_buy_sell": "yes",
        "basis_premium": "yes",
        "btc_etf_flows": "unknown",
        "multi_exchange_aggregate": "yes",
        "historical_depth": "deep",
        "granularity": "good",
        "api_usability": "professional",
        "rate_limits": "plan dependent",
        "free_tier": "limited",
        "notes": "Candidate if exchange-normalized market data becomes priority.",
    },
    {
        "provider": "Amberdata",
        "monthly_cost": "requires manual check",
        "funding_history": "yes",
        "open_interest_history": "yes",
        "liquidations_history": "yes",
        "long_short_ratio": "unknown",
        "taker_buy_sell": "yes",
        "basis_premium": "yes",
        "btc_etf_flows": "unknown",
        "multi_exchange_aggregate": "yes",
        "historical_depth": "deep",
        "granularity": "high",
        "api_usability": "professional",
        "rate_limits": "contract dependent",
        "free_tier": False,
        "notes": "Likely expensive; only justify after public signal evidence.",
    },
    {
        "provider": "Laevitas",
        "monthly_cost": "requires manual check",
        "funding_history": "yes",
        "open_interest_history": "yes",
        "liquidations_history": "yes",
        "long_short_ratio": "unknown",
        "taker_buy_sell": "unknown",
        "basis_premium": "yes",
        "btc_etf_flows": "no",
        "multi_exchange_aggregate": "yes",
        "historical_depth": "deep",
        "granularity": "good",
        "api_usability": "requires manual check",
        "rate_limits": "plan dependent",
        "free_tier": False,
        "notes": "Derivatives-focused watchlist provider.",
    },
    {
        "provider": "Coinalyze",
        "monthly_cost": "requires manual check",
        "funding_history": "yes",
        "open_interest_history": "yes",
        "liquidations_history": "yes",
        "long_short_ratio": "yes",
        "taker_buy_sell": "unknown",
        "basis_premium": "partial",
        "btc_etf_flows": "no",
        "multi_exchange_aggregate": "yes",
        "historical_depth": "good",
        "granularity": "good",
        "api_usability": "requires manual check",
        "rate_limits": "plan dependent",
        "free_tier": "limited",
        "notes": "Potential lower-cost alternative to evaluate manually.",
    },
]


def build_provider_decision_matrix() -> dict[str, Any]:
    providers = [_with_priority(row) for row in PROVIDERS]
    return {
        "version": "V1.14",
        "providers": providers,
        "decision_rule": (
            "Ne pas acheter tant que les donnees publiques ne montrent pas un signal derive "
            "prometteur ou que les liquidations/OI multi-exchange deviennent "
            "explicitement critiques."
        ),
        "verdicts": [
            "DO_NOT_BUY_PROVIDER_YET",
            "COINGLASS_WATCHLIST",
            "NEED_MANUAL_PRICE_CHECK",
            "PUBLIC_DATA_ENOUGH_FOR_NOW",
        ],
    }


def _with_priority(row: dict[str, Any]) -> dict[str, Any]:
    score = 0
    for key in [
        "funding_history",
        "open_interest_history",
        "liquidations_history",
        "basis_premium",
        "multi_exchange_aggregate",
    ]:
        value = row.get(key)
        if value == "yes":
            score += 2
        elif value in {"partial", "provider_plan_dependent"}:
            score += 1
    if row.get("monthly_cost") == "free":
        score += 2
    elif row.get("monthly_cost") == "requires manual check":
        score -= 1
    row = dict(row)
    row["priority_score"] = score
    row["suitability_for_btc_4h_research"] = (
        "high" if score >= 7 else ("medium" if score >= 4 else "low")
    )
    row["suitability_for_intrabar_execution_research"] = (
        "medium" if row.get("granularity") in {"good", "high"} else "low"
    )
    return row
