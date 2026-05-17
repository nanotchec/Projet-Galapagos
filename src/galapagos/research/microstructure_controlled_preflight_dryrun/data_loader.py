import json
from pathlib import Path

def load_baseline(version: str):
    p = Path("reports/PROJECT_STATE.json")
    if not p.exists():
        raise FileNotFoundError(f"Missing PROJECT_STATE.json for baseline check")
    with open(p, "r") as f:
        return json.load(f)

def load_fixtures():
    fixtures_dir = Path("tests/fixtures/microstructure")
    fixtures = {}
    for p in fixtures_dir.glob("*.json"):
        with open(p, "r") as f:
            fixtures[p.name] = json.load(f)
    return fixtures
