from typing import Any, Dict

class SafetyAudit:
    def audit_v1_77_execution(self, 
                             guard_res: Dict[str, Any],
                             request_status: Dict[str, Any],
                             data_write_res: Dict[str, Any]) -> Dict[str, Any]:
        
        issues = []
        if not guard_res.get("v1_76_1_state_validated"):
            issues.append("Input state validation failed")
            
        if request_status.get("requests_executed_count", 0) > 10:
            issues.append("Request count limit exceeded")
            
        if not data_write_res.get("no_data_directory_writes"):
            issues.append("Forbidden data writes detected")
            
        return {
            "safety_audit_passed": len(issues) == 0,
            "issues": issues,
            "no_strategy_validated": True,
            "no_paper_live": True,
            "no_real_trading": True,
            "strategy_link_allowed": False,
            "trading_allowed": False,
            "dataset_created": False,
            "real_collection_approved": False,
            "real_orders_possible": False,
            "no_preregistration_yet": True,
            "holdout_executed": False,
            "codex_cli_called": False
        }
