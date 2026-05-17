from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression

from galapagos.research.walk_forward_calibration.calibrator_schema import Calibrator


class PlattCalibrator(Calibrator):
    def __init__(self):
        self.model = LogisticRegression(penalty=None, solver='lbfgs')

    def fit(self, y_true: np.ndarray, y_prob: np.ndarray) -> PlattCalibrator:
        # Platt scaling is basically a logistic regression on the logit of the probabilities
        # or directly on the probabilities if they are well-behaved.
        # We'll use the probabilities directly as a single feature.
        X = y_prob.reshape(-1, 1)
        self.model.fit(X, y_true)
        return self

    def predict(self, y_prob: np.ndarray) -> np.ndarray:
        X = y_prob.reshape(-1, 1)
        return self.model.predict_proba(X)[:, 1]

    @property
    def method_name(self) -> str:
        return "platt_scaling"
