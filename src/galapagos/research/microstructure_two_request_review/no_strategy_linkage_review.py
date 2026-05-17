from typing import Any, Dict

class NoStrategyLinkageReview:
    def review_linkage(self, v1_74_summary: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "strategy_link_allowed": v1_74_summary.get("strategy_link_allowed"),
            "trading_allowed": v1_74_summary.get("trading_allowed"),
            "no_strategy_validated": v1_74_summary.get("no_strategy_validated"),
            "no_real_trading": v1_74_summary.get("no_real_trading"),
            "no_strategy_linkage_review_passed": (
                v1_74_summary.get("strategy_link_allowed") is False and
                v1_74_summary.get("trading_allowed") is False and
                v1_74_summary.get("no_strategy_validated") is True and
                v1_74_summary.get("no_real_trading") is True
            )
        }
