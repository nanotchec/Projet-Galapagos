from typing import Any

import pandas as pd

from galapagos.research.walk_forward_calibration.bin_calibrator import BinCalibrator
from galapagos.research.walk_forward_calibration.calibration_metrics import get_calibration_metrics
from galapagos.research.walk_forward_calibration.isotonic_calibrator import IsotonicCalibrator
from galapagos.research.walk_forward_calibration.leakage_audit import audit_walk_forward_leakage
from galapagos.research.walk_forward_calibration.platt_calibrator import PlattCalibrator
from galapagos.research.walk_forward_calibration.reliability_report import (
    generate_reliability_bins_report,
)
from galapagos.research.walk_forward_calibration.split_builder import CalibrationSplit


def run_walk_forward_calibration_suite(
    df: pd.DataFrame, 
    splits: list[CalibrationSplit]
) -> dict[str, Any]:
    """
    Run walk-forward calibration across all splits and methods.
    """
    methods = [
        PlattCalibrator(),
        IsotonicCalibrator(),
        BinCalibrator(n_bins=10)
    ]
    
    all_results = []
    leakage_reports = []
    all_reliability_bins = []
    
    for split in splits:
        train_df = df[(pd.to_datetime(df["timestamp"]) >= split.train_start) & 
                      (pd.to_datetime(df["timestamp"]) <= split.train_end)]
        test_df = df[(pd.to_datetime(df["timestamp"]) >= split.test_start) & 
                     (pd.to_datetime(df["timestamp"]) <= split.test_end)]
        
        # Leakage audit
        leak_rep = audit_walk_forward_leakage(train_df, test_df, ["predicted_probability"])
        leak_rep["split_id"] = split.split_id
        leakage_reports.append(leak_rep)
        
        y_train_true = train_df["actual_target"].values
        y_train_prob = train_df["predicted_probability"].values
        
        y_test_true = test_df["actual_target"].values
        y_test_prob = test_df["predicted_probability"].values
        
        # Baseline: Raw Probabilities
        baseline_metrics = get_calibration_metrics(y_test_true, y_test_prob)
        baseline_metrics.update({
            "split_id": split.split_id,
            "method": "raw_probability",
            "sample_count": len(test_df)
        })
        all_results.append(baseline_metrics)
        
        # Reliability bins for raw
        all_reliability_bins.extend(
            generate_reliability_bins_report(
                y_test_true, y_test_prob, split.split_id, "raw_probability"
            )
        )
        
        for method in methods:
            # Fit on train
            method.fit(y_train_true, y_train_prob)
            
            # Predict on test
            y_test_cal = method.predict(y_test_prob)
            
            # Evaluate on test
            metrics = get_calibration_metrics(y_test_true, y_test_cal)
            metrics.update({
                "split_id": split.split_id,
                "method": method.method_name,
                "sample_count": len(test_df)
            })
            all_results.append(metrics)
            
            # Reliability bins for calibrated
            all_reliability_bins.extend(
                generate_reliability_bins_report(
                    y_test_true, y_test_cal, split.split_id, method.method_name
                )
            )
            
    return {
        "results": all_results,
        "leakage_reports": leakage_reports,
        "reliability_bins": all_reliability_bins
    }
