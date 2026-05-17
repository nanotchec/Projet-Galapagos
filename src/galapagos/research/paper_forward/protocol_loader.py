from __future__ import annotations

import json
from pathlib import Path
from typing import Any

def load_and_verify_protocol(protocol_path: str) -> dict[str, Any]:
    """Load V1.26.2 protocol and verify all locks."""
    p = Path(protocol_path)
    if not p.exists():
        return {"status": "PARTIAL_INPUTS_MISSING", "error": f"Protocol not found at {protocol_path}"}
    
    with open(p) as f:
        protocol = json.load(f)
    
    # Verify locks
    required_locks = [
        "protocol_locked",
        "filter_parameters_locked",
        "policy_parameters_locked",
        "selection_rules_locked",
        "metrics_locked",
        "data_sources_locked",
        "cost_model_locked",
        "baselines_locked",
        "no_hyperparameter_tuning",
        "no_reviewer_llm",
        "no_holdout",
        "no_real_trading"
    ]
    
    issues = []
    for lock in required_locks:
        if not protocol.get(lock):
            issues.append(f"Lock missing or false: {lock}")
    
    # V1.27.4 Hardening: Require Reference Protocol
    if not protocol.get("reference_protocol"):
        issues.append("Protocol is not marked as reference_protocol (V1.26.6+ required)")
    
    if protocol.get("protocol_version") not in ["v1.26.6", "v1.27.4"]: # Allow self-reference for tests
        if not protocol.get("reference_protocol"):
            issues.append(f"Protocol version {protocol.get('protocol_version')} is not an approved reference")

    if issues:
        return {
            "status": "PROTOCOL_CHECK_FAILED",
            "issues": issues,
            "protocol": protocol
        }
    
    return {
        "status": "PROTOCOL_CHECK_PASSED_REFERENCE_V1_26_6" if protocol.get("protocol_version") == "v1.26.6" else "PROTOCOL_CHECK_PASSED",
        "protocol": protocol
    }
