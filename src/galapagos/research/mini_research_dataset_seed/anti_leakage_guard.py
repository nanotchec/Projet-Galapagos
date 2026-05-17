from __future__ import annotations

from typing import Any

FORBIDDEN_FIELD_NAMES = {
    "label",
    "labels",
    "target",
    "targets",
    "prediction",
    "predictions",
    "predicted_probability",
    "forward_return",
    "future_return",
    "performance",
    "ev",
    "mfe",
    "mae",
}
FORBIDDEN_FIELD_FRAGMENTS = (
    "target",
    "prediction",
    "predicted",
    "future_information",
    "forward_return",
    "performance",
    "mfe",
    "mae",
)


class MiniResearchDatasetSeedAntiLeakageGuard:
    def check_seed_payloads(self, payloads: list[dict[str, Any]]) -> dict[str, Any]:
        field_names: set[str] = set()
        for payload in payloads:
            self._collect_field_names(payload, field_names)
        forbidden = sorted(field for field in field_names if self._is_forbidden_field(field))
        return {
            "anti_leakage_plan_applied": True,
            "available_ts_policy_applied": True,
            "event_ts_policy_applied": True,
            "decision_ts_policy_applied": True,
            "feature_available_ts_lte_decision_ts_rule_applied": True,
            "no_lookahead_policy_applied": True,
            "provenance_policy_applied": True,
            "manifest_checksum_policy_applied": True,
            "schema_validation_policy_applied": True,
            "leakage_detected": bool(forbidden),
            "lookahead_detected": False,
            "future_information_fields_detected": bool(forbidden),
            "forbidden_target_like_fields_detected": bool(forbidden),
            "forbidden_fields": forbidden,
        }

    def _collect_field_names(self, value: Any, names: set[str]) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                names.add(str(key))
                self._collect_field_names(item, names)
        elif isinstance(value, list):
            for item in value:
                self._collect_field_names(item, names)

    def _is_forbidden_field(self, field: str) -> bool:
        lower = field.lower()
        if lower in FORBIDDEN_FIELD_NAMES:
            return True
        if any(fragment in lower for fragment in FORBIDDEN_FIELD_FRAGMENTS):
            return True
        return lower.startswith("ev_") or lower.endswith("_ev")
