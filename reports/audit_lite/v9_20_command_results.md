# Commandes V9.20

## PASS - `PYTHONPATH=src python -m pytest --collect-only -q`
- Timestamp UTC : `2026-05-27T20:49:05Z`.
- Returncode : `0`.
- Duree secondes : `4.648`.
- Stdout tail :

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

5440 tests collected in 4.24s

```
- Stderr tail :

```text

```

## PASS - `PYTHONPATH=src python -m pytest -q tests/data/test_aggtrades_post_v9_batch_collection_v9_20.py`
- Timestamp UTC : `2026-05-27T20:49:10Z`.
- Returncode : `0`.
- Duree secondes : `0.527`.
- Stdout tail :

```text
...........                                                              [100%]
11 passed in 0.33s

```
- Stderr tail :

```text

```

## PASS - `PYTHONPATH=src python -m pytest -q tests/validation/test_aggtrades_post_v9_batch_collection_v9_20_validator.py`
- Timestamp UTC : `2026-05-27T20:49:11Z`.
- Returncode : `0`.
- Duree secondes : `0.192`.
- Stdout tail :

```text
.........                                                                [100%]
9 passed in 0.03s

```
- Stderr tail :

```text

```

## PASS - `python scripts/run_aggtrades_post_v9_batch_collection_v9_20.py --mode collect --start-date 2024-05-12 --end-date 2024-06-10 --max-downloads 30`
- Timestamp UTC : `2026-05-27T20:49:11Z`.
- Returncode : `0`.
- Duree secondes : `282.318`.
- Stdout tail :

```text
{
  "version": "V9.20",
  "status": "PASS",
  "mode": "collect",
  "decision": "aggtrades_post_v9_batch_collection_success",
  "batch_start": "2024-05-12",
  "batch_end": "2024-06-10",
  "max_downloads": 30,
  "days_requested": 30,
  "days_attempted": 30,
  "days_downloaded": 30,
  "days_normalized": 30,
  "days_skipped_existing": 0,
  "days_complete": 30,
  "days_failed": 0,
  "total_rows": 27668612,
  "raw_bytes_total": 365946254,
  "silver_bytes_total": 718259780,
  "runtime_seconds": 282.14,
  "cumulative_known_coverage_start": "2024-05-05",
  "cumulative_known_coverage_end": "2024-06-10",
  "network_used": true,
  "api_key_used": false,
  "private_endpoint_used": false,
  "exchange_auth_used": false,
  "websocket_live_used": false,
  "complete_collection_reached": false
}

```
- Stderr tail :

```text

```

## PASS - `python scripts/validate_aggtrades_post_v9_batch_collection_v9_20.py`
- Timestamp UTC : `2026-05-27T20:53:53Z`.
- Returncode : `0`.
- Duree secondes : `0.533`.
- Stdout tail :

```text
{
  "version": "V9.20",
  "passed": true,
  "errors": []
}

```
- Stderr tail :

```text

```

## PASS - `python scripts/release_audit_lite_zip_v9_20.py`
- Timestamp UTC : `2026-05-27T20:53:54Z`.
- Returncode : `0`.
- Duree secondes : `0.588`.
- Stdout tail :

```text
{
  "version": "V9.20",
  "zip_name": "projet-galapagos-v9.20-audit-lite.zip",
  "zip_bytes_estimate": 237647,
  "zip_bytes_is_authoritative": false,
  "included_files": 48,
  "sidecars_created": false,
  "zip_fingerprints_created": false,
  "status": "PASS"
}

```
- Stderr tail :

```text

```

## PASS - `python scripts/release_audit_lite_zip_v9_20.py`
- Timestamp UTC : `2026-05-27T20:53:54Z`.
- Returncode : `0`.
- Duree secondes : `0.107`.
- Stdout tail :

```text
{
  "version": "V9.20",
  "zip_name": "projet-galapagos-v9.20-audit-lite.zip",
  "zip_bytes_estimate": 237893,
  "zip_bytes_is_authoritative": false,
  "included_files": 48,
  "sidecars_created": false,
  "zip_fingerprints_created": false,
  "status": "PASS"
}

```
- Stderr tail :

```text

```

## PASS - `python scripts/audit_audit_lite_zip_v9_20.py --zip projet-galapagos-v9.20-audit-lite.zip`
- Timestamp UTC : `2026-05-27T20:53:54Z`.
- Returncode : `0`.
- Duree secondes : `0.051`.
- Stdout tail :

```text
{
  "version": "V9.20",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.20-audit-lite.zip",
  "passed": true,
  "errors": []
}

```
- Stderr tail :

```text

```

## PASS - `python scripts/smoke_audit_lite_zip_v9_20.py --zip projet-galapagos-v9.20-audit-lite.zip`
- Timestamp UTC : `2026-05-27T20:53:54Z`.
- Returncode : `0`.
- Duree secondes : `1.377`.
- Stdout tail :

```text
{
  "version": "V9.20",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.20-audit-lite.zip",
  "passed": true,
  "errors": [],
  "import_timeout_seconds": 20,
  "pytest_timeout_seconds": 60,
  "test_timeout_seconds": 90,
  "audit_timeout_seconds": 30,
  "sidecars_expected": false,
  "zip_fingerprints_expected": false
}

```
- Stderr tail :

```text

```

## PASS - `python scripts/release_audit_lite_zip_v9_20.py`
- Timestamp UTC : `2026-05-27T20:53:56Z`.
- Returncode : `0`.
- Duree secondes : `0.106`.
- Stdout tail :

```text
{
  "version": "V9.20",
  "zip_name": "projet-galapagos-v9.20-audit-lite.zip",
  "zip_bytes_estimate": 238362,
  "zip_bytes_is_authoritative": false,
  "included_files": 48,
  "sidecars_created": false,
  "zip_fingerprints_created": false,
  "status": "PASS"
}

```
- Stderr tail :

```text

```

## PASS - `python scripts/audit_audit_lite_zip_v9_20.py --zip projet-galapagos-v9.20-audit-lite.zip`
- Timestamp UTC : `2026-05-27T20:53:56Z`.
- Returncode : `0`.
- Duree secondes : `0.047`.
- Stdout tail :

```text
{
  "version": "V9.20",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.20-audit-lite.zip",
  "passed": true,
  "errors": []
}

```
- Stderr tail :

```text

```

## PASS - `python scripts/smoke_audit_lite_zip_v9_20.py --zip projet-galapagos-v9.20-audit-lite.zip`
- Timestamp UTC : `2026-05-27T20:53:56Z`.
- Returncode : `0`.
- Duree secondes : `1.255`.
- Stdout tail :

```text
{
  "version": "V9.20",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.20-audit-lite.zip",
  "passed": true,
  "errors": [],
  "import_timeout_seconds": 20,
  "pytest_timeout_seconds": 60,
  "test_timeout_seconds": 90,
  "audit_timeout_seconds": 30,
  "sidecars_expected": false,
  "zip_fingerprints_expected": false
}

```
- Stderr tail :

```text

```
