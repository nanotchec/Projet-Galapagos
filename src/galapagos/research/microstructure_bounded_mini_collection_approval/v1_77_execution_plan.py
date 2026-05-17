from typing import Any, Dict

class V177ExecutionPlan:
    def create_plan(self, authorized: bool) -> Dict[str, Any]:
        return {
            "v1_77_execution_plan_ready": authorized,
            "operation_type": "BOUNDED_MINI_COLLECTION",
            "constraints": {
                "max_requests": 10,
                "reports_only": True,
                "no_data_writes": True,
                "no_trading": True
            },
            "status": "AUTHORIZED_FOR_V1_77" if authorized else "AWAITING_APPROVAL"
        }
