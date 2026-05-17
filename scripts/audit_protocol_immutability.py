from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

def calculate_protocol_hash(protocol_path: str) -> str:
    """Calculate SHA256 hash of the protocol file."""
    p = Path(protocol_path)
    if not p.exists():
        return "FILE_MISSING"
    
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def run_protocol_immutability_audit(protocol_path: str, initial_hash: str) -> dict[str, Any]:
    """Verify if the protocol has changed since the start of the run."""
    current_hash = calculate_protocol_hash(protocol_path)
    
    mutated = initial_hash != current_hash
    
    return {
        "protocol_path": protocol_path,
        "protocol_hash_before": initial_hash,
        "protocol_hash_after": current_hash,
        "protocol_mutated_during_run": mutated,
        "status": "PROTOCOL_IMMUTABILITY_PASSED" if not mutated else "PROTOCOL_MUTATION_DETECTED"
    }
