from __future__ import annotations
from typing import List, Dict, Any
from .config_schema import RequestPlan
from .network_guard import NetworkGuard


class DryRunExecutor:
    """Simulates the execution of a request plan without network access."""

    def __init__(self, plan: RequestPlan):
        self.plan = plan
        self.results: List[Dict[str, Any]] = []

    def execute(self) -> List[Dict[str, Any]]:
        """Simulates execution by iterating over requests."""
        if not self.plan.config.dry_run_only:
            raise RuntimeError("DryRunExecutor can only be used with dry_run_only=True")

        with NetworkGuard(enabled=self.plan.config.network_disabled):
            for i, req in enumerate(self.plan.requests):
                # In V1.54, we only record that the request was "planned"
                # and we don't actually call any execution method.
                self.results.append({
                    "request_index": i,
                    "request_summary": f"{req['method']} {req['endpoint']}",
                    "status": "PLANNED_BUT_NOT_EXECUTED",
                    "network_disabled": self.plan.config.network_disabled,
                    "simulated": True
                })
        
        return self.results
