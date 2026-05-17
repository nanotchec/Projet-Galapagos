from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.research.trade_ledger.intrabar_evaluator import evaluate_trade_candidates_intrabar
from galapagos.research.trade_ledger.ledger_builder import build_trade_candidates
from galapagos.research.trade_ledger.signal_loader import load_ml_signals


def reconstruct_evaluation(
    predictions_path: str,
    ohlcv_4h: pd.DataFrame,
    intrabar_df: pd.DataFrame,
    policy_names: list[str]
) -> dict[str, dict[str, Any]]:
    """Re-evaluate trades in memory to get raw results for analysis."""
    signals_df, _ = load_ml_signals(predictions_path)
    
    raw_results = {}
    for p_name in policy_names:
        candidates = build_trade_candidates(signals_df, ohlcv_4h, p_name)
        results = evaluate_trade_candidates_intrabar(candidates, intrabar_df)
        raw_results[p_name] = {
            "results": results,
            "candidates": candidates
        }
        
    return raw_results

def results_to_df(results: list[TradeSimulationResult], candidates: list[TradeCandidate]) -> pd.DataFrame:
    """Convert simulation results to a DataFrame, joining with candidates for metadata."""
    cand_map = {c.candidate_id: c for c in candidates}
    
    data = []
    for r in results:
        c = cand_map.get(r.candidate_id)
        data.append({
            "timestamp": r.signal_time,
            "side": r.side,
            "entry_price": r.entry_price,
            "exit_price": r.exit_price,
            "gross_pnl_pct": r.pnl_pct,
            "net_pnl_pct": r.pnl_after_cost_pct,
            "exit_reason": r.exit_reason,
            "simulation_status": r.simulation_status,
            "duration": (r.exit_time - r.entry_time).total_seconds() if r.exit_time and r.entry_time else 0,
            "mae_pct": r.mae_pct,
            "mfe_pct": r.mfe_pct,
            "confidence": c.confidence if c and c.confidence is not None else 0.5
        })
    return pd.DataFrame(data)
