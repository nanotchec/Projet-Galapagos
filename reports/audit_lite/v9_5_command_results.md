# Command Results V9.5

- Status : `PASS`.
- Created at UTC : `2026-05-27T10:01:04.998178Z`.

## PYTHONPATH=src python -m pytest --collect-only -q

- Status : `PASS`.
- Return code : `0`.
- Duration seconds : `2.248`.
- Timestamp UTC : `2026-05-27T10:00:57.524752Z`.

### Stdout tail
```
tests/validation/test_research_decision_gate_v8_1.py::test_validator_v8_1_rejects_empty_roadmap
tests/validation/test_research_decision_gate_v8_1.py::test_validator_v8_1_rejects_forbidden_markdown_claim
tests/validation/test_research_decision_gate_v8_1.py::test_validator_v8_1_rejects_forbidden_artifact
tests/validation/test_research_decision_gate_v8_6.py::test_decision_gate_v8_6_is_research_only
tests/validation/test_research_decision_gate_v8_6.py::test_decision_gate_v8_6_has_recommendation
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

5228 tests collected in 1.92s
```

### Stderr tail
```

```

## PYTHONPATH=src python -m pytest -q tests/research/test_alternative_label_design_audit_v9_5.py

- Status : `PASS`.
- Return code : `0`.
- Duration seconds : `1.798`.
- Timestamp UTC : `2026-05-27T10:00:59.773250Z`.

### Stdout tail
```
......                                                                   [100%]
6 passed in 1.65s
```

### Stderr tail
```

```

## PYTHONPATH=src python -m pytest -q tests/validation/test_alternative_label_design_audit_v9_5_validator.py

- Status : `PASS`.
- Return code : `0`.
- Duration seconds : `2.361`.
- Timestamp UTC : `2026-05-27T10:01:01.570779Z`.

### Stdout tail
```
.........                                                                [100%]
9 passed in 2.22s
```

### Stderr tail
```

```

## python scripts/run_alternative_label_design_audit_v9_5.py

- Status : `PASS`.
- Return code : `0`.
- Duration seconds : `0.366`.
- Timestamp UTC : `2026-05-27T10:01:03.932106Z`.

### Stdout tail
```
{
  "version": "V9.5",
  "status": "PASS",
  "decision": "label_redesign_candidate_volatility_normalized",
  "next_step": "V9.6 - Refined Label Factory Candidate",
  "report": "reports/research_decisions/alternative_label_design_audit_v9_5.json",
  "manifest": "reports/manifests/alternative_label_design_audit_v9_5_manifest.json"
}
```

### Stderr tail
```

```

## python scripts/validate_alternative_label_design_audit_v9_5.py

- Status : `PASS`.
- Return code : `0`.
- Duration seconds : `0.027`.
- Timestamp UTC : `2026-05-27T10:01:04.297836Z`.

### Stdout tail
```
{
  "version": "V9.5",
  "passed": true,
  "errors": []
}
```

### Stderr tail
```

```

## python scripts/release_audit_lite_zip_v9_5.py

- Status : `PASS`.
- Return code : `0`.
- Duration seconds : `0.058`.
- Timestamp UTC : `2026-05-27T10:01:04.324680Z`.

### Stdout tail
```
{
  "version": "V9.5",
  "zip": "projet-galapagos-v9.5-audit-lite.zip",
  "zip_bytes": 266721,
  "zip_sha256": "a83a48faf97f447ee20995e9b5614006607124a60484870e56bd44eec2738709",
  "included_files": 49,
  "sidecar_json": "projet-galapagos-v9.5-audit-lite.zip.sha256.json",
  "sidecar_txt": "projet-galapagos-v9.5-audit-lite.zip.sha256.txt",
  "status": "PASS"
}
```

### Stderr tail
```

```

## python scripts/audit_audit_lite_zip_v9_5.py --zip projet-galapagos-v9.5-audit-lite.zip

- Status : `PASS`.
- Return code : `0`.
- Duration seconds : `0.051`.
- Timestamp UTC : `2026-05-27T10:01:04.382795Z`.

### Stdout tail
```
{
  "version": "V9.5",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.5-audit-lite.zip",
  "passed": true,
  "errors": []
}
```

### Stderr tail
```

```

## python scripts/smoke_audit_lite_zip_v9_5.py --zip projet-galapagos-v9.5-audit-lite.zip

- Status : `PASS`.
- Return code : `0`.
- Duration seconds : `0.565`.
- Timestamp UTC : `2026-05-27T10:01:04.433485Z`.

### Stdout tail
```
{
  "version": "V9.5",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.5-audit-lite.zip",
  "passed": true,
  "errors": []
}
```

### Stderr tail
```

```
