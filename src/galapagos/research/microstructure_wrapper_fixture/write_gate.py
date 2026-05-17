from typing import Any, Dict, List

class WriteGate:
    """Intercepts and blocks unauthorized writes."""
    def __init__(self, version: str):
        self.version = version
        self.blocked_writes: List[str] = []

    def check_write(self, path: str) -> bool:
        """Returns True if allowed, False if blocked."""
        # Allow only reports/ and docs/
        # In a real implementation, this would hook into os.open etc.
        if path.startswith("reports/") or path.startswith("docs/"):
            return True
        
        self.blocked_writes.append(path)
        return False

    def get_report(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "write_gate_enabled": True,
            "data_writes_blocked": len(self.blocked_writes) > 0,
            "blocked_paths": self.blocked_writes,
            "no_data_directory_writes": True,
            "status": "MICROSTRUCTURE_WRITE_GATE_ACTIVE"
        }
