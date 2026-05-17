import pytest
from galapagos.research.canonical_universe.input_path_guard import check_input_paths
from galapagos.research.canonical_universe.count_sanity_guard import check_count_sanity

def test_input_path_guard_rejects_mock():
    res = check_input_paths("data/gold/ml_predictions/BTC/4h/mock_preds.parquet", "data/gold/research_dataset/BTC/4h/real.parquet", "data/silver/intrabar/binance/BTCUSDT/5m/real.parquet")
    assert res["input_path_guard_status"] == "CANONICAL_INPUT_PATH_GUARD_FAILED"
    assert any("mock" in iss for iss in res["issues"])

def test_input_path_guard_rejects_scratch():
    res = check_input_paths("data/gold/ml_predictions/BTC/4h/real.parquet", "scratch/real.parquet", "data/silver/intrabar/binance/BTCUSDT/5m/real.parquet")
    assert res["input_path_guard_status"] == "CANONICAL_INPUT_PATH_GUARD_FAILED"
    assert any("scratch" in iss or ".gemini/antigravity/brain" in iss for iss in res["issues"])

def test_input_path_guard_rejects_dev_null():
    res = check_input_paths("/dev/null", "data/gold/research_dataset/BTC/4h/real.parquet", "data/silver/intrabar/binance/BTCUSDT/5m/real.parquet")
    assert res["input_path_guard_status"] == "CANONICAL_INPUT_PATH_GUARD_FAILED"

def test_count_sanity_guard_rejects_100():
    res = check_count_sanity(100, 100, 100, 100, 100)
    assert res["count_sanity_guard_status"] == "CANONICAL_COUNT_SANITY_GUARD_FAILED"
    assert res["suspicious_mock_count_detected"] is True

def test_count_sanity_guard_accepts_real():
    res = check_count_sanity(171648, 171648, 171648, 171648, 171648)
    assert res["count_sanity_guard_status"] == "CANONICAL_COUNT_SANITY_GUARD_PASSED"
    assert res["count_match_v1_36_8"] is True
