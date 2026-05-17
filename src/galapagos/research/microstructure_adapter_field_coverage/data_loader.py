from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any

class DataLoader:
    def __init__(self, paths: Dict[str, str]):
        self.paths = paths

    def load_all(self) -> Dict[str, Any]:
        data = {}
        for key, path in self.paths.items():
            if Path(path).exists():
                with open(path) as f:
                    data[key] = json.load(f)
            else:
                data[key] = None
        return data
