# Commandes V9.14

- Statut : `PASS`.
- Aucun sidecar et aucune empreinte ZIP.

## PASS - `PYTHONPATH=src python -m pytest --collect-only -q`
- Return code : `0`.
- Duree : `2.633` secondes.

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

5321 tests collected in 2.26s
```

## PASS - `PYTHONPATH=src python -m pytest -q tests/research/test_feature_label_separability_v9_14.py`
- Return code : `0`.
- Duree : `0.475` secondes.

```text
......                                                                   [100%]
6 passed in 0.29s
```

## PASS - `PYTHONPATH=src python -m pytest -q tests/validation/test_feature_label_separability_v9_14_validator.py`
- Return code : `0`.
- Duree : `0.455` secondes.

```text
.........                                                                [100%]
9 passed in 0.27s
```

## PASS - `python scripts/run_feature_label_separability_v9_14.py`
- Return code : `0`.
- Duree : `4.335` secondes.

```text
{
  "version": "V9.14",
  "status": "PASS",
  "decision": "feature_first_before_more_labels",
  "target_name": "up_down_flat_volnorm_h4",
  "full_data_available": true,
  "no_backtest": true,
  "no_walk_forward": true
}
```

## PASS - `python scripts/validate_feature_label_separability_v9_14.py`
- Return code : `0`.
- Duree : `0.474` secondes.

```text
{
  "version": "V9.14",
  "passed": true,
  "errors": []
}
```

## PASS - `python scripts/release_audit_lite_zip_v9_14.py`
- Return code : `0`.
- Duree : `0.115` secondes.

```text
{
  "version": "V9.14",
  "zip_name": "projet-galapagos-v9.14-audit-lite.zip",
  "zip_bytes": 384550,
  "included_files": 53,
  "sidecars_created": false,
  "zip_fingerprints_created": false,
  "status": "PASS"
}
```

## PASS - `python scripts/audit_audit_lite_zip_v9_14.py --zip projet-galapagos-v9.14-audit-lite.zip`
- Return code : `0`.
- Duree : `0.048` secondes.

```text
{
  "version": "V9.14",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.14-audit-lite.zip",
  "passed": true,
  "errors": []
}
```

## PASS - `python scripts/smoke_audit_lite_zip_v9_14.py --zip projet-galapagos-v9.14-audit-lite.zip`
- Return code : `0`.
- Duree : `1.87` secondes.

```text
{
  "version": "V9.14",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.14-audit-lite.zip",
  "passed": true,
  "errors": [],
  "import_timeout_seconds": 20,
  "pytest_timeout_seconds": 60,
  "test_timeout_seconds": 60,
  "sample_timeout_seconds": 40,
  "sidecars_expected": false,
  "zip_fingerprints_expected": false
}
```
