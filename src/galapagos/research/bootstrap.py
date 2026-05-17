from __future__ import annotations

import numpy as np


def bootstrap_trade_pnl(
    trades: list[dict],
    n_bootstrap: int = 1000,
    seed: int | None = 42,
) -> dict:
    values = np.array([float(trade.get("net_pnl") or trade.get("pnl") or 0.0) for trade in trades])
    if len(values) == 0:
        return {"samples": [], "mean": 0.0, "p05": 0.0, "p95": 0.0}
    rng = np.random.default_rng(seed)
    samples = [
        float(rng.choice(values, size=len(values), replace=True).sum())
        for _ in range(int(n_bootstrap))
    ]
    return {
        "samples": samples,
        "mean": float(np.mean(samples)),
        "p05": float(np.percentile(samples, 5)),
        "p95": float(np.percentile(samples, 95)),
    }


def permutation_test_signal_vs_random(
    signal_returns: list[float],
    random_returns: list[float],
    n_permutations: int = 1000,
    seed: int | None = 42,
) -> dict:
    signal = np.array(signal_returns, dtype=float)
    random = np.array(random_returns, dtype=float)
    if len(signal) == 0 or len(random) == 0:
        return {"observed_delta": 0.0, "p_value": None, "permutations": 0}
    observed = float(signal.mean() - random.mean())
    combined = np.concatenate([signal, random])
    rng = np.random.default_rng(seed)
    extreme = 0
    for _ in range(int(n_permutations)):
        shuffled = rng.permutation(combined)
        delta = shuffled[: len(signal)].mean() - shuffled[len(signal) :].mean()
        if abs(delta) >= abs(observed):
            extreme += 1
    return {
        "observed_delta": observed,
        "p_value": (extreme + 1) / (int(n_permutations) + 1),
        "permutations": int(n_permutations),
    }

