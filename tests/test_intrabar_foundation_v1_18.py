"""Tests for Galapagos V1.18 - Intrabar Foundation."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pandas as pd

from galapagos.research.intrabar.alignment import get_intrabar_slice, validate_intrabar_coverage
from galapagos.research.intrabar.availability import check_availability
from galapagos.research.intrabar.comparison import compare_simulations
from galapagos.research.intrabar.downloader import download_intrabar_sample
from galapagos.research.intrabar.execution_simulator import simulate_intrabar_exit
from galapagos.research.intrabar.mae_mfe import calculate_mae_mfe

ROOT = Path(__file__).parent.parent


def test_availability_dry_run():
    res = check_availability(["binance", "bybit"], "BTCUSDT", ["5m", "1m"], dry_run=True)
    assert len(res) == 4
    for r in res:
        assert r["status"] == "dry_run_only"


def test_downloader_dry_run(tmp_path):
    res = download_intrabar_sample(
        "binance", "BTCUSDT", "5m", 30, output_dir=str(tmp_path), dry_run=True
    )
    assert res["status"] == "dry_run"
    assert res["rows"] == 0


def test_alignment_no_future_intrabar():
    intrabar = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                ["2026-01-01 00:05", "2026-01-01 03:55", "2026-01-01 04:05"], utc=True
            )
        }
    )
    open_ts = pd.Timestamp("2026-01-01 00:00", tz="UTC")
    close_ts = open_ts + pd.Timedelta(hours=4)
    slice_df = get_intrabar_slice(intrabar, open_ts, close_ts)
    assert len(slice_df) == 2
    assert "2026-01-01 04:05" not in slice_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M").values


def test_alignment_partial_coverage():
    intrabar = pd.DataFrame({"timestamp": pd.to_datetime(["2026-01-01 00:05"], utc=True)})
    open_ts = pd.Timestamp("2026-01-01 00:00", tz="UTC")
    close_ts = open_ts + pd.Timedelta(hours=4)
    val = validate_intrabar_coverage(open_ts, close_ts, intrabar, "5m")
    assert val["status"] == "partial"


def test_simulate_long_tp_sl():
    intrabar = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2026-01-01 00:05", "2026-01-01 00:10"], utc=True),
            "high": [51000, 50000],
            "low": [49000, 48000],
            "close": [50000, 49000],
        }
    )
    # Long, entry 50000, TP 51000, SL 48000.
    # At 00:05, high is 51000 (hits TP), low is 49000 (no hit SL). Exit reason: take_profit
    res = simulate_intrabar_exit(
        "LONG",
        50000,
        48000,
        51000,
        pd.Timestamp("2026-01-01 00:00", tz="UTC"),
        pd.Timestamp("2026-01-01 04:00", tz="UTC"),
        intrabar,
    )
    assert res["exit_reason"] == "take_profit"
    assert res["exit_price"] == 51000


def test_simulate_short_tp_sl():
    intrabar = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2026-01-01 00:05", "2026-01-01 00:10"], utc=True),
            "high": [51000, 52000],
            "low": [49000, 48000],
            "close": [50000, 51000],
        }
    )
    # Short, entry 50000, TP 49000, SL 52000.
    # At 00:05, low is 49000 (hits TP), high is 51000 (no hit SL).
    res = simulate_intrabar_exit(
        "SHORT",
        50000,
        52000,
        49000,
        pd.Timestamp("2026-01-01 00:00", tz="UTC"),
        pd.Timestamp("2026-01-01 04:00", tz="UTC"),
        intrabar,
    )
    assert res["exit_reason"] == "take_profit"


def test_simulate_ambiguous_same_intrabar():
    intrabar = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2026-01-01 00:05"], utc=True),
            "high": [52000],
            "low": [48000],
            "close": [50000],
        }
    )
    # Long, entry 50000, TP 51000, SL 49000.
    # Both hit in same candle. Conservative fallback should select SL.
    res = simulate_intrabar_exit(
        "LONG",
        50000,
        49000,
        51000,
        pd.Timestamp("2026-01-01 00:00", tz="UTC"),
        pd.Timestamp("2026-01-01 04:00", tz="UTC"),
        intrabar,
        fallback_policy="conservative",
    )
    assert res["exit_reason"] == "stop_loss"
    assert res["ambiguous"] is True


def test_simulate_fallback_no_intrabar():
    res = simulate_intrabar_exit(
        "LONG",
        50000,
        49000,
        51000,
        pd.Timestamp("2026-01-01 00:00", tz="UTC"),
        pd.Timestamp("2026-01-01 04:00", tz="UTC"),
        pd.DataFrame(),
    )
    assert res["exit_reason"] == "fallback_no_intrabar"
    assert res["used_fallback"] is True


def test_mae_mfe_calculation():
    intrabar = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2026-01-01 00:05", "2026-01-01 00:10"], utc=True),
            "high": [51000, 52000],
            "low": [49000, 48000],
            "open": [50000, 50500],
            "close": [50500, 49000],
        }
    )
    res = calculate_mae_mfe("LONG", 50000, intrabar)
    assert res["max_favorable_excursion_abs"] == 2000  # 52000 - 50000
    assert res["max_adverse_excursion_abs"] == 2000  # 50000 - 48000


def test_comparison_sparse_data():
    res = compare_simulations(pd.DataFrame(), pd.DataFrame())
    assert res["verdict"] == "INTRABAR_DATA_TOO_SPARSE"


def test_orchestrator_dry_run_no_network():
    cmd = (
        "python scripts/run_intrabar_foundation.py --symbol BTCUSDT "
        "--timeframe 5m --days 30 --version v1.18 --dry-run"
    )
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, shell=True)
    assert result.returncode == 0
    assert "Orchestration complete" in result.stdout


def test_no_codex_cli_v1_18():
    cmd = (
        "grep -rE 'subprocess.*codex|codex.*subprocess' scripts/ src/galapagos/research/intrabar/"
        " --include='*.py' -l 2>/dev/null || true"
    )
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, shell=True)
    codex_files = [f for f in result.stdout.strip().split("\n") if f]
    assert codex_files == []


def test_no_holdout_execution_v1_18():
    cmd = (
        "grep -rE 'run_holdout' scripts/ src/galapagos/research/intrabar/"
        " --include='*.py' -l 2>/dev/null || true"
    )
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, shell=True)
    holdout_files = [f for f in result.stdout.strip().split("\n") if f]
    assert holdout_files == []


def test_no_real_trading_v1_18():
    cmd = (
        "grep -rE 'create_order|place_order' scripts/ src/galapagos/research/intrabar/"
        " --include='*.py' -l 2>/dev/null || true"
    )
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, shell=True)
    trading_files = [f for f in result.stdout.strip().split("\n") if f]
    assert trading_files == []
