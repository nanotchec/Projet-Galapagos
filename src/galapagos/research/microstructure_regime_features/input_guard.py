class MicrostructureInputGuard:
    def __init__(self, config: dict):
        self.config = config

    def validate(self) -> dict:
        expected_versions = {
            "feature_ablation_base": "V1.45.1",
            "regime_data_quality_base": "V1.46.3",
            "canonical_base": "V1.37.2"
        }
        
        status = "MICROSTRUCTURE_INPUT_GUARD_PASSED"
        issues = []
        
        for key, expected in expected_versions.items():
            actual = self.config.get(key)
            if actual != expected:
                issues.append(f"Mismatch for {key}: expected {expected}, got {actual}")
                status = "MICROSTRUCTURE_INPUT_GUARD_FAILED"
        
        return {
            "status": status,
            "issues": issues,
            "config_validated": self.config
        }
