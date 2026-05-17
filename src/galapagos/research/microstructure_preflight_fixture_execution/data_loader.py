import json
from pathlib import Path
from typing import Any, Dict, List

class DataLoader:
    """
    Charge les fixtures locales pour le preflight execution.
    """
    def load_fixtures(self, fixtures_dir: Path) -> List[Dict[str, Any]]:
        fixtures = []
        for p in fixtures_dir.glob("*.json"):
            with open(p) as f:
                fixtures.append(json.load(f))
        return fixtures
