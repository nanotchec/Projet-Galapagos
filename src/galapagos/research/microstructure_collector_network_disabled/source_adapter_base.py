from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Any
from .config_schema import CollectorConfig


class SourceAdapter(ABC):
    """Abstract base class for data source adapters."""

    def __init__(self, config: CollectorConfig):
        self.config = config

    @abstractmethod
    def build_requests(self) -> List[dict]:
        """Build the list of request parameters to be executed."""
        pass

    @abstractmethod
    def validate_request(self, request: dict) -> bool:
        """Check if a request is valid according to source constraints."""
        pass

    def execute_request(self, request: dict) -> Any:
        """
        Execute the request.
        In V1.54, this MUST NOT be called if network_disabled is True.
        """
        if self.config.network_disabled:
            raise RuntimeError("Cannot execute request: network is disabled.")
        
        # Real implementation would go here in future versions (V1.55+)
        raise NotImplementedError("Real execution not implemented in V1.54.")
