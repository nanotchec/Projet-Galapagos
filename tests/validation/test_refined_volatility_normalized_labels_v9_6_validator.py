from __future__ import annotations

import pandas as pd

from galapagos.labels.refined_volatility_normalized_labels_v9_6 import build_refined_volatility_normalized_labels_frame_v9_6
from galapagos.labels.refined_volatility_normalized_labels_v9_6_validation import (
    validate_label_frame_v9_6,
    validate_manifest_payload_v9_6,
)
from galapagos.labels.refined_volatility_normalized_labels_v9_6_schemas import (
    EXPECTED_LIMITATIONS_V9_6,
    FINDINGS_V9_6,
    LABEL_SCHEMA_VERSION_V9_6,
    PARAMETER_GRID_V9_6,
    REFINED_VOLATILITY_NORMALIZED_LABEL_COLUMNS_V9_6,
    SAFETY_FLAGS_V9_6,
    TARGET_NAME_V9_6,
    VERSION_V9_6,
)


def _payload() -> dict:
    return {
        "version": VERSION_V9_6,
        "status": "PASS",
        "decision": "label_factory_candidate_created_volatility_normalized",
        "target_name": TARGET_NAME_V9_6,
        "label_schema_version": LABEL_SCHEMA_VERSION_V9_6,
        "label_columns": REFINED_VOLATILITY_NORMALIZED_LABEL_COLUMNS_V9_6,
        "parameters_tested": PARAMETER_GRID_V9_6,
        "findings": FINDINGS_V9_6,
        "safety": SAFETY_FLAGS_V9_6,
        "limitations": EXPECTED_LIMITATIONS_V9_6,
        "leakage_guard": {"passed": True},
        "outputs": {"1m": {}, "5m": {}, "15m": {}, "1h": {}},
    }


def test_validator_v9_6_accepts_valid_manifest_payload() -> None:
    assert validate_manifest_payload_v9_6(_payload()) == []


def test_validator_v9_6_rejects_forbidden_claim_flag() -> None:
    payload = _payload()
    payload["findings"] = {**FINDINGS_V9_6, "strategy_validated": True}
    assert "V9.6 findings mismatch" in validate_manifest_payload_v9_6(payload)


def test_validator_v9_6_rejects_bad_target() -> None:
    payload = _payload()
    payload["target_name"] = "up_down_flat_h1"
    assert "V9.6 target mismatch" in validate_manifest_payload_v9_6(payload)


def test_validator_v9_6_rejects_forbidden_output_column() -> None:
    event_ts = pd.date_range("2023-03-25", periods=48, freq="min", tz="UTC")
    dataset = pd.DataFrame(
        {
            "source": "binance_archive",
            "venue": "binance",
            "market_type": "spot",
            "symbol": "BTCUSDT",
            "timeframe": "1m",
            "event_ts": event_ts,
            "close_ts": event_ts + pd.Timedelta(seconds=59),
            "decision_ts": event_ts + pd.Timedelta(seconds=59),
            "close": range(100, 148),
            "future_log_return_h1": 0.001,
            "label_end_ts_h1": event_ts + pd.Timedelta(minutes=1, seconds=59),
            "warmup_row": False,
        }
    )
    labels = build_refined_volatility_normalized_labels_frame_v9_6(
        dataset,
        source_dataset_path="sample",
        source_dataset_version="V9.1",
        label_run_id="test",
        volatility_threshold_multiplier=0.5,
    )
    labels["signal"] = "forbidden"
    errors = validate_label_frame_v9_6(labels)
    assert any("schema mismatch" in error or "forbidden" in error for error in errors)
