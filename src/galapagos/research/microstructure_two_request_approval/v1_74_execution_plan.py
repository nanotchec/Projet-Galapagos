from typing import Any, Dict

class V174ExecutionPlan:
    def build_plan(self, authorized: bool) -> Dict[str, Any]:
        if not authorized:
            return {
                "plan_status": "PENDING_AUTHORIZATION",
                "v1_74_steps": [],
                "can_proceed": False
            }
            
        return {
            "plan_status": "READY_FOR_V1_74",
            "v1_74_steps": [
                "load_two_request_approval",
                "validate_approval_proof",
                "execute_request_1_btcusdt_1m",
                "execute_request_2_ethusdt_1m",
                "generate_reports_only",
                "safety_audit_zero_data_writes"
            ],
            "max_request_count": 2,
            "can_proceed": True
        }
