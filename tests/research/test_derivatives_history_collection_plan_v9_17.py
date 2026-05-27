from __future__ import annotations

from pathlib import Path

from galapagos.research.derivatives_history_collection_plan_v9_17 import (
    SAFETY_FLAGS,
    build_candidate_target_windows_v9_17,
    build_current_data_gap_summary_v9_17,
    build_source_collection_candidates_v9_17,
    decide_v9_17,
    gap_between_v9_17,
    inspect_local_metadata_v9_17,
)


def _payloads() -> dict:
    return {
        "v9_16_decision": {
            "v9_16_decision": {"decision": "data_extension_should_collect_more_history"},
            "data_sources_inventory": [
                {
                    "source_name": "OHLCV",
                    "coverage_start": "2023-03-25T00:00:00Z",
                    "coverage_end": "2026-05-23T23:59:59Z",
                    "total_rows": 2136288,
                },
                {
                    "source_name": "trades_aggTrades",
                    "coverage_start": "2023-03-25T00:00:00Z",
                    "coverage_end": "2024-03-24T23:59:59Z",
                    "total_rows": 352055121,
                },
                {
                    "source_name": "funding_rates",
                    "coverage_start": "2024-05-05 16:00:00+00:00",
                    "coverage_end": "2026-05-05 08:00:00+00:00",
                    "total_rows": 2390,
                },
                {
                    "source_name": "open_interest",
                    "coverage_start": "2026-04-02 08:00:00+00:00",
                    "coverage_end": "2026-05-05 12:00:00+00:00",
                    "total_rows": 200,
                },
                {
                    "source_name": "other_derivatives_local",
                    "coverage_start": "2026-04-05 12:00:00+00:00",
                    "coverage_end": "2026-05-05 15:14:11+00:00",
                    "total_rows": 362,
                },
            ],
        }
    }


def test_gap_between_aggtrades_end_and_funding_start_v9_17() -> None:
    gap_days = gap_between_v9_17("2024-03-24T23:59:59Z", "2024-05-05T16:00:00Z")

    assert gap_days == 42


def test_current_gap_summary_keeps_collection_boundary_v9_17() -> None:
    summary = build_current_data_gap_summary_v9_17(_payloads())

    assert summary["v9_16_decision"] == "data_extension_should_collect_more_history"
    assert summary["aggtrades_to_funding_gap_days"] == 42
    assert summary["current_common_window_ohlcv_aggtrades_funding_days"] == 0
    assert summary["collection_needed_before_feature_candidate"] is True


def test_source_candidates_prioritize_aggtrades_and_funding_without_keys_v9_17() -> None:
    gap_summary = build_current_data_gap_summary_v9_17(_payloads())
    candidates = build_source_collection_candidates_v9_17(gap_summary, _payloads())
    by_name = {item["source_name"]: item for item in candidates}

    assert by_name["aggTrades_public_trades_post_v9"]["integration_priority"] == "priority_1"
    assert by_name["aggTrades_public_trades_post_v9"]["network_required_future_collection"] is True
    assert by_name["aggTrades_public_trades_post_v9"]["needs_api_key"] is False
    assert by_name["funding_rates_historical"]["integration_priority"] == "priority_1"
    assert by_name["open_interest_history"]["integration_priority"] == "priority_2"
    assert all(candidate["needs_api_key"] is False for candidate in candidates)
    assert all("available_ts" in candidate["expected_causal_timestamp_fields"] for candidate in candidates)


def test_target_windows_reject_short_open_interest_and_prioritize_post_v9_v9_17() -> None:
    gap_summary = build_current_data_gap_summary_v9_17(_payloads())
    windows = build_candidate_target_windows_v9_17(gap_summary)
    by_name = {item["window_name"]: item for item in windows}

    assert by_name["funding_first_post_v9"]["recommendation_status"] == "priority_1_collection_plan"
    assert by_name["funding_first_post_v9"]["suitable_for_future_walk_forward"] is True
    assert by_name["funding_open_interest_recent"]["recommendation_status"] == "reject_too_short"
    assert by_name["funding_open_interest_recent"]["suitable_for_future_ml"] is False
    assert by_name["derivatives_native_4h"]["recommendation_status"] == "priority_2_collection_plan"


def test_v9_17_decision_selects_aggtrades_post_v9_collection_plan() -> None:
    gap_summary = build_current_data_gap_summary_v9_17(_payloads())
    candidates = build_source_collection_candidates_v9_17(gap_summary, _payloads())
    windows = build_candidate_target_windows_v9_17(gap_summary)
    decision = decide_v9_17(candidates, windows)

    assert decision["decision"] == "collection_plan_priority_aggtrades_post_v9_and_funding"
    assert decision["collection_executed"] is False
    assert decision["no_backtest"] is True
    assert "V9.18" in decision["next_recommendation"]


def test_local_metadata_inventory_uses_tmp_path_and_keeps_runtime_safety_v9_17(tmp_path: Path) -> None:
    (tmp_path / "data/raw/public_trades").mkdir(parents=True)
    (tmp_path / "reports/research").mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    inventory = inspect_local_metadata_v9_17(tmp_path)

    assert inventory["raw_public_trades"]["exists"] is True
    assert inventory["reports_research"]["exists"] is True
    assert inventory["network_used_in_v9_17"] is False
    assert inventory["new_data_downloaded_in_v9_17"] is False
    assert inventory["ingestion_executed_in_v9_17"] is False
    assert SAFETY_FLAGS["network_used"] is False
    assert SAFETY_FLAGS["no_ingestion_executed"] is True
