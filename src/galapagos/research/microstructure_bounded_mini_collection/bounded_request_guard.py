from typing import Any, Dict

class BoundedRequestGuard:
    def __init__(self, max_requests: int = 10):
        self.max_requests = max_requests
        self.request_counter = 0

    def can_request(self) -> bool:
        return self.request_counter < self.max_requests

    def increment(self):
        self.request_counter += 1

    def get_status(self) -> Dict[str, Any]:
        return {
            "max_request_count": self.max_requests,
            "requests_executed_count": self.request_counter,
            "bounded_request_limit_enforced": True,
            "limit_reached": self.request_counter >= self.max_requests
        }
