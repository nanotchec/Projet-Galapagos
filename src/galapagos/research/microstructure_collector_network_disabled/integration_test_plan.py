from __future__ import annotations
from typing import List


class IntegrationTestPlan:
    """Documents the testing strategy for the network-disabled collector."""

    def __init__(self, version: str):
        self.version = version

    def get_test_cases(self) -> List[dict]:
        """Returns the list of test cases for V1.54."""
        return [
            {
                "id": "TC_001",
                "description": "Verify network guard blocks raw socket calls",
                "type": "SAFETY"
            },
            {
                "id": "TC_002",
                "description": "Verify adapter build_requests produces valid kline params",
                "type": "FUNCTIONAL"
            },
            {
                "id": "TC_003",
                "description": "Verify dry_run_executor doesn't execute any requests",
                "type": "SAFETY"
            },
            {
                "id": "TC_004",
                "description": "Verify manifest validator schema checks",
                "type": "VAL_MANIFEST"
            }
        ]
