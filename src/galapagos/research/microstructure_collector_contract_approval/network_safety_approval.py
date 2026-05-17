from __future__ import annotations

class NetworkSafetyVerifier:
    def __init__(self, metrics: dict[str, Any]):
        self.metrics = metrics

    def verify(self) -> dict[str, Any]:
        network_disabled = self.metrics.get("network_disabled", False)
        api_called = self.metrics.get("external_api_called", True)
        data_downloaded = self.metrics.get("external_data_downloaded", True)
        
        passed = network_disabled and not api_called and not data_downloaded
        
        return {
            "status": "PASSED" if passed else "FAILED",
            "network_disabled": network_disabled,
            "external_api_called": api_called,
            "external_data_downloaded": data_downloaded,
            "network_safety_approved": passed
        }
