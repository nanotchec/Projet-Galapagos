"""V1.83 explicit human approval gate for future tiny materialization."""

from .approval_gate import ApprovalGate, EXPECTED_APPROVAL_PHRASE
from .safety_guard import ApprovalGateSafetyGuard

__all__ = ["ApprovalGate", "ApprovalGateSafetyGuard", "EXPECTED_APPROVAL_PHRASE"]
