from __future__ import annotations

from typing import Any
import pandas as pd
from galapagos.research.paper_forward.frozen_filter import apply_frozen_filter
from galapagos.research.paper_forward.criteria_evaluator import evaluate_success_criteria

def compute_realized_metrics(selected_trades: pd.DataFrame) -> dict[str, Any]:
    """Compute performance metrics only if realized data is available."""
    
    if selected_trades.empty:
        return {
            "selected_count": 0,
            "mean_net_pnl_after_cost_pct": None,
            "profit_factor": None,
            "top_10_trades_contribution": None,
            "status": "NO_TRADES_SELECTED"
        }
    
    metrics = {"selected_count": len(selected_trades)}
    
    # Check for required columns
    pnl_col = "mean_net_pnl_after_cost_pct"
    
    if pnl_col in selected_trades.columns:
        metrics[pnl_col] = selected_trades[pnl_col].mean()
        
        # Compute Profit Factor if gross profit/loss columns exist
        # Or if we have a way to split PnL. Assuming for now we need pnl_col.
        pos_pnl = selected_trades[selected_trades[pnl_col] > 0][pnl_col].sum()
        neg_pnl = abs(selected_trades[selected_trades[pnl_col] < 0][pnl_col].sum())
        
        if neg_pnl > 0:
            metrics["profit_factor"] = pos_pnl / neg_pnl
        else:
            metrics["profit_factor"] = float('inf') if pos_pnl > 0 else None
            
        # Compute top 10 concentration
        sorted_pnl = selected_trades[pnl_col].sort_values(ascending=False)
        total_abs_pnl = selected_trades[pnl_col].abs().sum()
        if total_abs_pnl > 0:
            metrics["top_10_trades_contribution"] = sorted_pnl.head(10).abs().sum() / total_abs_pnl
        else:
            metrics["top_10_trades_contribution"] = None
            
        metrics["status"] = "METRICS_COMPUTED"
    else:
        metrics[pnl_col] = None
        metrics["profit_factor"] = None
        metrics["top_10_trades_contribution"] = None
        metrics["status"] = "METRICS_NOT_AVAILABLE"
        
    return metrics

def run_paper_forward_validation(
    protocol: dict[str, Any],
    criteria: dict[str, Any],
    predictions: pd.DataFrame,
    dataset: pd.DataFrame,
    intrabar: pd.DataFrame,
    reference_end_timestamp: str = "2026-05-06T20:35:00Z"
) -> dict[str, Any]:
    """Execute the paper-forward validation harness with zero placeholders."""
    
    ref_ts = pd.to_datetime(reference_end_timestamp).tz_localize(None)
    
    if predictions.empty:
        return {
            "validation_executed": False,
            "reason": "NO_PREDICTIONS_LOADED",
            "strategy_validated": False
        }

    definition = protocol.get("locked_filter_definition", {})
    if not definition.get("selection_logic") and definition.get("threshold") is None:
        return {
            "validation_executed": False,
            "reason": "FROZEN_FILTER_DEFINITION_INSUFFICIENT",
            "strategy_validated": False,
            "ready_for_reviewer": False,
            "holdout_executed": False,
            "no_real_trading": True,
            "criteria_status": "NOT_EVALUATED_FILTER_NOT_RECONSTRUCTABLE",
        }
        
    if 'timestamp' in predictions.columns and predictions['timestamp'].dt.tz is not None:
        predictions['timestamp'] = predictions['timestamp'].dt.tz_localize(None)
        
    oos_candidates = predictions[predictions['timestamp'] > ref_ts]
    
    if len(oos_candidates) == 0:
        return {
            "validation_executed": False,
            "reason": "NO_NEW_OUT_OF_SAMPLE_DATA",
            "strategy_validated": False,
            "ready_for_reviewer": False,
            "criteria_status": "NOT_EVALUATED_NO_OOS_DATA"
        }
    
    # 2. Apply Frozen Filter
    try:
        selected_trades = apply_frozen_filter(oos_candidates, protocol)
    except Exception as e:
        return {
            "validation_executed": False,
            "status": "FILTER_EXECUTION_FAILED",
            "error": str(e),
            "strategy_validated": False
        }

    if dataset.empty or intrabar.empty:
        selected_count = len(selected_trades)
        return {
            "validation_executed": False,
            "reason": "OOS_OUTCOMES_NOT_AVAILABLE",
            "selected_count": selected_count,
            "minimum_required_selected_trades": 60,
            "criteria_status": "INCONCLUSIVE_NEEDS_MORE_DATA" if selected_count < 60 else "NOT_EVALUATED_NO_OUTCOMES",
            "validation_passed": False,
            "strategy_validated": False,
            "ready_for_reviewer": False,
            "holdout_executed": False,
            "no_real_trading": True,
            "detailed_eval": {
                "status": "INCONCLUSIVE_NEEDS_MORE_DATA" if selected_count < 60 else "METRICS_NOT_AVAILABLE",
                "validation_passed": False,
            },
        }
    
    # 3. Calculate Real Metrics
    metrics = compute_realized_metrics(selected_trades)
    
    # 4. Evaluate against success criteria
    if metrics["selected_count"] < 60:
        eval_results = {
            "status": "INCONCLUSIVE_NEEDS_MORE_DATA",
            "validation_passed": False
        }
    else:
        eval_results = evaluate_success_criteria(metrics, criteria)
    
    return {
        "validation_executed": metrics["status"] == "METRICS_COMPUTED" or metrics["selected_count"] > 0,
        "true_out_of_sample": True,
        "selected_count": metrics["selected_count"],
        "minimum_required_selected_trades": 60,
        "criteria_status": eval_results["status"],
        "validation_passed": eval_results["validation_passed"],
        "strategy_validated": False,
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True,
        "reason": metrics["status"],
        "detailed_eval": eval_results if metrics["selected_count"] >= 60 else None
    }
