from __future__ import annotations

from copy import deepcopy

from galapagos.research.derivatives_window_extension_v9_16 import FINDINGS, SAFETY, SAFETY_FLAGS, VERSION
from galapagos.research.derivatives_window_extension_v9_16_validation import (
    validate_candidate_windows_v9_16,
    validate_manifest_payload_v9_16,
    validate_markdown_v9_16,
    validate_report_payload_v9_16,
)


def _candidate(name: str, status: str = "not_viable") -> dict:
    return {
        "candidate_window_name": name,
        "duration_days": 0,
        "recommendation_status": status,
        "requires_new_feature_store": False,
        "compatible_with_existing_v9_features": False,
    }


def _valid_candidates() -> list[dict]:
    return [
        _candidate("funding_only_with_ohlcv_trades"),
        _candidate("funding_and_open_interest_with_ohlcv_trades"),
        _candidate("derivatives_4h_native", "partial_candidate_requires_alignment"),
        _candidate("multi_year_ohlcv_trades_without_derivatives"),
    ]


def _valid_report() -> dict:
    return {
        "version": VERSION,
        "source_version": "V9.15",
        "status": "PASS",
        "v9_16_decision": {"decision": "data_extension_should_collect_more_history"},
        "data_sources_inventory": [
            {"source_name": "OHLCV"},
            {"source_name": "trades_aggTrades"},
            {"source_name": "funding_rates"},
            {"source_name": "open_interest"},
            {"source_name": "other_derivatives_local"},
        ],
        "candidate_windows": _valid_candidates(),
        "compatibility_analysis": {
            "enough_for_future_walk_forward": False,
            "funding_only_more_realistic_than_oi_plus_funding": True,
        },
        "features_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "findings": dict(FINDINGS),
        "safety": dict(SAFETY),
        "safety_flags": dict(SAFETY_FLAGS),
    }


def test_validator_accepts_valid_report_v9_16() -> None:
    assert validate_report_payload_v9_16(_valid_report()) == []


def test_validator_rejects_missing_source_inventory_v9_16() -> None:
    report = _valid_report()
    report["data_sources_inventory"] = [{"source_name": "OHLCV"}]

    assert any("must inventory" in error for error in validate_report_payload_v9_16(report))


def test_validator_rejects_viable_funding_candidate_without_overlap_v9_16() -> None:
    candidates = _valid_candidates()
    candidates[0]["recommendation_status"] = "viable_candidate"

    assert "V9.16 funding-only candidate must not be viable while aggTrades end before funding starts" in validate_candidate_windows_v9_16(candidates)


def test_validator_rejects_walk_forward_ready_v9_16() -> None:
    report = _valid_report()
    report["compatibility_analysis"]["enough_for_future_walk_forward"] = True

    assert "V9.16 must not mark future walk-forward as ready" in validate_report_payload_v9_16(report)


def test_validator_rejects_backtest_execution_true_v9_16() -> None:
    report = _valid_report()
    report["backtest_executed"] = True

    assert "V9.16 must not execute ML, walk-forward or backtest" in validate_report_payload_v9_16(report)


def test_validator_rejects_network_used_true_v9_16() -> None:
    report = _valid_report()
    report["safety_flags"]["network_used"] = True

    assert "V9.16 safety flag mismatch: network_used" in validate_report_payload_v9_16(report)


def test_validator_rejects_sidecar_field_v9_16() -> None:
    report = _valid_report()
    manifest = deepcopy(report)
    manifest.update(
        {
            "version": VERSION,
            "status": "PASS",
            "v9_16_decision": {"decision": "data_extension_should_collect_more_history"},
            "candidate_windows_count": 4,
            "data_sources_count": 5,
            "sidecar_json": "forbidden",
        }
    )

    assert "V9.16 manifest must not contain sidecar or ZIP hash fields" in validate_manifest_payload_v9_16(manifest, report)


def test_validator_rejects_markdown_forbidden_claim_v9_16() -> None:
    text = "Funding-only. Funding + OI. Derivatives 4h native. Aucun backtest. Aucun trading. Aucun ordre. Aucune strategie. Aucun signal actionnable. Aucun walk-forward. Aucun reseau. Aucun telechargement. tradable edge confirmed"

    assert any("forbidden claim" in error for error in validate_markdown_v9_16(text))


def test_validator_rejects_markdown_trading_metric_v9_16() -> None:
    text = "Funding-only. Funding + OI. Derivatives 4h native. Aucun backtest. Aucun trading. Aucun ordre. Aucune strategie. Aucun signal actionnable. Aucun walk-forward. Aucun reseau. Aucun telechargement. Sharpe."

    assert any("forbidden metric term" in error for error in validate_markdown_v9_16(text))
