from __future__ import annotations
import pytest
from galapagos.research.microstructure_adapter_field_coverage.required_field_classifier import RequiredFieldClassifier
from galapagos.research.microstructure_adapter_field_coverage.adapter_field_gap_analyzer import AdapterFieldGapAnalyzer
from galapagos.research.microstructure_adapter_field_coverage.optional_field_policy import OptionalFieldPolicy
from galapagos.research.microstructure_adapter_field_coverage.coverage_decision import CoverageDecisionEngine

def test_classifier_categorization():
    spec = ["open_5m", "high_5m", "quote_asset_volume_5m", "taker_buy_base_asset_volume_5m"]
    classifier = RequiredFieldClassifier(spec)
    res = classifier.classify()
    
    assert "open" in res["mandatory_for_offline_review"]
    assert "quote_asset_volume" in res["mandatory_for_offline_review"]
    assert "taker_buy_base_asset_volume" in res["optional_for_real_collection"]
    assert res["field_alias_map"]["quote_asset_volume"] == "quote_volume"

def test_gap_analysis_mapping():
    classification = {
        "mandatory_for_offline_review": ["open", "quote_asset_volume"],
        "optional_for_real_collection": ["taker_buy_base_asset_volume"],
        "field_alias_map": {"open": "open", "quote_asset_volume": "quote_volume", "taker_buy_base_asset_volume": "taker_buy_base_volume"}
    }
    mapped = {"binance": ["open", "high", "low", "close", "volume", "quote_volume"]}
    analyzer = AdapterFieldGapAnalyzer(classification)
    res = analyzer.analyze(mapped)
    
    assert "open" in res["binance"]["covered_required_fields"]
    assert "quote_asset_volume" in res["binance"]["covered_required_fields"]
    assert "taker_buy_base_asset_volume" in res["binance"]["still_missing_optional"]

def test_policy_downgrade_bybit():
    gap_report = {
        "bybit": {
            "covered_required_fields": ["open", "high", "low", "close", "volume", "quote_asset_volume"],
            "still_missing_mandatory": ["number_of_trades"],
            "still_missing_optional": ["taker_buy_base_asset_volume", "taker_buy_quote_asset_volume"]
        }
    }
    policy = OptionalFieldPolicy(gap_report)
    res = policy.apply()
    
    assert res["bybit"]["remaining_mandatory_for_offline_review"] == []
    assert res["bybit"]["downgraded_to_optional_fields"][0]["field"] == "number_of_trades"

def test_decision_engine_ready():
    policy_report = {"binance": {"remaining_mandatory_for_offline_review": []}, "bybit": {"remaining_mandatory_for_offline_review": []}}
    gap_report = {}
    engine = CoverageDecisionEngine(policy_report, gap_report)
    res = engine.compute()
    
    assert res["contract_ready_for_offline_review"] == True
    assert res["verdict"] == "MICROSTRUCTURE_FIELD_COVERAGE_READY_FOR_OFFLINE_REVIEW"
