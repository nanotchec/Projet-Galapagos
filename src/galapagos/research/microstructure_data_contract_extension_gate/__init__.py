"""V1.86 explicit human approval gate for future V1.87 tiny extension."""

from .approval_gate import AUTHORIZED_SCOPE, EXPECTED_APPROVAL_PHRASE, ExtensionApprovalGate
from .safety_guard import ExtensionGateSafetyGuard

__all__ = [
    "AUTHORIZED_SCOPE",
    "EXPECTED_APPROVAL_PHRASE",
    "ExtensionApprovalGate",
    "ExtensionGateSafetyGuard",
]
