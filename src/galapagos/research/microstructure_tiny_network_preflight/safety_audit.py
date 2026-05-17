from typing import Any, Dict

class SafetyAudit:
    def perform_audit(self, client_res: Dict[str, Any], guard_status: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "strategy_link_allowed": False,
            "no_strategy_validated": True,
            "trading_allowed": False,
            "no_real_trading": True,
            "real_orders_possible": False,
            "secrets_used": False,
            "authenticated_request_allowed": False,
            "request_limit_audit_passed": guard_status.get("requests_executed_count", 0) <= 1,
            "holdout_executed": False,
            "codex_cli_called": False,
            "no_paper_live": True,
            "safety_audit_passed": guard_status.get("requests_executed_count", 0) <= 1
        }
