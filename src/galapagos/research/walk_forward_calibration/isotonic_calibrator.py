from __future__ import annotations

import numpy as np
from sklearn.isotonic import IsotonicRegression

from galapagos.research.walk_forward_calibration.calibrator_schema import Calibrator


class IsotonicCalibrator(Calibrator):
    def __init__(self):
        self.model = IsotonicRegression(out_of_bounds='clip')

    def fit(self, y_true: np.ndarray, y_prob: np.ndarray) -> IsotonicCalibrator:
        self.model.fit(y_prob, y_true)
        return self

    def predict(self, y_prob: np.ndarray) -> np.ndarray:
        return self.model.predict(y_prob)

    @property
    def method_name(self) -> str:
        return "isotonic_regression"
