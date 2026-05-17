from __future__ import annotations

import pandas as pd

from galapagos.research.walk_forward_calibration.platt_calibrator import PlattCalibrator
from galapagos.research.walk_forward_calibration.split_builder import build_walk_forward_splits


def rebuild_calibrated_probabilities(
    df: pd.DataFrame, 
    method: str = "platt_scaling"
) -> pd.DataFrame:
    """
    Rebuild calibrated probabilities using walk-forward splits.
    """
    splits = build_walk_forward_splits(df)
    df = df.copy()
    # Default to raw if no split covers it
    df["predicted_probability_calibrated"] = df["predicted_probability"]
    
    for split in splits:
        train_df = df[(pd.to_datetime(df["timestamp"]) >= split.train_start) & 
                      (pd.to_datetime(df["timestamp"]) <= split.train_end)]
        test_df = df[(pd.to_datetime(df["timestamp"]) >= split.test_start) & 
                     (pd.to_datetime(df["timestamp"]) <= split.test_end)]
        
        if len(train_df) < 100 or len(test_df) == 0:
            continue
            
        y_train_true = train_df["actual_target"].values
        y_train_prob = train_df["predicted_probability"].values
        
        y_test_prob = test_df["predicted_probability"].values
        
        calibrator = PlattCalibrator() # Default to Platt as per V1.31.1 best_method_by_ece
        calibrator.fit(y_train_true, y_train_prob)
        
        y_test_cal = calibrator.predict(y_test_prob)
        
        df.loc[test_df.index, "predicted_probability_calibrated"] = y_test_cal
        
    return df
