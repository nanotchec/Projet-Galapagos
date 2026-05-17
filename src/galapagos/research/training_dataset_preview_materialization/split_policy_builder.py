from __future__ import annotations

from typing import Any


class SplitPolicyBuilder:
    def build(self) -> dict[str, Any]:
        return {
            "version": "V1.99",
            "split_policy_created": True,
            "purge_policy_defined": True,
            "embargo_policy_defined": True,
            "temporal_split_policy_defined": True,
            "no_random_shuffle_policy_defined": True,
            "random_shuffle_used": False,
            "split_policy": {
                "split_axis": "decision_ts",
                "shuffle": "forbidden",
                "purge": "required before any future research experiment",
                "embargo": "required around split boundaries",
            },
        }
