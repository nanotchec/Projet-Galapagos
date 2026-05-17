import pytest
import pandas as pd
import json
from pathlib import Path
from galapagos.research.universe_mismatch.timestamp_alignment import analyze_timestamp_alignment
from galapagos.research.universe_mismatch.duplicate_analysis import analyze_duplicates
from galapagos.research.universe_mismatch.mismatch_classifier import classify_mismatch

def test_timestamp_alignment_detection():
    df_preds = pd.DataFrame(index=pd.to_datetime(["2026-01-01", "2026-01-01", "2026-01-02"]))
    df_dataset = pd.DataFrame(index=pd.to_datetime(["2026-01-01", "2026-01-03"]))
    
    res = analyze_timestamp_alignment(df_preds, df_dataset)
    assert res["intersection_count"] == 1 # Only 2026-01-01
    assert res["duplicate_rows_per_timestamp_max"] == 2
    assert res["unmatched_prediction_timestamps"] == 1 # 2026-01-02
    assert res["unmatched_dataset_timestamps"] == 1 # 2026-01-03

def test_duplicate_analysis_36_rows():
    # Mock 36 rows for one timestamp
    ts = pd.to_datetime("2026-01-01")
    df = pd.DataFrame(index=[ts]*36)
    
    res = analyze_duplicates(df)
    assert res["rows_per_timestamp_mean"] == 36.0
    assert res["v1_32_4_trade_unit_hypothesis"] == "MULTI_ROW_PER_TIMESTAMP"

def test_mismatch_classifier_trade_unit():
    summary = {
        "duplicate_policy_status": "DUPLICATE_POLICY_MISMATCH_EXPLAINS_DELTA",
        "join_path_status": "JOIN_PATH_MATCHES",
        "warmup_policy_status": "WARMUP_NOT_EXPLANATORY"
    }
    res = classify_mismatch(summary)
    assert res["primary_mismatch_driver"] == "TRADE_UNIT_MISMATCH"
    assert res["confidence_level"] == "HIGH"

def test_mismatch_classifier_unexplained():
    summary = {
        "duplicate_policy_status": "DUPLICATE_POLICY_MATCHES",
        "join_path_status": "JOIN_PATH_MATCHES",
        "warmup_policy_status": "WARMUP_NOT_EXPLANATORY"
    }
    res = classify_mismatch(summary)
    assert res["primary_mismatch_driver"] == "MISMATCH_UNEXPLAINED"
