"""V1.89 consolidation readiness pack and approval gate."""

from .approval_gate import (
    APPROVAL_PHRASE_EXPECTED,
    AUTHORIZED_FUTURE_SCOPE,
    evaluate_approval_phrase,
)
from .consolidation_designer import design_consolidation_contract_v2, validate_consolidation_design
from .physical_auditor import ConsolidationPhysicalAuditor
from .safety_guard import ConsolidationReadinessSafetyGuard

__all__ = [
    "APPROVAL_PHRASE_EXPECTED",
    "AUTHORIZED_FUTURE_SCOPE",
    "ConsolidationPhysicalAuditor",
    "ConsolidationReadinessSafetyGuard",
    "design_consolidation_contract_v2",
    "evaluate_approval_phrase",
    "validate_consolidation_design",
]
