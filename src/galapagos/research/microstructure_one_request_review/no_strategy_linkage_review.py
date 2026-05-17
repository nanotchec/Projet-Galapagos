from typing import Any, Dict

class NoStrategyLinkageReview:
    def review_linkage(self, v1_71_summary: Dict[str, Any]) -> Dict[str, Any]:
        res = {
            "previous_strategy_link_allowed": v1_71_summary.get("strategy_link_allowed") is False,
            "previous_no_strategy_validated": v1_71_summary.get("no_strategy_validated") is True,
            "previous_trading_allowed": v1_71_summary.get("trading_allowed") is False,
            "previous_no_real_trading": v1_71_summary.get("no_real_trading") is True,
            "previous_real_orders_possible": v1_71_summary.get("real_orders_possible") is False
        }
        res["no_strategy_linkage_review_passed"] = all(res.values())
        return res
