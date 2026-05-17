from typing import Any, Dict

class TwoRequestGuard:
    def __init__(self, max_requests: int = 2):
        self.max_requests = max_requests
        self.counter = 0

    def authorize_request(self) -> bool:
        if self.counter < self.max_requests:
            self.counter += 1
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        return {
            "two_request_limit_enforced": True,
            "max_request_count": self.max_requests,
            "requests_executed_count": self.counter,
            "limit_respected": self.counter <= self.max_requests
        }
