import json
from pathlib import Path
from typing import Any, Dict, List

class InputGuard:
    def validate(self, summary_v1_64_2: Dict[str, Any]) -> bool:
        return (
            summary_v1_64_2.get("version") == "V1.64.2" and
            summary_v1_64_2.get("wrapper_fixture_implementation_passed") is True and
            summary_v1_64_2.get("network_enabled") is False
        )

class DataLoader:
    def load_fixtures(self, fixtures_dir: Path) -> List[Path]:
        return list(fixtures_dir.glob("*.json"))

class PreflightSkeletonSafetyPolicy:
    def get_policy(self) -> Dict[str, Any]:
        return {
            "network": "STRICTLY_DISABLED",
            "write": "STRICTLY_DISABLED",
            "read": "FIXTURES_ONLY",
            "execution": "NON_INTERACTIVE"
        }

class PreflightSkeletonManifestPreview:
    def get_preview_format(self) -> Dict[str, Any]:
        return {
            "fields": [
                "source", "symbol", "timeframe", "fixture_id", "request_window_preview",
                "expected_rows_preview", "available_ts_policy", "ingest_ts_policy",
                "checksum_policy", "no_lookahead_confirmation"
            ]
        }

class PreflightSkeletonTestPlan:
    def get_plan_v1_66(self) -> Dict[str, Any]:
        return {
            "tests": [
                "skeleton_fixture_execution",
                "network_blocking_verification",
                "write_blocking_verification",
                "manifest_preview_validation"
            ]
        }
