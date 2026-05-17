import pandas as pd
from galapagos.research.ev_net_research.calibrated_probability_loader import rebuild_calibrated_probabilities
from galapagos.research.ev_net_research.payoff_estimator import estimate_causal_payoffs
from galapagos.research.ev_net_research.cost_proxy_model import apply_cost_proxy
from galapagos.research.ev_net_research.ev_proxy_builder import build_ev_proxies

def rebuild_ev_proxy_for_replay(df):
    """
    Rebuilds EV proxy columns on the provided dataframe.
    """
    if df.empty:
        return df, {"ev_proxy_rebuild_status": "EV_PROXY_REBUILD_FAILED", "reason": "empty_dataframe"}
        
    try:
        # 1. Calibrated Probability
        df = rebuild_calibrated_probabilities(df)
        
        # 2. Payoff Estimates
        df = estimate_causal_payoffs(df)
        
        # 3. Cost Proxy
        df = apply_cost_proxy(df)
        
        # 4. EV Proxy Build
        df = build_ev_proxies(df)
        
        status = "EV_PROXY_REBUILD_COMPLETE"
        
        rows_with_ev = len(df[df["ev_proxy_ready"] == True]) if "ev_proxy_ready" in df.columns else 0
        rows_without_ev = len(df) - rows_with_ev
        
        report = {
            "ev_proxy_rebuild_status": status,
            "calibrated_probability_rebuilt": "ev_calibrated_proxy" in df.columns,
            "cost_proxy_rebuilt": "cost_proxy" in df.columns,
            "payoff_estimates_rebuilt": "avg_win_past" in df.columns,
            "ev_calibrated_proxy_rebuilt": "ev_calibrated_proxy" in df.columns,
            "rows_with_ev_ready": rows_with_ev,
            "rows_without_ev_ready": rows_without_ev,
            "default_payoff_used": False,
            "fallback_used": False,
            "reconstruction_limitations": []
        }
        
        return df, report
        
    except Exception as e:
        return df, {
            "ev_proxy_rebuild_status": "EV_PROXY_REBUILD_FAILED",
            "reason": str(e)
        }
