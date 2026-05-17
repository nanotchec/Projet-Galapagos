"""Tests for intrabar signal semantics and duplicate audit (V1.18.2)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd

scripts_path = str(Path(__file__).parent.parent / "scripts")
if scripts_path not in sys.path:
    sys.path.append(scripts_path)

from run_intrabar_foundation import find_real_signals  # noqa: E402


def test_deduplication_logic():
    """Verify that find_real_signals correctly deduplicates signals."""
    mock_df = pd.DataFrame({
        "timestamp": ["2026-01-01 00:00:00", "2026-01-01 00:00:00", "2026-01-01 04:00:00"],
        "model_name": ["model_A", "model_B", "model_A"],
        "feature_set": ["fs1", "fs1", "fs1"],
        "target": ["t1", "t1", "t1"],
        "predicted_probability": [0.6, 0.8, 0.7],
        "predicted_label": [1, 1, 1],
        "split_name": ["oos", "oos", "oos"]
    })

    with patch("pathlib.Path.exists", return_value=True), \
         patch("pandas.read_parquet", return_value=mock_df):

        signals_df, audit = find_real_signals()

        assert audit["raw_signal_rows"] == 3
        assert audit["unique_signal_timestamps"] == 2
        assert audit["duplicate_signal_rows"] == 1
        assert audit["duplicates_per_timestamp_max"] == 2

        # Check that we kept the one with 0.8 probability for 00:00:00
        ts_00 = pd.Timestamp("2026-01-01 00:00:00", tz="UTC")
        row_00 = signals_df[signals_df["timestamp"] == ts_00]
        assert len(row_00) == 1
        assert row_00.iloc[0]["predicted_probability"] == 0.8


def test_semantics_honesty():
    """Verify that summary and metrics correctly identify the simulation status."""
    summary_path = Path("reports/current/latest_summary.md")
    if summary_path.exists():
        content = summary_path.read_text()
        assert "INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER" in content
        assert "déduplication" in content.lower()

    metrics_path = Path("reports/current/latest_metrics.json")
    if metrics_path.exists():
        with open(metrics_path) as f:
            data = json.load(f)
            assert data["version"].lower().startswith("v1.")
            assert data.get("strategy_reviewer_ready") is False
            assert data.get("release_ready_for_external_review") is True


def test_security_constraints():
    """Verify that security constraints are mentioned in latest summary."""
    summary_path = Path("reports/current/latest_summary.md")
    if summary_path.exists():
        content = summary_path.read_text()
        assert "Codex CLI** : Non appelé" in content
        assert "Holdout** : Non exécuté" in content
        assert "Trading Réel** : Désactivé" in content
        assert "ne peut toujours pas passer d'ordre réel" in content or (
            "Trading Réel** : Désactivé" in content
        )
