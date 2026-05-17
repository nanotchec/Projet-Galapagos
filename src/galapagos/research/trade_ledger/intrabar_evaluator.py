"""Intrabar evaluator for trade candidates."""
from __future__ import annotations

import pandas as pd

from galapagos.research.intrabar.execution_simulator import simulate_intrabar_exit
from galapagos.research.intrabar.mae_mfe import calculate_mae_mfe

from .schema import TradeCandidate, TradeSide, TradeSimulationResult


def evaluate_trade_candidates_intrabar(
    candidates: list[TradeCandidate],
    intrabar_df: pd.DataFrame,
    base_cost_pct: float = 0.003,
    cost_multiplier: float = 1.0,
) -> list[TradeSimulationResult]:
    """Evaluate candidates using intrabar data."""
    results = []

    # Standardize Intrabar DF
    if not intrabar_df.empty:
        intrabar_df = intrabar_df.copy()
        if "timestamp" in intrabar_df.columns:
            intrabar_df["timestamp"] = pd.to_datetime(intrabar_df["timestamp"])
            if intrabar_df["timestamp"].dt.tz is None:
                intrabar_df["timestamp"] = intrabar_df["timestamp"].dt.tz_localize("UTC")

    for cand in candidates:
        # 1. Get intrabar slice from entry to max holding time
        mask = (intrabar_df["timestamp"] >= cand.entry_time) & (
            intrabar_df["timestamp"] <= cand.max_holding_time
        )
        slice_df = intrabar_df[mask]

        # 2. Simulate Exit
        if cand.stop_loss is not None and cand.take_profit is not None:
            exit_sim = simulate_intrabar_exit(
                side=cand.side.value,
                entry_price=cand.entry_price,
                stop_loss=cand.stop_loss,
                take_profit=cand.take_profit,
                entry_time=cand.entry_time,
                max_exit_time=cand.max_holding_time,
                intrabar_slice=slice_df,
            )
        else:
            # Horizon only or missing SL/TP
            if slice_df.empty:
                exit_sim = {
                    "exit_reason": "fallback_no_intrabar",
                    "exit_price": 0.0,
                    "exit_time": cand.max_holding_time,
                    "bars_held_intrabar": 0,
                    "ambiguous": False,
                    "used_fallback": True,
                }
            else:
                last_row = slice_df.iloc[-1]
                exit_sim = {
                    "exit_reason": "horizon_timeout",
                    "exit_price": last_row["close"],
                    "exit_time": last_row["timestamp"],
                    "bars_held_intrabar": len(slice_df),
                    "ambiguous": False,
                    "used_fallback": False,
                }

        # 3. Calculate PnL
        exit_price = exit_sim["exit_price"]
        pnl_abs = 0.0
        pnl_pct = 0.0
        if exit_price > 0:
            if cand.side == TradeSide.LONG:
                pnl_abs = exit_price - cand.entry_price
            else:
                pnl_abs = cand.entry_price - exit_price
            pnl_pct = pnl_abs / cand.entry_price

        # 4. Costs
        cost_pct = base_cost_pct * cost_multiplier
        cost_abs = cost_pct * cand.entry_price

        pnl_after_cost_abs = pnl_abs - cost_abs
        pnl_after_cost_pct = pnl_pct - cost_pct

        # 5. MAE/MFE
        mae_mfe = calculate_mae_mfe(
            cand.side.value, cand.entry_price, slice_df, cand.stop_loss or 0.0
        )

        res = TradeSimulationResult(
            candidate_id=cand.candidate_id,
            signal_time=cand.signal_time,
            entry_time=cand.entry_time,
            side=cand.side,
            entry_price=cand.entry_price,
            exit_price=exit_price if exit_price > 0 else None,
            exit_time=exit_sim["exit_time"],
            exit_reason=exit_sim["exit_reason"],
            pnl_abs=pnl_abs,
            pnl_pct=pnl_pct,
            cost_proxy_abs=cost_abs,
            cost_proxy_pct=cost_pct,
            pnl_after_cost_abs=pnl_after_cost_abs,
            pnl_after_cost_pct=pnl_after_cost_pct,
            mfe_pct=mae_mfe["max_favorable_excursion_pct"],
            mae_pct=mae_mfe["max_adverse_excursion_pct"],
            bars_held_intrabar=exit_sim["bars_held_intrabar"],
            used_intrabar=not exit_sim["used_fallback"],
            used_fallback=exit_sim["used_fallback"],
            ambiguous=exit_sim["ambiguous"],
            coverage_pct=1.0 if not slice_df.empty else 0.0,
            simulation_status="complete" if not slice_df.empty else "missing_data",
            notes=f"Policy: {cand.policy_name}",
        )
        results.append(res)

    return results
