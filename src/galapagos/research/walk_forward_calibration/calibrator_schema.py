from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class Calibrator(ABC):
    @abstractmethod
    def fit(self, y_true: np.ndarray, y_prob: np.ndarray) -> Calibrator:
        pass

    @abstractmethod
    def predict(self, y_prob: np.ndarray) -> np.ndarray:
        pass

    @property
    @abstractmethod
    def method_name(self) -> str:
        pass
