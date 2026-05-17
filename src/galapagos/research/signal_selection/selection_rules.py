"""Deterministic signal selection rules for V1.24."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SelectionRule:
    name: str
    family: str
    description: str
    apply: Callable[[pd.DataFrame], pd.Series]
    causal: bool = True
    used_columns: tuple[str, ...] = ()


def build_default_rules() -> list[SelectionRule]:
    """Return a bounded set of transparent non-optimized selection rules."""
    return [
        _rule("all_candidates", "baseline", "Tous les candidats.", _all, ()),
        _rule("no_trade", "baseline", "Aucun trade.", _none, ()),
        _rule(
            "prob_ge_0_55",
            "confidence",
            "Probabilité >= 0.55.",
            _prob(0.55),
            ("predicted_probability",),
        ),
        _rule(
            "prob_ge_0_60",
            "confidence",
            "Probabilité >= 0.60.",
            _prob(0.60),
            ("predicted_probability",),
        ),
        _rule(
            "prob_ge_0_65",
            "confidence",
            "Probabilité >= 0.65.",
            _prob(0.65),
            ("predicted_probability",),
        ),
        _rule(
            "top_25pct_probability",
            "confidence",
            "Top 25% probabilité.",
            _top("predicted_probability", 0.75),
            ("predicted_probability",),
        ),
        _rule(
            "top_10pct_probability",
            "confidence",
            "Top 10% probabilité.",
            _top("predicted_probability", 0.90),
            ("predicted_probability",),
        ),
        _rule(
            "expected_move_gt_cost",
            "cost",
            "Move attendu > coût.",
            _move_cost("gross_expected_move_pct", 1.0),
            ("gross_expected_move_pct", "cost_pct"),
        ),
        _rule(
            "expected_move_gt_1_5x_cost",
            "cost",
            "Move attendu > 1.5x coût.",
            _move_cost("gross_expected_move_pct", 1.5),
            ("gross_expected_move_pct", "cost_pct"),
        ),
        _rule(
            "expected_move_gt_2x_cost",
            "cost",
            "Move attendu > 2x coût.",
            _move_cost("gross_expected_move_pct", 2.0),
            ("gross_expected_move_pct", "cost_pct"),
        ),
        _rule(
            "mfe_proxy_gt_cost",
            "cost",
            "Proxy MFE > coût.",
            _move_cost("mfe_proxy_pct", 1.0),
            ("mfe_proxy_pct", "cost_pct"),
        ),
        _rule(
            "mfe_proxy_gt_1_5x_cost",
            "cost",
            "Proxy MFE > 1.5x coût.",
            _move_cost("mfe_proxy_pct", 1.5),
            ("mfe_proxy_pct", "cost_pct"),
        ),
        _rule(
            "mfe_proxy_gt_2x_cost",
            "cost",
            "Proxy MFE > 2x coût.",
            _move_cost("mfe_proxy_pct", 2.0),
            ("mfe_proxy_pct", "cost_pct"),
        ),
        _rule(
            "low_normal_volatility_only",
            "regime",
            "Volatilité basse/normale uniquement.",
            _vol_allowed({"low", "normal"}),
            ("volatility_regime",),
        ),
        _rule(
            "exclude_high_volatility",
            "regime",
            "Exclure high volatility.",
            _exclude_high_vol,
            ("volatility_regime",),
        ),
        _rule(
            "trend_aligned_only",
            "regime",
            "LONG seulement bull/range.",
            _trend_allowed({"bull", "range"}),
            ("trend_regime",),
        ),
        _rule(
            "bull_range_only",
            "regime",
            "Bull ou range uniquement.",
            _trend_allowed({"bull", "range"}),
            ("trend_regime",),
        ),
        _rule(
            "top25_probability_cost_viable",
            "combined",
            "Top 25% probabilité + coût viable.",
            _and(
                _top("predicted_probability", 0.75),
                _move_cost("gross_expected_move_pct", 1.0),
            ),
            ("predicted_probability", "gross_expected_move_pct", "cost_pct"),
        ),
        _rule(
            "top10_probability_cost_viable",
            "combined",
            "Top 10% probabilité + coût viable.",
            _and(
                _top("predicted_probability", 0.90),
                _move_cost("gross_expected_move_pct", 1.0),
            ),
            ("predicted_probability", "gross_expected_move_pct", "cost_pct"),
        ),
        _rule(
            "cost_viable_exclude_high_vol",
            "combined",
            "Coût viable + exclure high vol.",
            _and(_move_cost("gross_expected_move_pct", 1.0), _exclude_high_vol),
            ("gross_expected_move_pct", "cost_pct", "volatility_regime"),
        ),
        _rule(
            "prob60_bull_range",
            "combined",
            "Probabilité >=0.60 + bull/range.",
            _and(_prob(0.60), _trend_allowed({"bull", "range"})),
            ("predicted_probability", "trend_regime"),
        ),
        _rule(
            "low_frequency_strict_score",
            "frequency",
            "Meilleur score par semaine.",
            highest_score_per_period("7D"),
            ("timestamp", "predicted_probability"),
        ),
        _rule(
            "one_trade_per_day",
            "frequency",
            "Premier signal par jour.",
            cooldown("24h"),
            ("timestamp",),
        ),
        _rule(
            "one_trade_per_12h",
            "frequency",
            "Premier signal par 12h.",
            cooldown("12h"),
            ("timestamp",),
        ),
        _rule(
            "highest_score_per_day",
            "frequency",
            "Meilleur score par jour.",
            highest_score_per_period("1D"),
            ("timestamp", "predicted_probability"),
        ),
        _rule(
            "highest_score_per_week",
            "frequency",
            "Meilleur score par semaine.",
            highest_score_per_period("7D"),
            ("timestamp", "predicted_probability"),
        ),
    ]


def apply_signal_filter(df: pd.DataFrame, filter_name: str) -> pd.Index:
    """Helper to apply a named filter to a DataFrame."""
    rules = build_default_rules()
    for rule in rules:
        if rule.name == filter_name:
            mask = rule.apply(df)
            return df[mask].index
    raise ValueError(f"Unknown filter: {filter_name}")


def _rule(
    name: str,
    family: str,
    description: str,
    apply: Callable[[pd.DataFrame], pd.Series],
    used_columns: tuple[str, ...],
    *,
    causal: bool = True,
) -> SelectionRule:
    return SelectionRule(
        name=name,
        family=family,
        description=description,
        apply=apply,
        causal=causal,
        used_columns=used_columns,
    )


def _all(frame: pd.DataFrame) -> pd.Series:
    return pd.Series(True, index=frame.index)


def _none(frame: pd.DataFrame) -> pd.Series:
    return pd.Series(False, index=frame.index)


def _prob(threshold: float) -> Callable[[pd.DataFrame], pd.Series]:
    def apply(frame: pd.DataFrame) -> pd.Series:
        return _numeric(frame, "predicted_probability").fillna(0) >= threshold

    return apply


def _top(column: str, quantile: float) -> Callable[[pd.DataFrame], pd.Series]:
    def apply(frame: pd.DataFrame) -> pd.Series:
        values = _numeric(frame, column)
        if values.dropna().empty:
            return pd.Series(False, index=frame.index)
        return values >= values.quantile(quantile)

    return apply


def _move_cost(column: str, multiplier: float) -> Callable[[pd.DataFrame], pd.Series]:
    def apply(frame: pd.DataFrame) -> pd.Series:
        move = _numeric(frame, column).fillna(0.0)
        cost = _numeric(frame, "cost_pct").fillna(0.003)
        return move > multiplier * cost

    return apply


def _vol_allowed(allowed: set[str]) -> Callable[[pd.DataFrame], pd.Series]:
    def apply(frame: pd.DataFrame) -> pd.Series:
        if "volatility_regime" not in frame:
            return pd.Series(False, index=frame.index)
        return frame["volatility_regime"].isin(allowed)

    return apply


def _exclude_high_vol(frame: pd.DataFrame) -> pd.Series:
    if "volatility_regime" not in frame:
        return pd.Series(False, index=frame.index)
    return frame["volatility_regime"].fillna("unknown") != "high"


def _trend_allowed(allowed: set[str]) -> Callable[[pd.DataFrame], pd.Series]:
    def apply(frame: pd.DataFrame) -> pd.Series:
        if "trend_regime" not in frame:
            return pd.Series(False, index=frame.index)
        return frame["trend_regime"].isin(allowed)

    return apply


def _and(
    left: Callable[[pd.DataFrame], pd.Series],
    right: Callable[[pd.DataFrame], pd.Series],
) -> Callable[[pd.DataFrame], pd.Series]:
    def apply(frame: pd.DataFrame) -> pd.Series:
        return left(frame) & right(frame)

    return apply


def cooldown(duration: str) -> Callable[[pd.DataFrame], pd.Series]:
    def apply(frame: pd.DataFrame) -> pd.Series:
        if frame.empty:
            return pd.Series(False, index=frame.index)
        ordered = frame.sort_values("timestamp")
        keep = pd.Series(False, index=frame.index)
        last_kept = None
        delta = pd.Timedelta(duration)
        for idx, row in ordered.iterrows():
            ts = pd.Timestamp(row["timestamp"])
            if last_kept is None or ts - last_kept >= delta:
                keep.loc[idx] = True
                last_kept = ts
        return keep

    return apply


def highest_score_per_period(period: str) -> Callable[[pd.DataFrame], pd.Series]:
    def apply(frame: pd.DataFrame) -> pd.Series:
        if frame.empty:
            return pd.Series(False, index=frame.index)
        work = frame.copy()
        work["timestamp"] = pd.to_datetime(work["timestamp"], utc=True)
        work["period"] = work["timestamp"].dt.floor(period)
        score = _numeric(work, "predicted_probability").fillna(-1)
        work["_score"] = score
        idx = work.sort_values("_score", ascending=False).groupby("period").head(1).index
        keep = pd.Series(False, index=frame.index)
        keep.loc[idx] = True
        return keep

    return apply


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame:
        return pd.Series(float("nan"), index=frame.index)
    return pd.to_numeric(frame[column], errors="coerce")
