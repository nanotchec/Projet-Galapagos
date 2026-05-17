import json
from pathlib import Path
from typing import Any, Dict

class PreflightSkeletonBuilder:
    """
    Squelette technique pour le futur collector preflight network-disabled.
    Strictement fixture-only et infrastructure-only.
    """
    def __init__(self, version: str):
        self.version = version
        self.network_enabled = False
        self.write_enabled = False
        self.fixture_only = True
        self.created = True
        self.executed = False

    def get_skeleton_info(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "preflight_skeleton_created": self.created,
            "preflight_skeleton_executed": self.executed,
            "network_enabled": self.network_enabled,
            "write_enabled": self.write_enabled,
            "fixture_only": self.fixture_only,
            "collector_type": "MICROSTRUCTURE_PREFLIGHT_NETWORK_DISABLED",
            "supported_modes": ["FIXTURE_ONLY", "DRY_RUN"],
            "forbidden_modes": ["REAL_COLLECTION", "LIVE_NETWORK"]
        }

class PreflightSkeletonContract:
    """
    Définit le contrat d'interface pour le futur collecteur.
    """
    def get_contract(self) -> Dict[str, Any]:
        return {
            "interface": "ICollectorPreflight",
            "capabilities": [
                "load_fixtures",
                "preview_manifest",
                "validate_schema",
                "detect_lookahead",
                "check_timestamp_causality"
            ],
            "security_gates": [
                "NETWORK_GATE_MANDATORY",
                "WRITE_GATE_MANDATORY",
                "FIXTURE_ONLY_MANDATORY"
            ],
            "outputs": [
                "manifest_preview.json",
                "safety_audit.json"
            ]
        }
