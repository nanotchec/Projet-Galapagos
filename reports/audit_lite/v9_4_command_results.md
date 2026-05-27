# Command Results V9.4

- Status : `PASS`.
- Created at UTC : `2026-05-27T09:10:43.587634Z`.

## PYTHONPATH=src python -m pytest --collect-only -q

- Status : `PASS`.
- Return code : `0`.
- Duration seconds : `1.934`.
- Timestamp UTC : `2026-05-27T09:10:39.660776Z`.

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

5213 tests collected in 1.58s
```

### Stderr tail
```

```

## PYTHONPATH=src python -m pytest -q tests/research/test_refined_research_decision_gate_v9_4.py

- Status : `PASS`.
- Return code : `0`.
- Duration seconds : `0.22`.
- Timestamp UTC : `2026-05-27T09:10:41.595334Z`.

### Stdout tail
```
......                                                                   [100%]
6 passed in 0.09s
```

### Stderr tail
```

```

## PYTHONPATH=src python -m pytest -q tests/validation/test_refined_research_decision_gate_v9_4_validator.py

- Status : `PASS`.
- Return code : `0`.
- Duration seconds : `0.246`.
- Timestamp UTC : `2026-05-27T09:10:41.815736Z`.

### Stdout tail
```
.........                                                                [100%]
9 passed in 0.11s
```

### Stderr tail
```

```

## python scripts/run_refined_research_decision_gate_v9_4.py

- Status : `PASS`.
- Return code : `0`.
- Duration seconds : `0.036`.
- Timestamp UTC : `2026-05-27T09:10:42.061274Z`.

### Stdout tail
```
{
  "version": "V9.4",
  "status": "PASS",
  "research_decision": "backtest_not_justified_refine_labels",
  "manifest": "reports/manifests/refined_research_decision_gate_v9_4_manifest.json",
  "decision_report": "reports/research_decisions/refined_research_decision_gate_v9_4.json"
}
```

### Stderr tail
```

```

## python scripts/validate_refined_research_decision_gate_v9_4.py

- Status : `PASS`.
- Return code : `0`.
- Duration seconds : `0.83`.
- Timestamp UTC : `2026-05-27T09:10:42.097793Z`.

### Stdout tail
```
            "5m": 0.3617734254570485
          },
          "worst_timeframe": "1h"
        },
        "majority_class_baseline": {
          "best_timeframe": "1m",
          "dominant_timeframe_warning": true,
          "macro_f1_range": 0.118637822469,
          "mean_test_macro_f1_by_timeframe": {
            "15m": 0.15181265040275366,
            "1h": 0.20897773706730657,
            "1m": 0.270450472871428,
            "5m": 0.18317720788644298
          },
          "worst_timeframe": "15m"
        },
        "random_seeded_baseline": {
          "best_timeframe": "1h",
          "dominant_timeframe_warning": false,
          "macro_f1_range": 0.013361888882,
          "mean_test_macro_f1_by_timeframe": {
            "15m": 0.3235384932216264,
            "1h": 0.3366848509206902,
            "1m": 0.32332296203827965,
            "5m": 0.3237656227865917
          },
          "worst_timeframe": "1m"
        }
      },
      "dominant_timeframe_warnings_count": 1,
      "verdict": "non_uniforme_entre_timeframes"
    },
    "version": "V9.4",
    "window": {
      "total_days": 366,
      "window_end": "2024-03-24",
      "window_start": "2023-03-25"
    }
  }
}
```

### Stderr tail
```

```

## python scripts/release_audit_lite_zip_v9_4.py

- Status : `PASS`.
- Return code : `0`.
- Duration seconds : `0.055`.
- Timestamp UTC : `2026-05-27T09:10:42.927543Z`.

### Stdout tail
```
{
  "version": "V9.4",
  "zip": "projet-galapagos-v9.4-audit-lite.zip",
  "zip_bytes": 260688,
  "zip_sha256": "9e767a55836673519952e2bdc0134d24c5a261d3481baa23a86b1eb1097bf66a",
  "included_files": 47,
  "sidecar_json": "projet-galapagos-v9.4-audit-lite.zip.sha256.json",
  "sidecar_txt": "projet-galapagos-v9.4-audit-lite.zip.sha256.txt",
  "status": "PASS"
}
```

### Stderr tail
```

```

## python scripts/audit_audit_lite_zip_v9_4.py --zip projet-galapagos-v9.4-audit-lite.zip

- Status : `PASS`.
- Return code : `0`.
- Duration seconds : `0.046`.
- Timestamp UTC : `2026-05-27T09:10:42.982986Z`.

### Stdout tail
```
{
  "version": "V9.4",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.4-audit-lite.zip",
  "passed": true,
  "errors": []
}
```

### Stderr tail
```

```

## python scripts/smoke_audit_lite_zip_v9_4.py --zip projet-galapagos-v9.4-audit-lite.zip

- Status : `PASS`.
- Return code : `0`.
- Duration seconds : `0.558`.
- Timestamp UTC : `2026-05-27T09:10:43.029407Z`.

### Stdout tail
```
{
  "version": "V9.4",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.4-audit-lite.zip",
  "passed": true,
  "errors": []
}
```

### Stderr tail
```

```
