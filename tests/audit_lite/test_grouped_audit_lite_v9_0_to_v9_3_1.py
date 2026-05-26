from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from galapagos.datasets.schemas import DATASET_COLUMNS_V9_1
from galapagos.features.refined_ohlcv_trades_schemas import REFINED_OHLCV_TRADES_FEATURE_COLUMNS_V9_0
from galapagos.ml.schemas import ML_SCORE_COLUMNS_V9_2, ML_SCORE_COLUMNS_V9_3, WALK_FORWARD_FOLD_COLUMNS_V9_3


ROOT = Path(__file__).resolve().parents[2]
TIMEFRAMES = ["1m", "5m", "15m", "1h"]
FORBIDDEN_SAMPLE_COLUMNS = {
    "prediction",
    "predicted",
    "model_score",
    "signal",
    "trading_signal",
    "strategy",
    "order",
    "position_size",
    "pnl",
    "profit",
    "backtest",
    "execution",
}


def test_grouped_audit_lite_v9_0_to_v9_3_1_samples_are_self_contained() -> None:
    assert (ROOT / "scripts/_bootstrap.py").is_file()
    manifest = _read_json(ROOT / "reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json")

    assert manifest["selected_features_count"] == 18
    assert manifest["selected_features"]


def test_grouped_audit_lite_v9_0_to_v9_3_1_sample_schemas_are_strict() -> None:
    sample_specs = [
        ("features", "features_sample.parquet", REFINED_OHLCV_TRADES_FEATURE_COLUMNS_V9_0),
        ("datasets", "dataset_sample.parquet", DATASET_COLUMNS_V9_1),
        ("ml_scores", "ml-scores_sample.parquet", ML_SCORE_COLUMNS_V9_2),
        ("walk_forward_scores", "walk_forward_scores_sample.parquet", ML_SCORE_COLUMNS_V9_3),
        ("folds", "folds_sample.parquet", WALK_FORWARD_FOLD_COLUMNS_V9_3),
    ]

    for folder, filename, expected_columns in sample_specs:
        for timeframe in TIMEFRAMES:
            sample_path = ROOT / "data/audit_lite/v9_0_to_v9_3" / folder / f"timeframe={timeframe}" / filename
            frame = pd.read_parquet(sample_path, engine="pyarrow")
            assert list(frame.columns) == expected_columns
            assert len(frame) > 0


def test_grouped_audit_lite_v9_0_to_v9_3_1_samples_exclude_forbidden_outputs() -> None:
    for sample_path in (ROOT / "data/audit_lite/v9_0_to_v9_3").rglob("*.parquet"):
        frame = pd.read_parquet(sample_path, engine="pyarrow")

        assert sorted(set(frame.columns) & FORBIDDEN_SAMPLE_COLUMNS) == []


def test_grouped_audit_lite_v9_0_to_v9_3_1_claims_remain_false() -> None:
    manifest = _read_json(ROOT / "reports/manifests/refined_strict_walk_forward_validation_v9_3_manifest.json")
    findings = manifest["findings"]

    assert findings["robust_edge_claimed"] is False
    assert findings["strategy_validated"] is False
    assert findings["backtest_performed"] is False
    assert findings["actionable_signal_produced"] is False
    assert findings["walk_forward_validated_for_trading"] is False


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
