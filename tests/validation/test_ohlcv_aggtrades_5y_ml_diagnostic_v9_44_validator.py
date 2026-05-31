from __future__ import annotations

import json

from galapagos.research.ohlcv_aggtrades_5y_ml_diagnostic_v9_44 import FINDINGS, SAFETY_FLAGS
from galapagos.research.ohlcv_aggtrades_5y_ml_diagnostic_v9_44_validation import validate_manifest_payload_v9_44, validate_report_payload_v9_44


def test_v9_44_validator_accepts_required_payload():
    report = _report()
    errors = validate_report_payload_v9_44(report)
    assert errors == []


def test_v9_44_validator_rejects_forbidden_network_and_backtest():
    report = _report()
    report["network_used"] = True
    report["backtest_executed"] = True
    report["safety_flags"]["network_used"] = True
    errors = validate_report_payload_v9_44(report)
    assert any("network_used" in error for error in errors)
    assert any("backtest_executed" in error for error in errors)


def test_v9_44_manifest_validator_rejects_zip_fingerprint_field():
    report = _report()
    manifest = {"version": "V9.44", "source_version": "V9.43", "decision": report["decision"], "safety_flags": report["safety_flags"], "zip_sha256": "forbidden"}
    errors = validate_manifest_payload_v9_44(manifest, report)
    assert any("ZIP fingerprint" in error for error in errors)


def _report():
    return json.loads(
        json.dumps(
            {
                "version": "V9.44",
                "source_version": "V9.43",
                "decision": "feature_enrichment_before_more_ml",
                "diagnostic_only": True,
                "heavy_ml_executed": False,
                "walk_forward_executed": False,
                "backtest_executed": False,
                "signal_created": False,
                "strategy_created": False,
                "model_persisted": False,
                "network_used": False,
                "new_data_downloaded": False,
                "findings": FINDINGS,
                "safety_flags": SAFETY_FLAGS,
                "ml_result_summary": {"baseline_clear_wins_count": 0, "no_clear_edge_vs_shuffled_labels_count": 15},
                "label_diagnostic": {},
                "feature_diagnostic": {},
                "option_comparison": {},
            }
        )
    )
