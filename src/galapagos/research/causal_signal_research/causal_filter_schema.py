from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import pandas as pd

@dataclass(frozen=True)
class CausalFilterMetadata:
    name: str
    family: str
    description: str
    parameters: dict[str, Any]
    is_causal: bool = True

class CausalFilter(ABC):
    """Base class for strictly causal filters."""
    
    @abstractmethod
    def get_metadata(self) -> CausalFilterMetadata:
        pass
        
    @abstractmethod
    def apply(self, df: pd.DataFrame) -> pd.Series:
        """Apply filter and return a boolean mask."""
        pass
