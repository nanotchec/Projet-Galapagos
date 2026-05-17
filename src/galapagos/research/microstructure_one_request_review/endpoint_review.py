from typing import Any, Dict

class EndpointReview:
    def review_endpoint(self, v1_71_summary: Dict[str, Any]) -> Dict[str, Any]:
        res = {
            "previous_endpoint_allowed": v1_71_summary.get("endpoint_allowed") is True,
            "previous_endpoint_authentication_required": v1_71_summary.get("endpoint_authentication_required") is False,
            "previous_secrets_used": v1_71_summary.get("secrets_used") is False,
            "authenticated_request_allowed_check": v1_71_summary.get("authenticated_request_allowed") is False
        }
        res["endpoint_review_passed"] = all(res.values())
        return res
