from __future__ import annotations

from pathlib import Path

from galapagos.research.derivatives_data_extension_readiness_v9_15 import (
    SAFETY_FLAGS,
    analyze_source_readiness_v9_15,
    analyze_v9_compatibility_v9_15,
    decide_feature_candidate_v9_15,
    decide_readiness_v9_15,
    inspect_local_derivatives_sources_v9_15,
    overlap_with_v9_window_v9_15,
)


def _coverage() -> dict:
    return {
        "checks": [
            {
                "source": "binance",
                "metric_name": "funding_rate",
                "status": "available",
                "rows": 2190,
                "start_timestamp": "2024-05-05 16:00:00+00:00",
                "end_timestamp": "2026-05-05 00:00:00+00:00",
                "missing_rate": 0.769,
                "freshness": "fresh",
            },
            {
                "source": "binance",
                "metric_name": "open_interest",
                "status": "unavailable",
                "rows": 0,
                "start_timestamp": None,
                "end_timestamp": None,
                "missing_rate": 1.0,
                "freshness": "unknown",
            },
            {
                "source": "bybit",
                "metric_name": "open_interest",
                "status": "available",
                "rows": 200,
                "start_timestamp": "2026-04-02 08:00:00+00:00",
                "end_timestamp": "2026-05-05 12:00:00+00:00",
                "missing_rate": 0.978,
                "freshness": "fresh",
            },
        ]
    }


def _quality() -> dict:
    return {
        "missing_rates": {
            "funding_rate": 0.04,
            "funding_rate_binance": 0.08,
            "open_interest": 0.91,
            "open_interest_bybit": 0.91,
        }
    }


def _features() -> dict:
    return {"columns": ["available_timestamp", "funding_rate", "open_interest"], "status": "available"}


def test_overlap_detects_no_v9_coverage_for_post_v9_derivatives_v9_15() -> None:
    overlap = overlap_with_v9_window_v9_15("2024-05-05 16:00:00+00:00", "2026-05-05 00:00:00+00:00")

    assert overlap["overlaps_v9_window"] is False
    assert overlap["overlap_start"] is None
    assert overlap["overlap_end"] is None


def test_funding_readiness_marks_missing_v9_coverage_v9_15() -> None:
    funding = analyze_source_readiness_v9_15("funding_rates", _coverage(), _quality(), _features())

    assert funding["present_local"] is True
    assert funding["total_rows_available"] == 2190
    assert funding["compatible_with_v9_window"] is False
    assert funding["readiness_decision"] == "not_ready_missing_coverage"
    assert funding["causality"]["available_timestamp_or_equivalent_present"] is True


def test_open_interest_readiness_marks_missing_v9_coverage_v9_15() -> None:
    open_interest = analyze_source_readiness_v9_15("open_interest", _coverage(), _quality(), _features())

    assert open_interest["present_local"] is True
    assert open_interest["total_rows_available"] == 200
    assert open_interest["compatible_with_v9_window"] is False
    assert open_interest["readiness_decision"] == "not_ready_missing_coverage"


def test_v9_compatibility_rejects_alignment_without_overlap_v9_15(tmp_path: Path) -> None:
    funding = analyze_source_readiness_v9_15("funding_rates", _coverage(), _quality(), _features())
    open_interest = analyze_source_readiness_v9_15("open_interest", _coverage(), _quality(), _features())
    inventory = inspect_local_derivatives_sources_v9_15(tmp_path)
    compatibility = analyze_v9_compatibility_v9_15(funding, open_interest, inventory)

    assert compatibility["compatible_with_current_v9_chain"] is False
    assert compatibility["alignment_possible_now"] is False
    assert compatibility["forward_fill_policy"] == "not_allowed_for_current_v9_window_because_coverage_does_not_overlap"


def test_feature_candidate_is_not_created_when_window_incompatible_v9_15(tmp_path: Path) -> None:
    funding = analyze_source_readiness_v9_15("funding_rates", _coverage(), _quality(), _features())
    open_interest = analyze_source_readiness_v9_15("open_interest", _coverage(), _quality(), _features())
    compatibility = analyze_v9_compatibility_v9_15(funding, open_interest, inspect_local_derivatives_sources_v9_15(tmp_path))
    candidate = decide_feature_candidate_v9_15(funding, open_interest, compatibility)
    decision = decide_readiness_v9_15(funding, open_interest, compatibility, candidate)

    assert candidate["created"] is False
    assert candidate["outputs"] == []
    assert decision["decision"] == "derivatives_readiness_not_compatible_with_v9_window"
    assert "V9.16" in decision["next_recommendation"]


def test_safety_flags_confirm_no_network_and_no_download_v9_15() -> None:
    assert SAFETY_FLAGS["network_used"] is False
    assert SAFETY_FLAGS["no_new_data_download"] is True
    assert SAFETY_FLAGS["no_backtest"] is True
    assert SAFETY_FLAGS["no_walk_forward"] is True
