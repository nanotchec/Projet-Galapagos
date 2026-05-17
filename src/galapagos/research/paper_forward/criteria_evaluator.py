from __future__ import annotations

from typing import Any

def evaluate_success_criteria(metrics: dict[str, Any], criteria: dict[str, Any]) -> dict[str, Any]:
    """Evaluate OOS results against criteria, handling missing metrics."""
    
    results = {}
    
    # 1. Selected Count
    count = metrics.get("selected_count", 0)
    results["selected_count"] = {
        "status": "PASSED" if count >= 60 else "FAILED",
        "observed": count,
        "required": ">= 60"
    }
    
    # Helper for evaluating numeric criteria
    def eval_metric(name, observed, threshold, op=">"):
        if observed is None:
            return {"status": "NOT_EVALUATED", "observed": "N/A", "required": f"{op} {threshold}", "reason": "metric_missing"}
        
        passed = False
        if op == ">": passed = observed > threshold
        elif op == ">=": passed = observed >= threshold
        elif op == "<": passed = observed < threshold
        
        return {
            "status": "PASSED" if passed else "FAILED",
            "observed": observed,
            "required": f"{op} {threshold}"
        }

    # 2. Mean Net PnL
    results["mean_net_pnl"] = eval_metric("mean_net_pnl", metrics.get("mean_net_pnl_after_cost_pct"), 0, ">")
    
    # 3. Profit Factor
    results["profit_factor"] = eval_metric("profit_factor", metrics.get("profit_factor"), 1.2, ">")
    
    # 4. Concentration
    results["concentration"] = eval_metric("concentration", metrics.get("top_10_trades_contribution"), 0.50, "<")
    
    # Overall status logic
    if count < 60:
        status = "INCONCLUSIVE_NEEDS_MORE_DATA"
        all_passed = False
    else:
        # Check if any evaluated metric failed
        failed = any(r["status"] == "FAILED" for r in results.values())
        missing = any(r["status"] == "NOT_EVALUATED" for r in results.values())
        
        if failed:
            status = "CRITERIA_FAILED"
            all_passed = False
        elif missing:
            status = "NOT_EVALUATED_MISSING_METRICS"
            all_passed = False
        else:
            status = "CRITERIA_PASSED"
            all_passed = True
            
    return {
        "status": status,
        "validation_passed": all_passed,
        "detailed_results": results
    }
