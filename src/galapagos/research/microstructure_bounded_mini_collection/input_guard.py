from typing import Any, Dict

class InputGuard:
    def validate_v1_76_1_state(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        
        # 1. Human Approval Checks
        if summary.get("human_approval_granted") is not True:
            issues.append("human_approval_granted must be true")
        if summary.get("approval_phrase_validated") is not True:
            issues.append("approval_phrase_validated must be true")
            
        # 2. Authorization Checks
        if summary.get("v1_77_bounded_mini_collection_authorized") is not True:
            issues.append("v1_77_bounded_mini_collection_authorized must be true")
        
        # 3. Limit Checks
        if summary.get("max_request_count") != 10:
            issues.append(f"max_request_count {summary.get('max_request_count')} != 10")
            
        # 4. Security Checks
        if summary.get("no_data_directory_writes") is not True:
            issues.append("no_data_directory_writes must be true")
        if summary.get("dataset_created") is not False:
            issues.append("dataset_created must be false")
        if summary.get("no_real_trading") is not True:
            issues.append("no_real_trading must be true")
            
        return {
            "v1_76_1_state_validated": len(issues) == 0,
            "issues": issues
        }
