from typing import Any, Dict

class EndpointReview:
    def review_endpoints(self, v1_74_summary: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "endpoint_allowed": v1_74_summary.get("endpoint_allowed"),
            "endpoint_authentication_required": v1_74_summary.get("endpoint_authentication_required"),
            "authenticated_request_allowed": v1_74_summary.get("authenticated_request_allowed"),
            "secrets_used": v1_74_summary.get("secrets_used"),
            "endpoint_review_passed": (
                v1_74_summary.get("endpoint_allowed") is True and
                v1_74_summary.get("endpoint_authentication_required") is False and
                v1_74_summary.get("secrets_used") is False
            )
        }
