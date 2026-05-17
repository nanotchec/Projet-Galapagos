from typing import Any, Dict

class PreflightAuthorizationRecord:
    def create_record(self, approval_granted: bool) -> Dict[str, Any]:
        """
        Creates a record of the authorization status.
        """
        return {
            "approval_record_created": True,
            "v1_71_network_preflight_authorized": approval_granted
        }
