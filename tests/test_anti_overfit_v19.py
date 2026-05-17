from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from galapagos.evaluation.anti_overfit_runner import run_anti_overfit_evaluation
from galapagos.evaluation.holdout_guard import mark_holdout_used
from galapagos.evaluation.window_selector import (
    ensure_no_overlap,
    split_ohlcv_into_windows,
)
from galapagos.reports.anti_overfit_report import write_anti_overfit_summary


def test_window_selector_non_overlap_and_timestamps() -> None:
    data = _sample_ohlcv(160)
    windows = split_ohlcv_into_windows(data, n_windows=4, min_bars_per_window=20)
    assert len(windows) == 4
    assert ensure_no_overlap(windows) is True
    assert windows[0].end_index <= windows[1].start_index
    assert windows[0].start_timestamp < windows[0].end_timestamp


def test_window_selector_errors_on_insufficient_history() -> None:
    with pytest.raises(ValueError, match="Insufficient history"):
        split_ohlcv_into_windows(_sample_ohlcv(20), n_windows=4, min_bars_per_window=20)


def test_holdout_guard_creates_marker(tmp_path: Path) -> None:
    marker = mark_holdout_used(tmp_path, config_hash="abc", prompt_hash="def")
    assert marker.exists()
    text = marker.read_text(encoding="utf-8")
    assert "Do not tune on this result." in text
    assert "config_hash: abc" in text


def test_anti_overfit_runner_dry_run(monkeypatch, tmp_path: Path) -> None:
    data_path = tmp_path / "ohlcv.csv"
    _sample_ohlcv(200).to_csv(data_path, index=False)
    config_path = tmp_path / "evaluation.yaml"
    config_path.write_text(
        """
evaluation_name: test_anti_overfit
profile: galapagos_4h
asset: BTC/USD
timeframe: 4h
source_policies:
  - state_aware_breakout
  - state_aware_momentum
min_bars_per_window: 40
warmup_bars: 25
min_spacing_bars: 1
windows:
  calibration:
    label: calibration
    max_candidates: 5
    purpose: debug
  validation_1:
    label: validation_1
    max_candidates: 5
    purpose: validation
  validation_2:
    label: validation_2
    max_candidates: 5
    purpose: validation
  holdout:
    label: holdout
    max_candidates: 5
    purpose: holdout
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "galapagos.evaluation.anti_overfit_runner.find_latest_cached_ohlcv",
        lambda symbol, timeframe: data_path,
    )
    result = run_anti_overfit_evaluation(
        config_path=config_path,
        mode="dry-run",
        output_root=tmp_path / "reports",
    )
    assert result["codex_cli_called"] is False
    assert result["holdout_executed"] is False
    assert len(result["windows"]) == 4
    for window in result["windows"]:
        assert "no_trade" in window["baselines"]
        assert "state_aware_momentum" in window["baselines"]
        assert "state_aware_breakout" in window["baselines"]
        assert "llm_offline_conservative" in window["baselines"]
        assert "ledger_pnl_matches_official" in window
    summary_json = Path(result["summary_paths"]["json"])
    assert summary_json.exists()
    assert json.loads(summary_json.read_text(encoding="utf-8"))["verdict"] == "NOT_ENOUGH_DATA"
    assert not any(Path(result["output_dir"]).glob("HOLDOUT_USED.txt"))


def test_global_report_generated(tmp_path: Path) -> None:
    paths = write_anti_overfit_summary(
        evaluation_run_id="run",
        config={"evaluation_name": "test", "profile": "galapagos_4h"},
        window_results=[
            {
                "window_label": "calibration",
                "window": {"start_index": 0, "end_index": 10, "bars": 10},
                "candidates_found": 2,
                "baselines": {"no_trade": {}},
                "gpt_setup_review": {"executed": False},
                "ledger_pnl_matches_official": None,
            }
        ],
        output_dir=tmp_path,
        holdout_executed=False,
    )
    assert paths["markdown"].exists()
    assert paths["json"].exists()


def _sample_ohlcv(rows: int) -> pd.DataFrame:
    data = []
    price = 100.0
    start = pd.Timestamp("2026-01-01T00:00:00Z")
    for index in range(rows):
        price += 0.2
        if index % 11 == 0:
            price += 2.0
        data.append(
            {
                "timestamp": start + pd.Timedelta(hours=4 * index),
                "open": price - 0.4,
                "high": price + 1.0,
                "low": price - 1.0,
                "close": price,
                "volume": 100 + index,
            }
        )
    return pd.DataFrame(data)
