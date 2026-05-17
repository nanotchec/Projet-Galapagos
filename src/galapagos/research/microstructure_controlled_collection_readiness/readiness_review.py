from typing import Any, Dict

class ReadinessReview:
    """
    Audite le plan de readiness V1.66.
    """
    def audit(self, plan_v1_66: Dict[str, Any]) -> Dict[str, Any]:
        required_checks = [
            "Secrets audit (no API keys in code)",
            "Explicit human approval required",
            "Network disabled by default policy",
            "Tiny sample collection first (1 record)",
            "No data directory writes until review",
            "Rollback/Cleanup plan validation",
            "Audit logs verification"
        ]
        checks_found = plan_v1_66.get("mandatory_checks_before_collection", [])
        passed = all(check in checks_found for check in required_checks)
        
        return {
            "controlled_collection_readiness_review_passed": passed,
            "readiness_review_source": "PLAN_V1_66_AUDIT",
            "mandatory_checks_validated": passed
        }

class NetworkActivationRiskAudit:
    """
    Identifie les risques avant activation réseau future.
    """
    def audit(self) -> Dict[str, Any]:
        risks = [
            "Accidental recursive requests (rate limit / cost)",
            "Sensitive information leakage in headers",
            "Unintended write of real market data to research data/ dir",
            "Insecure certificate validation on some systems",
            "Network timeout handling during synchronization"
        ]
        return {
            "network_activation_risk_audit_completed": True,
            "network_activation_risks": risks,
            "network_activation_risk_count": len(risks),
            "network_enabled": False,
            "network_activation_protection": "MAXIMUM_GATES_ACTIVE"
        }
