from __future__ import annotations

from pathlib import Path

from galapagos.research.feature_label_separability_v9_14_1 import (
    REQUIRED_SOURCE_NAMES,
    SAFETY_FLAGS,
    build_data_extension_recommendation_v9_14_1,
    build_data_source_inventory_v9_14_1,
    classify_hypotheses_v9_14_1,
    decide_v9_14_1,
)


def _touch(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")


def _inventory_root(tmp_path: Path) -> Path:
    for relative in [
        "reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json",
        "reports/features/refined_ohlcv_trades_feature_store_v9_0.json",
        "reports/manifests/public_trades_1y_window_v8_2_manifest.json",
        "reports/research/derivatives_coverage_v1_14.json",
        "reports/research/derivatives_data_quality_v1_14.json",
        "reports/research/derivatives_features_v1_14.json",
        "src/galapagos/data/derivatives/binance_futures.py",
        "src/galapagos/data/derivatives/bybit_v5.py",
        "src/galapagos/data/macro/fred_client.py",
        "reports/research/fred_macro_readiness_v1_12_2.json",
    ]:
        _touch(tmp_path, relative)
    (tmp_path / "data/gold/derivatives_features/BTCUSDT/4h").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data/silver/derivatives/binance/BTCUSDT").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data/gold/macro_features/4h").mkdir(parents=True, exist_ok=True)
    return tmp_path


def test_data_source_inventory_contains_required_sources_v9_14_1(tmp_path: Path) -> None:
    inventory = build_data_source_inventory_v9_14_1(_inventory_root(tmp_path))

    assert {item["source_name"] for item in inventory} == set(REQUIRED_SOURCE_NAMES)
    assert next(item for item in inventory if item["source_name"] == "ohlcv")["used_in_validated_v9_chain"] is True
    assert next(item for item in inventory if item["source_name"] == "public_trades_aggTrades")["used_in_validated_v9_chain"] is True


def test_data_source_inventory_proves_derivatives_are_priority_candidates_v9_14_1(tmp_path: Path) -> None:
    inventory = build_data_source_inventory_v9_14_1(_inventory_root(tmp_path))
    funding = next(item for item in inventory if item["source_name"] == "funding_rates")
    open_interest = next(item for item in inventory if item["source_name"] == "open_interest")

    assert funding["present_in_repo"] is True
    assert funding["used_in_validated_v9_chain"] is False
    assert funding["recommended_priority"] == "priority_1_candidate"
    assert open_interest["recommended_priority"] == "priority_1_candidate"


def test_data_source_inventory_does_not_claim_missing_order_book_v9_14_1(tmp_path: Path) -> None:
    inventory = build_data_source_inventory_v9_14_1(_inventory_root(tmp_path))
    order_book = next(item for item in inventory if item["source_name"] == "order_book_l2")

    assert order_book["present_in_repo"] is False
    assert order_book["evidence_paths"] == []
    assert order_book["recommended_priority"] == "missing_or_unknown"


def test_hypotheses_include_h9_h10_h11_v9_14_1(tmp_path: Path) -> None:
    inventory = build_data_source_inventory_v9_14_1(_inventory_root(tmp_path))
    hypotheses = classify_hypotheses_v9_14_1(
        {"flat_low_timeframes": ["1m"], "flat_high_timeframes": ["1h"]},
        {"no_clear_edge_vs_shuffled_labels_count": 14, "clear_wins_vs_baselines": 0},
        {"common_top_features_count": 0, "unstable_top_features_count": 10},
        inventory,
    )

    assert {item["id"] for item in hypotheses} == {f"H{index}" for index in range(1, 12)}
    assert next(item for item in hypotheses if item["id"] == "H11")["status"] == "likely"


def test_corrected_decision_prefers_data_extension_when_priority_sources_exist_v9_14_1(tmp_path: Path) -> None:
    inventory = build_data_source_inventory_v9_14_1(_inventory_root(tmp_path))
    decision = decide_v9_14_1(
        {"v9_14_decision": {"decision": "feature_first_before_more_labels"}},
        [],
        inventory,
        {"clear_wins_vs_baselines": 0},
        {"common_top_features_count": 0},
    )

    assert decision["previous_decision"] == "feature_first_before_more_labels"
    assert decision["decision"] == "data_extension_first_before_more_labels"
    assert "V9.15 Data Extension" in decision["next_recommendation"]


def test_data_extension_recommendation_lists_priorities_v9_14_1(tmp_path: Path) -> None:
    inventory = build_data_source_inventory_v9_14_1(_inventory_root(tmp_path))
    recommendation = build_data_extension_recommendation_v9_14_1(inventory, {"decision": "data_extension_first_before_more_labels", "next_recommendation": "V9.15"})

    assert "funding_rates" in recommendation["primary_sources"]
    assert "open_interest" in recommendation["primary_sources"]
    assert recommendation["no_backtest"] is True
    assert recommendation["no_walk_forward"] is True


def test_safety_flags_disable_execution_surfaces_v9_14_1() -> None:
    assert SAFETY_FLAGS["no_trading"] is True
    assert SAFETY_FLAGS["no_backtest"] is True
    assert SAFETY_FLAGS["no_walk_forward"] is True
    assert SAFETY_FLAGS["no_sidecars"] is True
