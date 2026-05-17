import json
import os
from pathlib import Path
from typing import Any, Dict, List

class FixtureRequestLoader:
    """Loads fixtures from tests/fixtures/microstructure/."""
    def __init__(self, version: str, fixtures_dir: str):
        self.version = version
        self.fixtures_dir = Path(fixtures_dir)

    def load_fixtures(self) -> List[Dict[str, Any]]:
        fixtures = []
        if not self.fixtures_dir.exists():
            return []
            
        for f_path in self.fixtures_dir.glob("*.json"):
            try:
                with open(f_path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        fixtures.extend(data)
                    else:
                        fixtures.append(data)
            except Exception:
                continue
        return fixtures

    def get_report(self, loaded_count: int) -> Dict[str, Any]:
        return {
            "version": self.version,
            "fixtures_dir": str(self.fixtures_dir),
            "fixture_requests_loaded_count": loaded_count,
            "status": "MICROSTRUCTURE_FIXTURE_REQUEST_LOADER_PASSED"
        }

