from __future__ import annotations


class DiagnosticVerdict:
    """Provides the final assessment of the collector state."""

    @staticmethod
    def get_verdict(results: dict) -> str:
        """Determines the verdict based on test results."""
        if results.get("safety_guard_passed") and results.get("network_block_tests_passed"):
            return "MICROSTRUCTURE_COLLECTOR_NETWORK_DISABLED_READY"
        return "MICROSTRUCTURE_COLLECTOR_NETWORK_DISABLED_INCONCLUSIVE"
