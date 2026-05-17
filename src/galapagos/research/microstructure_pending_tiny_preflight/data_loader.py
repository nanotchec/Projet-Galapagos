import json
from pathlib import Path
from typing import Any, Dict

class DataLoader:
    """
    Charge les rapports de recherche requis pour la revue V1.69.
    """
    def load_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(f"Missing required report: {path}")
        with open(path) as f:
            return json.load(f)
