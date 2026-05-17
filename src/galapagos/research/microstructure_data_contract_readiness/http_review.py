from typing import Any, Dict, List

class HTTPReview:
    def review_v1_79(self, summary: Dict[str, Any], resp_summary: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        
        success_count = summary.get("successful_response_count", 0)
        status_codes = summary.get("response_status_codes", [])
        
        if success_count != 10:
            issues.append(f"Unexpected success count: {success_count} (expected 10)")
            
        if len(status_codes) != 10:
            issues.append(f"Unexpected status codes count: {len(status_codes)} (expected 10)")
            
        if any(c != 200 for c in status_codes):
            issues.append("Found non-200 status codes in success list")
            
        if summary.get("response_status_codes_none_present") is not False:
            issues.append("Found None in response status codes")
            
        if summary.get("response_status_codes_all_present") is not True:
            issues.append("Status codes not all present")
            
        return {
            "v1_79_http_review_passed": len(issues) == 0,
            "issues": issues,
            "v1_79_successful_response_count": success_count,
            "v1_79_response_status_codes": status_codes,
            "v1_79_response_status_codes_count": len(status_codes),
            "v1_79_response_status_codes_none_present": summary.get("response_status_codes_none_present"),
            "v1_79_response_status_codes_all_present": summary.get("response_status_codes_all_present"),
            "v1_79_response_status_codes_all_success": summary.get("response_status_codes_all_success")
        }
