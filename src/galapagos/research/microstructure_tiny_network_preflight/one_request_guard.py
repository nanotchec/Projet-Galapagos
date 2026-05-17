from typing import Any, Dict

class OneRequestGuard:
    def __init__(self, max_allowed: int = 1):
        self.max_allowed = max_allowed
        self.request_count = 0

    def authorize_request(self) -> bool:
        if self.request_count < self.max_allowed:
            self.request_count += 1
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        return {
            "max_request_count": self.max_allowed,
            "requests_executed_count": self.request_count,
            "request_limit_enforced": True,
            "request_limit_exceeded": self.request_count > self.max_allowed
        }
