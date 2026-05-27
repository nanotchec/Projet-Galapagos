# Commandes V9.11

- Statut global : `PASS`.
- Aucun sidecar et aucune empreinte ZIP.

## PASS - `PYTHONPATH=src python -m pytest --collect-only -q`
- Returncode : `0`.
- Duree secondes : `1.901`.
- Timestamp UTC : `2026-05-27T12:59:08Z`.

```text
/validation/test_research_decision_gate_v8_6.py::test_decision_gate_v8_6_has_recommendation
tests/validation/test_research_decision_gate_v8_6.py::test_decision_gate_v8_6_claims_false
tests/validation/test_research_decision_gate_v8_6.py::test_decision_gate_v8_6_no_backtest_claim
tests/validation/test_research_decision_gate_v8_6.py::test_decision_gate_v8_6_rejects_claim_true
tests/validation/test_research_decision_gate_v8_8.py::test_decision_gate_v8_8_is_research_only
tests/validation/test_research_decision_gate_v8_8.py::test_decision_gate_v8_8_has_feature_refinement_recommendation
tests/validation/test_research_decision_gate_v8_8.py::test_decision_gate_v8_8_preserves_label_shuffle_warning_count
tests/validation/test_research_decision_gate_v8_8.py::test_decision_gate_v8_8_claims_false
tests/validation/test_research_decision_gate_v8_8.py::test_decision_gate_v8_8_no_backtest_recommendation
tests/validation/test_research_decision_gate_v8_8.py::test_decision_gate_v8_8_rejects_claim_true
tests/validation/test_research_decision_gate_v8_8.py::test_decision_gate_v8_8_rejects_backtest_primary_recommendation
tests/validation/test_research_decision_gate_v8_8.py::test_decision_gate_v8_8_rejects_forbidden_markdown_claim
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_accepts_valid_walk_forward_report
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_forbidden_future_feature
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_forbidden_label_feature
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_forbidden_fold_feature
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_unknown_model
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_output_trading_signal_column
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_output_order_column
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_output_pnl_column
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_overlapping_folds
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_validation_before_train
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_test_before_validation
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_backtest_report_created
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_strategy_report_created
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_orders_directory_created
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_model_pickle_created
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_markdown_strategy_validated_claim
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_markdown_tradable_edge_confirmed_claim
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_safety_flag_trading_true
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_safety_flag_backtest_true
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_walk_forward_validated_for_trading_true
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_trading_metric_in_metrics
tests/validation/test_strict_walk_forward_validation_v8_7_validator.py::test_validator_v8_7_rejects_report_json_lie

5270 tests collected in 1.59s

```

## PASS - `PYTHONPATH=src python -m pytest -q tests/research/test_label_failure_analysis_v9_11.py`
- Returncode : `0`.
- Duree secondes : `0.407`.
- Timestamp UTC : `2026-05-27T12:59:10Z`.

```text
....                                                                     [100%]
4 passed in 0.25s

```

## PASS - `PYTHONPATH=src python -m pytest -q tests/validation/test_label_failure_analysis_v9_11_validator.py`
- Returncode : `0`.
- Duree secondes : `0.409`.
- Timestamp UTC : `2026-05-27T12:59:11Z`.

```text
......                                                                   [100%]
6 passed in 0.24s

```

## PASS - `python scripts/run_label_failure_analysis_v9_11.py`
- Returncode : `0`.
- Duree secondes : `1.704`.
- Timestamp UTC : `2026-05-27T12:59:11Z`.

```text
{
  "version": "V9.11",
  "status": "PASS",
  "decision": "label_redesign_plan_horizon_extension"
}

```

## PASS - `python scripts/validate_label_failure_analysis_v9_11.py`
- Returncode : `0`.
- Duree secondes : `0.287`.
- Timestamp UTC : `2026-05-27T12:59:13Z`.

```text
{
  "version": "V9.11",
  "passed": true,
  "errors": []
}

```

## PASS - `python scripts/release_audit_lite_zip_v9_11.py`
- Returncode : `0`.
- Duree secondes : `3.044`.
- Timestamp UTC : `2026-05-27T12:59:13Z`.

```text
{
  "version": "V9.11",
  "zip_name": "projet-galapagos-v9.11-audit-lite.zip",
  "zip_bytes": 1362090,
  "included_files": 1091,
  "sidecars_created": false,
  "zip_fingerprints_created": false,
  "status": "PASS"
}

```

## PASS - `python scripts/audit_audit_lite_zip_v9_11.py --zip projet-galapagos-v9.11-audit-lite.zip`
- Returncode : `0`.
- Duree secondes : `0.198`.
- Timestamp UTC : `2026-05-27T12:59:16Z`.

```text
{
  "version": "V9.11",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.11-audit-lite.zip",
  "passed": true,
  "errors": []
}

```

## PASS - `python scripts/smoke_audit_lite_zip_v9_11.py --zip projet-galapagos-v9.11-audit-lite.zip`
- Returncode : `0`.
- Duree secondes : `1.593`.
- Timestamp UTC : `2026-05-27T12:59:16Z`.

```text
{
  "version": "V9.11",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.11-audit-lite.zip",
  "passed": true,
  "errors": [],
  "import_timeout_seconds": 20,
  "pytest_timeout_seconds": 60,
  "sidecars_expected": false,
  "zip_fingerprints_expected": false
}

```
