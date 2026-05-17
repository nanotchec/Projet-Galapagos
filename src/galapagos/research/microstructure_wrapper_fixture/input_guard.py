from typing import Any, Dict
import json
from pathlib import Path

class InputGuard:
    def __init__(self, version: str):
        self.version = version

    def validate(self, reports: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that the planning phase is validated."""
        summary = reports.get("summary", {})
        
        passed = True
        issues = []
        
        # Check V1.63.2 validation
        if summary.get("version") != "V1.63.2":
            passed = False
            issues.append(f"Unexpected version in summary: {summary.get('version')}")
            
        if summary.get("final_verdict") != "MICROSTRUCTURE_NETWORK_DISABLED_WRAPPER_PLAN_READY":
            passed = False
            issues.append(f"Wrapper plan not ready: {summary.get('final_verdict')}")
            
        if summary.get("wrapper_plan_ready") is not True:
            passed = False
            issues.append("wrapper_plan_ready is not True")
            
        if summary.get("next_allowed_phase") != "network_disabled_wrapper_fixture_implementation":
            passed = False
            issues.append(f"Invalid next_allowed_phase: {summary.get('next_allowed_phase')}")
            
        # Infrastructure safety
        if summary.get("network_enabled") is not False:
            passed = False
            issues.append("network_enabled must be False")
            
        if summary.get("real_collection_approved") is not False:
            passed = False
            issues.append("real_collection_approved must be False")
            
        return {
            "version": self.version,
            "input_guard_passed": passed,
            "issues": issues,
            "status": "MICROSTRUCTURE_WRAPPER_FIXTURE_INPUT_GUARD_PASSED" if passed else "FAILED"
        }
