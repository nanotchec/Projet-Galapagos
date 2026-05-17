from __future__ import annotations

import math

import numpy as np
import pandas as pd


def benchmark_cash(data: pd.DataFrame) -> dict:
    return {
        "name": "cash",
        "return": 0.0,
        "max_drawdown": 0.0,
        "volatility": 0.0,
        "exposure_time": 0.0,
    }


def benchmark_buy_and_hold(data: pd.DataFrame) -> dict:
    close = data["close"].astype(float)
    returns = close.pct_change().fillna(0.0)
    return _metrics("buy_and_hold", returns, exposure=1.0)


def benchmark_trend_filter(data: pd.DataFrame, ma_window: int = 200) -> dict:
    close = data["close"].astype(float)
    ma = close.rolling(min(ma_window, max(2, len(close) // 2))).mean()
    exposure = (close > ma).shift(1)
    exposure = exposure.where(exposure.notna(), False).astype(float)
    returns = close.pct_change().fillna(0.0) * exposure
    return _metrics("trend_filter", returns, exposure=float(exposure.mean()))


def benchmark_volatility_target(data: pd.DataFrame, target_vol: float = 0.15) -> dict:
    close = data["close"].astype(float)
    returns = close.pct_change().fillna(0.0)
    realized = returns.rolling(24).std().replace(0, np.nan) * math.sqrt(365 * 6)
    exposure = (target_vol / realized).clip(0.0, 1.0).shift(1).fillna(0.0)
    return _metrics("volatility_target", returns * exposure, exposure=float(exposure.mean()))


def run_benchmarks(data: pd.DataFrame) -> dict:
    return {
        "cash": benchmark_cash(data),
        "buy_and_hold": benchmark_buy_and_hold(data),
        "trend_filter": benchmark_trend_filter(data),
        "volatility_target": benchmark_volatility_target(data),
    }


def _metrics(name: str, returns: pd.Series, exposure: float) -> dict:
    cumulative = (1.0 + returns).cumprod()
    total_return = float(cumulative.iloc[-1] - 1.0) if len(cumulative) else 0.0
    drawdown = cumulative / cumulative.cummax() - 1.0
    volatility = float(returns.std() * math.sqrt(365 * 6)) if len(returns) > 1 else 0.0
    downside = returns[returns < 0].std()
    sharpe = float(returns.mean() / returns.std() * math.sqrt(365 * 6)) if returns.std() else 0.0
    sortino = float(returns.mean() / downside * math.sqrt(365 * 6)) if downside else 0.0
    max_drawdown = float(drawdown.min()) if len(drawdown) else 0.0
    calmar = total_return / abs(max_drawdown) if max_drawdown else 0.0
    return {
        "name": name,
        "return": total_return,
        "max_drawdown": max_drawdown,
        "volatility": volatility,
        "sharpe_approx": sharpe,
        "sortino_approx": sortino,
        "calmar_approx": calmar,
        "exposure_time": exposure,
        "return_per_exposure": total_return / exposure if exposure else 0.0,
    }
