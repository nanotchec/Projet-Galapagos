# Commandes V9.13

- Statut : `PASS`.
- Aucun sidecar et aucune empreinte ZIP.

## PASS - `PYTHONPATH=src python -m pytest --collect-only -q`
- Return code : `0`.
- Duree : `2.057` secondes.

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

5306 tests collected in 1.69s
```

## PASS - `PYTHONPATH=src python -m pytest -q tests/datasets/test_h4_label_candidate_dataset_v9_13.py`
- Return code : `0`.
- Duree : `0.426` secondes.

```text
....                                                                     [100%]
4 passed in 0.26s
```

## PASS - `PYTHONPATH=src python -m pytest -q tests/validation/test_h4_label_candidate_dataset_v9_13_validator.py`
- Return code : `0`.
- Duree : `0.444` secondes.

```text
......                                                                   [100%]
6 passed in 0.27s
```

## PASS - `python scripts/run_h4_label_candidate_dataset_v9_13.py`
- Return code : `0`.
- Duree : `6.02` secondes.

```text
{
  "version": "V9.13",
  "status": "PASS",
  "decision": "dataset_created_h4_label_candidate",
  "target_name": "up_down_flat_volnorm_h4",
  "outputs": {
    "1m": 527040,
    "5m": 105408,
    "15m": 35136,
    "1h": 8784
  }
}
```

## PASS - `python scripts/validate_h4_label_candidate_dataset_v9_13.py`
- Return code : `0`.
- Duree : `0.743` secondes.

```text
{
  "version": "V9.13",
  "component": "dataset",
  "passed": true,
  "errors": []
}
```

## PASS - `PYTHONPATH=src python -m pytest -q tests/ml/test_h4_label_candidate_offline_ml_v9_13.py`
- Return code : `0`.
- Duree : `1.332` secondes.

```text
......                                                                   [100%]
6 passed in 1.11s
```

## PASS - `PYTHONPATH=src python -m pytest -q tests/validation/test_h4_label_candidate_offline_ml_v9_13_validator.py`
- Return code : `0`.
- Duree : `1.22` secondes.

```text
.......                                                                  [100%]
7 passed in 1.00s
```

## PASS - `python scripts/run_h4_label_candidate_offline_ml_v9_13.py`
- Return code : `0`.
- Duree : `53.85` secondes.

```text
{
  "version": "V9.13",
  "status": "PASS",
  "decision": "h4_offline_ml_completed_but_close_to_shuffled_labels",
  "global_decision": "h4_candidate_not_ready_refine_labels_again",
  "target_name": "up_down_flat_volnorm_h4",
  "outputs": {
    "1m": 2106000,
    "5m": 421008,
    "15m": 140176,
    "1h": 34864
  }
}
```

## PASS - `python scripts/validate_h4_label_candidate_offline_ml_v9_13.py`
- Return code : `0`.
- Duree : `2.3` secondes.

```text
{
  "version": "V9.13",
  "component": "ml",
  "passed": true,
  "errors": []
}
```

## PASS - `python scripts/release_audit_lite_zip_v9_13.py`
- Return code : `0`.
- Duree : `1.307` secondes.

```text
{
  "version": "V9.13",
  "zip_name": "projet-galapagos-v9.13-audit-lite.zip",
  "zip_bytes": 388716,
  "included_files": 77,
  "sidecars_created": false,
  "zip_fingerprints_created": false,
  "status": "PASS"
}
```

## PASS - `python scripts/audit_audit_lite_zip_v9_13.py --zip projet-galapagos-v9.13-audit-lite.zip`
- Return code : `0`.
- Duree : `0.053` secondes.

```text
{
  "version": "V9.13",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.13-audit-lite.zip",
  "passed": true,
  "errors": []
}
```

## PASS - `python scripts/smoke_audit_lite_zip_v9_13.py --zip projet-galapagos-v9.13-audit-lite.zip`
- Return code : `0`.
- Duree : `6.345` secondes.

```text
{
  "version": "V9.13",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.13-audit-lite.zip",
  "passed": true,
  "errors": [],
  "import_timeout_seconds": 20,
  "pytest_timeout_seconds": 60,
  "test_timeout_seconds": 90,
  "sidecars_expected": false,
  "zip_fingerprints_expected": false
}
```
