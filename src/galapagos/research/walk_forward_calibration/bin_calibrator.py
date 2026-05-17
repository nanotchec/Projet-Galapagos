from __future__ import annotations

import numpy as np

from galapagos.research.walk_forward_calibration.calibrator_schema import Calibrator


class BinCalibrator(Calibrator):
    def __init__(self, n_bins: int = 10):
        self.n_bins = n_bins
        self.bin_mappings = {}

    def fit(self, y_true: np.ndarray, y_prob: np.ndarray) -> BinCalibrator:
        bins = np.linspace(0, 1, self.n_bins + 1)
        for i in range(self.n_bins):
            mask = (y_prob >= bins[i]) & (y_prob < bins[i+1])
            if i == self.n_bins - 1:
                mask = (y_prob >= bins[i]) & (y_prob <= bins[i+1])
            
            if np.any(mask):
                self.bin_mappings[i] = np.mean(y_true[mask])
            else:
                # Fallback to bin center if no samples
                self.bin_mappings[i] = (bins[i] + bins[i+1]) / 2.0
        return self

    def predict(self, y_prob: np.ndarray) -> np.ndarray:
        bins = np.linspace(0, 1, self.n_bins + 1)
        y_cal = np.zeros_like(y_prob)
        for i in range(self.n_bins):
            mask = (y_prob >= bins[i]) & (y_prob < bins[i+1])
            if i == self.n_bins - 1:
                mask = (y_prob >= bins[i]) & (y_prob <= bins[i+1])
            y_cal[mask] = self.bin_mappings[i]
        return y_cal

    @property
    def method_name(self) -> str:
        return "bin_calibration"
