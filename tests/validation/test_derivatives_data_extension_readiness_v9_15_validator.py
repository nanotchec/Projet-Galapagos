from __future__ import annotations

from copy import deepcopy

from galapagos.research.derivatives_data_extension_readiness_v9_15 import FINDINGS, SAFETY, SAFETY_FLAGS, VERSION
from galapagos.research.derivatives_data_extension_readiness_v9_15_validation import (
    validate_manifest_payload_v9_15,
    validate_markdown_v9_15,
    validate_report_payload_v9_15,
    validate_source_readiness_v9_15,
)


def _source(name: str) -> dict:
    return {
        "source_name": name,
        "present_local": True,
        "evidence_paths": ["reports/research/derivatives_coverage_v1_14.json"],
        "compatible_with_v9_window": False,
        "readiness_decision": "not_ready_missing_coverage",
        "coverage_checks": [{"overlaps_v9_window": False}],
    }


def _valid_report() -> dict:
    return {
        "version": VERSION,
        "status": "PASS",
        "v9_15_decision": {"decision": "derivatives_readiness_not_compatible_with_v9_window"},
        "features_candidate_created": False,
        "funding_readiness": _source("funding_rates"),
        "open_interest_readiness": _source("open_interest"),
        "v9_chain_compatibility": {"compatible_with_current_v9_chain": False, "alignment_possible_now": False},
        "feature_candidate": {"created": False},
        "findings": dict(FINDINGS),
        "safety": dict(SAFETY),
        "safety_flags": dict(SAFETY_FLAGS),
    }


def test_validator_accepts_valid_report_v9_15() -> None:
    assert validate_report_payload_v9_15(_valid_report()) == []


def test_validator_rejects_feature_candidate_created_v9_15() -> None:
    report = _valid_report()
    report["features_candidate_created"] = True

    assert "V9.15 should not create features when V9 window is incompatible" in validate_report_payload_v9_15(report)


def test_validator_rejects_source_overlap_with_v9_v9_15() -> None:
    source = _source("funding_rates")
    source["compatible_with_v9_window"] = True

    assert "V9.15 source must not overlap current V9 window: funding_rates" in validate_source_readiness_v9_15(source, "funding_rates")


def test_validator_rejects_missing_evidence_v9_15() -> None:
    source = _source("open_interest")
    source["evidence_paths"] = []

    assert "V9.15 source lacks evidence paths: open_interest" in validate_source_readiness_v9_15(source, "open_interest")


def test_validator_rejects_network_used_true_v9_15() -> None:
    report = _valid_report()
    report["safety_flags"]["network_used"] = True

    assert "V9.15 safety flag mismatch: network_used" in validate_report_payload_v9_15(report)


def test_validator_rejects_new_data_download_false_flag_v9_15() -> None:
    report = _valid_report()
    report["safety_flags"]["no_new_data_download"] = False

    assert "V9.15 safety flag mismatch: no_new_data_download" in validate_report_payload_v9_15(report)


def test_validator_rejects_sidecar_field_v9_15() -> None:
    report = _valid_report()
    manifest = deepcopy(report)
    manifest.update(
        {
            "version": VERSION,
            "status": "PASS",
            "v9_15_decision": {"decision": "derivatives_readiness_not_compatible_with_v9_window"},
            "features_candidate_created": False,
            "compatible_with_current_v9_chain": False,
            "sidecar_json": "forbidden",
        }
    )

    assert "V9.15 manifest must not contain sidecar or ZIP hash fields" in validate_manifest_payload_v9_15(manifest, report)


def test_validator_rejects_strategy_validated_true_v9_15() -> None:
    report = _valid_report()
    report["findings"]["strategy_validated"] = True

    assert "V9.15 findings mismatch" in validate_report_payload_v9_15(report)


def test_validator_rejects_markdown_forbidden_claim_v9_15() -> None:
    text = "Funding readiness. Open interest readiness. Aucun backtest. Aucun trading. Aucun ordre. Aucune strategie. Aucun signal actionnable. Aucun walk-forward. Aucun reseau. Aucun telechargement. tradable edge confirmed"

    assert any("forbidden claim" in error for error in validate_markdown_v9_15(text))


def test_validator_rejects_markdown_trading_metric_v9_15() -> None:
    text = "Funding readiness. Open interest readiness. Aucun backtest. Aucun trading. Aucun ordre. Aucune strategie. Aucun signal actionnable. Aucun walk-forward. Aucun reseau. Aucun telechargement. Sharpe."

    assert any("forbidden metric term" in error for error in validate_markdown_v9_15(text))
