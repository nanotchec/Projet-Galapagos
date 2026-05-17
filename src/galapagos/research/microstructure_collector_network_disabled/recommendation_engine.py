from __future__ import annotations


class RecommendationEngine:
    """Logic for determining the next steps for the collector."""

    @staticmethod
    def get_recommendation(verdict: str) -> str:
        """Returns the recommended next step."""
        if verdict == "MICROSTRUCTURE_COLLECTOR_NETWORK_DISABLED_READY":
            return "prepare controlled collector dry-run with local fixture data only"
        return "refine adapter stubs before collection approval"
