from __future__ import annotations

import numpy as np
import pandas as pd

from galapagos.labels.redesigned_5y_label_factory_v9_64 import (
    binary_volnorm_label_v9_64,
    future_log_return_v9_64,
    safe_quantile_v9_64,
    ternary_quantile_label_v9_64,
)


def test_v9_64_future_return_uses_future_bars_only() -> None:
    returns = np.array([1.0, 2.0, 3.0, 4.0])
    result = future_log_return_v9_64(returns, 2)
    assert result[0] == 5.0
    assert result[1] == 7.0
    assert np.isnan(result[2])


def test_v9_64_binary_volnorm_excludes_neutral_zone() -> None:
    labels = binary_volnorm_label_v9_64(np.array([-0.5, 0.0, 0.5]), np.array([0.1, 0.1, 0.1]), np.array([True, True, True]))
    assert labels.tolist() == [-1, pd.NA, 1]


def test_v9_64_quantile_thresholds_are_numeric() -> None:
    assert safe_quantile_v9_64(np.array([1.0, 2.0, 3.0]), 0.5) == 2.0
    labels = ternary_quantile_label_v9_64(np.array([1.0, 2.0, 3.0]), 1.5, 2.5, np.array([True, True, True]))
    assert labels.tolist() == [-1, 0, 1]
