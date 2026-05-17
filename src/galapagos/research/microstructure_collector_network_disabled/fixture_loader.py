from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict


class FixtureLoader:
    """Loads JSON fixtures for testing while enforcing safety guards (V1.55)."""

    ALLOWED_DIR = Path("tests/fixtures/microstructure")

    @classmethod
    def load_fixture(cls, filename: str) -> Any:
        """
        Loads a fixture by name.
        Enforces that the file is inside tests/fixtures/microstructure/
        and not in data/.
        """
        # Ensure the filename is just a filename, not a full path
        if "/" in filename or "\\" in filename:
             raise PermissionError(f"Path-like filename forbidden: {filename}")
             
        path = cls.ALLOWED_DIR / filename
        
        if not path.exists():
            raise FileNotFoundError(f"Fixture not found: {path}")
            
        # Extra safety check to prevent directory traversal or absolute paths
        if not str(path.resolve()).startswith(str(cls.ALLOWED_DIR.resolve())):
            raise PermissionError(f"Access denied to path: {path}")

        # Explicitly block data/ directory access even if it was somehow reachable
        if "data/" in str(path) or "data\\" in str(path):
            raise PermissionError(f"Forbidden access to data directory: {path}")

        with open(path, "r") as f:
            return json.load(f)

    @classmethod
    def list_fixtures(cls) -> list[str]:
        """Lists available fixtures in the allowed directory."""
        if not cls.ALLOWED_DIR.exists():
            return []
        return [f.name for f in cls.ALLOWED_DIR.glob("*.json")]
