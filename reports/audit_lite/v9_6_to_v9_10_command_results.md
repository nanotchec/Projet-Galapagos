# Commandes V9.6 -> V9.10

- Statut global : `PASS`.
- Aucun sidecar et aucune empreinte ZIP.

## PASS - `PYTHONPATH=src python -m pytest --collect-only -q`
- Returncode : `0`.
- Duree secondes : `2.255`.
- Timestamp UTC : `2026-05-27T12:24:23Z`.

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

5260 tests collected in 1.86s

```

## PASS - `PYTHONPATH=src python -m pytest -q tests/labels/test_refined_volatility_normalized_labels_v9_6.py`
- Returncode : `0`.
- Duree secondes : `0.452`.
- Timestamp UTC : `2026-05-27T12:24:25Z`.

```text
....                                                                     [100%]
4 passed in 0.28s

```

## PASS - `PYTHONPATH=src python -m pytest -q tests/validation/test_refined_volatility_normalized_labels_v9_6_validator.py`
- Returncode : `0`.
- Duree secondes : `0.431`.
- Timestamp UTC : `2026-05-27T12:24:26Z`.

```text
....                                                                     [100%]
4 passed in 0.26s

```

## PASS - `python scripts/run_refined_volatility_normalized_labels_v9_6.py`
- Returncode : `0`.
- Duree secondes : `12.128`.
- Timestamp UTC : `2026-05-27T12:24:26Z`.

```text
{
  "version": "V9.6",
  "status": "PASS",
  "decision": "label_factory_candidate_created_volatility_normalized",
  "selected_volatility_threshold_multiplier": 0.5,
  "outputs": {
    "1m": {
      "path": "data/research/v9_6/labels/refined_volatility_normalized/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2024-03-24/labels.parquet",
      "sha256": "57ed4fb1691a5b7c44b27c68768fab1839baed14dc5c7bbc3bbb24d7a58e5143",
      "bytes": 37421588,
      "rows": 527040,
      "format": "parquet"
    },
    "5m": {
      "path": "data/research/v9_6/labels/refined_volatility_normalized/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2024-03-24/labels.parquet",
      "sha256": "db3505832e75cde50c4745db1472e3acd30f8a837b434d9192c59274c8089b0f",
      "bytes": 9047938,
      "rows": 105408,
      "format": "parquet"
    },
    "15m": {
      "path": "data/research/v9_6/labels/refined_volatility_normalized/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2024-03-24/labels.parquet",
      "sha256": "3bab9373a0249d142207a6168cf761c6465768e6b4fe1f59816fa37e7515ee19",
      "bytes": 3070590,
      "rows": 35136,
      "format": "parquet"
    },
    "1h": {
      "path": "data/research/v9_6/labels/refined_volatility_normalized/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2024-03-24/labels.parquet",
      "sha256": "b3e0930b1d383c473485609a24f03aafed265fad2c32d494a4f3308bd4bb7f50",
      "bytes": 754170,
      "rows": 8784,
      "format": "parquet"
    }
  }
}

```

## PASS - `python scripts/validate_refined_volatility_normalized_labels_v9_6.py`
- Returncode : `0`.
- Duree secondes : `0.995`.
- Timestamp UTC : `2026-05-27T12:24:38Z`.

```text
  "timeframe": "15m",
        "valid_rows": 35076,
        "warmup_rows": 60,
        "warnings": []
      },
      "1h": {
        "class_distribution": {
          "DOWN": {
            "count": 2098,
            "rate": 0.24048601558917929
          },
          "FLAT": {
            "count": 4361,
            "rate": 0.49988537368179736
          },
          "UP": {
            "count": 2265,
            "rate": 0.2596286107290234
          }
        },
        "entropy_bits": 1.4995859207867168,
        "errors": [],
        "fixed_label_distribution_h1": {
          "DOWN": {
            "count": 3585,
            "rate": 0.40812841530054644
          },
          "FLAT": {
            "count": 1431,
            "rate": 0.16290983606557377
          },
          "UP": {
            "count": 3768,
            "rate": 0.42896174863387976
          }
        },
        "flat_rate_reduction_vs_fixed_h1": -0.33697553761622356,
        "invalid_rows": 60,
        "majority_class": "FLAT",
        "majority_rate": 0.49988537368179736,
        "rows": 8784,
        "timeframe": "1h",
        "valid_rows": 8724,
        "warmup_rows": 60,
        "warnings": []
      },
      "1m": {
        "class_distribution": {
          "DOWN": {
            "count": 139523,
            "rate": 0.26475957341834605
          },
          "FLAT": {
            "count": 246639,
            "rate": 0.4680234544005465
          },
          "UP": {
            "count": 140818,
            "rate": 0.26721697218110746
          }
        },
        "entropy_bits": 1.5290160328404434,
        "errors": [],
        "fixed_label_distribution_h1": {
          "DOWN": {
            "count": 60407,
            "rate": 0.11461558894960534
          },
          "FLAT": {
            "count": 405035,
            "rate": 0.7685090315725561
          },
          "UP": {
            "count": 61598,
            "rate": 0.11687537947783849
          }
        },
        "flat_rate_reduction_vs_fixed_h1": 0.30048557717200963,
        "invalid_rows": 60,
        "majority_class": "FLAT",
        "majority_rate": 0.4680234544005465,
        "rows": 527040,
        "timeframe": "1m",
        "valid_rows": 526980,
        "warmup_rows": 60,
        "warnings": []
      },
      "5m": {
        "class_distribution": {
          "DOWN": {
            "count": 29411,
            "rate": 0.27917948133804155
          },
          "FLAT": {
            "count": 45739,
            "rate": 0.43417055852982495
          },
          "UP": {
            "count": 30198,
            "rate": 0.2866499601321335
          }
        },
        "entropy_bits": 1.5532180336046384,
        "errors": [],
        "fixed_label_distribution_h1": {
          "DOWN": {
            "count": 27243,
            "rate": 0.258452868852459
          },
          "FLAT": {
            "count": 50140,
            "rate": 0.47567547055251974
          },
          "UP": {
            "count": 28025,
            "rate": 0.26587166059502126
          }
        },
        "flat_rate_reduction_vs_fixed_h1": 0.041504912022694795,
        "invalid_rows": 60,
        "majority_class": "FLAT",
        "majority_rate": 0.43417055852982495,
        "rows": 105408,
        "timeframe": "5m",
        "valid_rows": 105348,
        "warmup_rows": 60,
        "warnings": []
      }
    },
    "safety": {
      "api_key_used": false,
      "authentication_used": false,
      "backtest_enabled": false,
      "dataset_enabled": false,
      "execution_enabled": false,
      "labels_enabled": true,
      "ml_enabled": false,
      "orders_enabled": false,
      "paper_live_enabled": false,
      "persistent_model_created": false,
      "private_endpoint_used": false,
      "public_read_only": true,
      "strategy_enabled": false,
      "trading_enabled": false
    },
    "selected_volatility_threshold_multiplier": 0.5,
    "status": "PASS",
    "target_name": "up_down_flat_volnorm_h1",
    "version": "V9.6"
  }
}

```

## PASS - `PYTHONPATH=src python -m pytest -q tests/datasets/test_refined_volnorm_labels_dataset_v9_7.py`
- Returncode : `0`.
- Duree secondes : `0.411`.
- Timestamp UTC : `2026-05-27T12:24:39Z`.

```text
...                                                                      [100%]
3 passed in 0.25s

```

## PASS - `PYTHONPATH=src python -m pytest -q tests/validation/test_refined_volnorm_labels_dataset_v9_7_validator.py`
- Returncode : `0`.
- Duree secondes : `0.426`.
- Timestamp UTC : `2026-05-27T12:24:39Z`.

```text
...                                                                      [100%]
3 passed in 0.26s

```

## PASS - `python scripts/run_refined_volnorm_labels_dataset_v9_7.py`
- Returncode : `0`.
- Duree secondes : `5.02`.
- Timestamp UTC : `2026-05-27T12:24:40Z`.

```text
{
  "version": "V9.7",
  "status": "PASS",
  "decision": "dataset_created_with_volnorm_labels",
  "outputs": {
    "1m": {
      "path": "data/research/v9_7/datasets/refined_volnorm_labels/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2024-03-24/dataset.parquet",
      "sha256": "4f080f36bc917e4a948607f291d8569bda8276aad9cd54f701a41457f0f4a3ea",
      "bytes": 99405645,
      "rows": 527040,
      "format": "parquet"
    },
    "5m": {
      "path": "data/research/v9_7/datasets/refined_volnorm_labels/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2024-03-24/dataset.parquet",
      "sha256": "489c3bdcb54ce3e5b61c65f56db34057e874f8983685910b6e1c077bf82eba3e",
      "bytes": 24593049,
      "rows": 105408,
      "format": "parquet"
    },
    "15m": {
      "path": "data/research/v9_7/datasets/refined_volnorm_labels/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2024-03-24/dataset.parquet",
      "sha256": "e9d4be6de1170c57df603f2630ad8581b62ab8abf026aa2deff68f42351a7b6e",
      "bytes": 8457292,
      "rows": 35136,
      "format": "parquet"
    },
    "1h": {
      "path": "data/research/v9_7/datasets/refined_volnorm_labels/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2024-03-24/dataset.parquet",
      "sha256": "2abe6a6f9342d36005c982ee36457406cac7650e866ed8819effb235486aacb2",
      "bytes": 2144102,
      "rows": 8784,
      "format": "parquet"
    }
  }
}

```

## PASS - `python scripts/validate_refined_volnorm_labels_dataset_v9_7.py`
- Returncode : `0`.
- Duree secondes : `1.052`.
- Timestamp UTC : `2026-05-27T12:24:45Z`.

```text
023_09",
          "wf_2023_10",
          "wf_2023_11",
          "wf_2023_12",
          "wf_2024_01",
          "wf_2024_02",
          "wf_2024_03"
        ],
        "warnings": []
      },
      "1m": {
        "errors": [],
        "forbidden_columns_present": [],
        "rows_invalid_labels": 60,
        "rows_total": 527040,
        "rows_valid_labels": 526980,
        "split_counts": {
          "test": 105408,
          "train": 316224,
          "validation": 105408
        },
        "timeframe": "1m",
        "walk_forward_groups": [
          "wf_2023_03",
          "wf_2023_04",
          "wf_2023_05",
          "wf_2023_06",
          "wf_2023_07",
          "wf_2023_08",
          "wf_2023_09",
          "wf_2023_10",
          "wf_2023_11",
          "wf_2023_12",
          "wf_2024_01",
          "wf_2024_02",
          "wf_2024_03"
        ],
        "warnings": []
      },
      "5m": {
        "errors": [],
        "forbidden_columns_present": [],
        "rows_invalid_labels": 60,
        "rows_total": 105408,
        "rows_valid_labels": 105348,
        "split_counts": {
          "test": 21083,
          "train": 63244,
          "validation": 21081
        },
        "timeframe": "5m",
        "walk_forward_groups": [
          "wf_2023_03",
          "wf_2023_04",
          "wf_2023_05",
          "wf_2023_06",
          "wf_2023_07",
          "wf_2023_08",
          "wf_2023_09",
          "wf_2023_10",
          "wf_2023_11",
          "wf_2023_12",
          "wf_2024_01",
          "wf_2024_02",
          "wf_2024_03"
        ],
        "warnings": []
      }
    },
    "safety": {
      "api_key_used": false,
      "authentication_used": false,
      "backtest_enabled": false,
      "dataset_enabled": true,
      "execution_enabled": false,
      "labels_enabled": true,
      "ml_enabled": false,
      "orders_enabled": false,
      "paper_live_enabled": false,
      "persistent_model_created": false,
      "private_endpoint_used": false,
      "public_read_only": true,
      "strategy_enabled": false,
      "trading_enabled": false
    },
    "split_policy": {
      "shuffle": false,
      "test_ratio": 0.2,
      "train_ratio": 0.6,
      "validation_ratio": 0.2,
      "walk_forward_group": "calendar_month"
    },
    "splits": {
      "15m": {
        "bytes": 1211119,
        "format": "parquet",
        "path": "data/research/v9_7/datasets/refined_volnorm_labels/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2024-03-24/splits.parquet",
        "rows": 35136,
        "sha256": "b7104718570884a8d2ca059d01a672bb669011a92f40176951153a737e5188fe"
      },
      "1h": {
        "bytes": 294576,
        "format": "parquet",
        "path": "data/research/v9_7/datasets/refined_volnorm_labels/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2024-03-24/splits.parquet",
        "rows": 8784,
        "sha256": "ac06ecb20eebbe7831e2871272162f18a6b45546ae93f56a759a9458bc1de188"
      },
      "1m": {
        "bytes": 14330530,
        "format": "parquet",
        "path": "data/research/v9_7/datasets/refined_volnorm_labels/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2024-03-24/splits.parquet",
        "rows": 527040,
        "sha256": "4a1be7d4f0d12a498af8b08d72e283d1bc4f23f0e71d7ce342a04aa54572b42a"
      },
      "5m": {
        "bytes": 3553960,
        "format": "parquet",
        "path": "data/research/v9_7/datasets/refined_volnorm_labels/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2024-03-24/splits.parquet",
        "rows": 105408,
        "sha256": "e4c35afa0eeaaed6e8b86e29bc22a01648614d28b208e306799f86b5f6d29d08"
      }
    },
    "status": "PASS",
    "target_name": "up_down_flat_volnorm_h1",
    "version": "V9.7",
    "window": {
      "total_days": 366,
      "window_end": "2024-03-24",
      "window_start": "2023-03-25"
    }
  }
}

```

## PASS - `PYTHONPATH=src python -m pytest -q tests/ml/test_refined_volnorm_labels_offline_ml_v9_8.py`
- Returncode : `0`.
- Duree secondes : `1.17`.
- Timestamp UTC : `2026-05-27T12:24:46Z`.

```text
....                                                                     [100%]
4 passed in 0.97s

```

## PASS - `PYTHONPATH=src python -m pytest -q tests/validation/test_refined_volnorm_labels_offline_ml_v9_8_validator.py`
- Returncode : `0`.
- Duree secondes : `1.211`.
- Timestamp UTC : `2026-05-27T12:24:47Z`.

```text
...                                                                      [100%]
3 passed in 0.99s

```

## PASS - `python scripts/run_refined_volnorm_labels_offline_ml_v9_8.py`
- Returncode : `0`.
- Duree secondes : `51.762`.
- Timestamp UTC : `2026-05-27T12:24:48Z`.

```text
{
  "version": "V9.8",
  "status": "PASS",
  "decision": "offline_ml_completed_but_close_to_shuffled_labels",
  "outputs": {
    "1m": {
      "path": "data/research/v9_8/ml/refined_volnorm_labels/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2024-03-24/ml-scores.parquet",
      "sha256": "f2a6693e761815ee15ba819ab9512f6a34cf71a072ecca72c5a3192294bf33e4",
      "bytes": 77331548,
      "rows": 2107920,
      "format": "parquet"
    },
    "5m": {
      "path": "data/research/v9_8/ml/refined_volnorm_labels/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2024-03-24/ml-scores.parquet",
      "sha256": "a9d1ba7d19711bdb51aaed41c6144a32d5d46b31bd5b0500baededc3947b5197",
      "bytes": 10045046,
      "rows": 421392,
      "format": "parquet"
    },
    "15m": {
      "path": "data/research/v9_8/ml/refined_volnorm_labels/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2024-03-24/ml-scores.parquet",
      "sha256": "8afe65755f86bbdf0dccae2d4fd1b8cd516884478fdad043b102aaf5f12636ac",
      "bytes": 3296002,
      "rows": 140304,
      "format": "parquet"
    },
    "1h": {
      "path": "data/research/v9_8/ml/refined_volnorm_labels/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2024-03-24/ml-scores.parquet",
      "sha256": "1abdaacc135cbd5847a11344572ce48816ce345bf3a33fc4ce8b2e7263fce8bc",
      "bytes": 808961,
      "rows": 34896,
      "format": "parquet"
    }
  }
}

```

## PASS - `python scripts/validate_refined_volnorm_labels_offline_ml_v9_8.py`
- Returncode : `0`.
- Duree secondes : `2.97`.
- Timestamp UTC : `2026-05-27T12:25:40Z`.

```text
rame": "5m",
        "walk_forward_group": "wf_2023_08"
      },
      "5m.random_seeded_baseline.wf_2023_09": {
        "accuracy": 0.35185185185185186,
        "balanced_accuracy": 0.3336785492575511,
        "class_distribution_pred": {
          "DOWN": 2385,
          "FLAT": 3875,
          "UP": 2380
        },
        "class_distribution_true": {
          "DOWN": 2359,
          "FLAT": 3842,
          "UP": 2439
        },
        "macro_f1": 0.3336504496265149,
        "model_name": "random_seeded_baseline",
        "rows": 8640,
        "timeframe": "5m",
        "walk_forward_group": "wf_2023_09"
      },
      "5m.random_seeded_baseline.wf_2023_10": {
        "accuracy": 0.3548387096774194,
        "balanced_accuracy": 0.3338302572102772,
        "class_distribution_pred": {
          "DOWN": 2392,
          "FLAT": 4036,
          "UP": 2500
        },
        "class_distribution_true": {
          "DOWN": 2354,
          "FLAT": 4015,
          "UP": 2559
        },
        "macro_f1": 0.3338522841854042,
        "model_name": "random_seeded_baseline",
        "rows": 8928,
        "timeframe": "5m",
        "walk_forward_group": "wf_2023_10"
      },
      "5m.random_seeded_baseline.wf_2023_11": {
        "accuracy": 0.34780092592592593,
        "balanced_accuracy": 0.3333170172656755,
        "class_distribution_pred": {
          "DOWN": 2355,
          "FLAT": 3937,
          "UP": 2348
        },
        "class_distribution_true": {
          "DOWN": 2488,
          "FLAT": 3577,
          "UP": 2575
        },
        "macro_f1": 0.3328011233912447,
        "model_name": "random_seeded_baseline",
        "rows": 8640,
        "timeframe": "5m",
        "walk_forward_group": "wf_2023_11"
      },
      "5m.random_seeded_baseline.wf_2023_12": {
        "accuracy": 0.34800627240143367,
        "balanced_accuracy": 0.333349834112318,
        "class_distribution_pred": {
          "DOWN": 2384,
          "FLAT": 4069,
          "UP": 2475
        },
        "class_distribution_true": {
          "DOWN": 2562,
          "FLAT": 3691,
          "UP": 2675
        },
        "macro_f1": 0.332766397224816,
        "model_name": "random_seeded_baseline",
        "rows": 8928,
        "timeframe": "5m",
        "walk_forward_group": "wf_2023_12"
      },
      "5m.random_seeded_baseline.wf_2024_01": {
        "accuracy": 0.3361335125448029,
        "balanced_accuracy": 0.32277302744517294,
        "class_distribution_pred": {
          "DOWN": 2477,
          "FLAT": 4044,
          "UP": 2407
        },
        "class_distribution_true": {
          "DOWN": 2588,
          "FLAT": 3676,
          "UP": 2664
        },
        "macro_f1": 0.3221931210685311,
        "model_name": "random_seeded_baseline",
        "rows": 8928,
        "timeframe": "5m",
        "walk_forward_group": "wf_2024_01"
      },
      "5m.random_seeded_baseline.wf_2024_02": {
        "accuracy": 0.3496168582375479,
        "balanced_accuracy": 0.33658833508947067,
        "class_distribution_pred": {
          "DOWN": 2288,
          "FLAT": 3736,
          "UP": 2328
        },
        "class_distribution_true": {
          "DOWN": 2361,
          "FLAT": 3446,
          "UP": 2545
        },
        "macro_f1": 0.336230035969351,
        "model_name": "random_seeded_baseline",
        "rows": 8352,
        "timeframe": "5m",
        "walk_forward_group": "wf_2024_02"
      },
      "5m.random_seeded_baseline.wf_2024_03": {
        "accuracy": 0.33969907407407407,
        "balanced_accuracy": 0.32863096575188083,
        "class_distribution_pred": {
          "DOWN": 1842,
          "FLAT": 3077,
          "UP": 1993
        },
        "class_distribution_true": {
          "DOWN": 2031,
          "FLAT": 2793,
          "UP": 2088
        },
        "macro_f1": 0.3282576738599389,
        "model_name": "random_seeded_baseline",
        "rows": 6912,
        "timeframe": "5m",
        "walk_forward_group": "wf_2024_03"
      }
    }
  }
}

```

## PASS - `PYTHONPATH=src python -m pytest -q tests/ml/test_refined_volnorm_strict_walk_forward_v9_9.py`
- Returncode : `0`.
- Duree secondes : `1.188`.
- Timestamp UTC : `2026-05-27T12:25:43Z`.

```text
...                                                                      [100%]
3 passed in 0.96s

```

## PASS - `PYTHONPATH=src python -m pytest -q tests/validation/test_refined_volnorm_strict_walk_forward_v9_9_validator.py`
- Returncode : `0`.
- Duree secondes : `1.199`.
- Timestamp UTC : `2026-05-27T12:25:44Z`.

```text
...                                                                      [100%]
3 passed in 0.98s

```

## PASS - `python scripts/run_refined_volnorm_strict_walk_forward_v9_9.py`
- Returncode : `0`.
- Duree secondes : `199.177`.
- Timestamp UTC : `2026-05-27T12:25:46Z`.

```text
{
  "version": "V9.9",
  "status": "PASS",
  "decision": "strict_walk_forward_completed_but_close_to_shuffled_labels",
  "outputs": {
    "scores": {
      "1m": {
        "path": "data/research/v9_9/ml/refined_volnorm_strict_walk_forward/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2024-03-24/walk_forward_scores.parquet",
        "sha256": "2737c5a52684cd9a91ae03fca33c728be14621948688174845ea854bce9f711c",
        "bytes": 322610134,
        "rows": 8805440,
        "format": "parquet"
      },
      "5m": {
        "path": "data/research/v9_9/ml/refined_volnorm_strict_walk_forward/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2024-03-24/walk_forward_scores.parquet",
        "sha256": "4a4751a9b6c04a9472a7e9464b1fc655a98712bae33fb4aef1fdaf69e4623c94",
        "bytes": 34636950,
        "rows": 1759808,
        "format": "parquet"
      },
      "15m": {
        "path": "data/research/v9_9/ml/refined_volnorm_strict_walk_forward/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2024-03-24/walk_forward_scores.parquet",
        "sha256": "f649f8eda22986e3f7ad57c1b44f22be51853347c74c376da4afe7a406567bfb",
        "bytes": 10484855,
        "rows": 585536,
        "format": "parquet"
      },
      "1h": {
        "path": "data/research/v9_9/ml/refined_volnorm_strict_walk_forward/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2024-03-24/walk_forward_scores.parquet",
        "sha256": "15e2ac177f3cdee81c4bd8cd6835b7f46996700f8a252b1b9f8dc2f1e28ee37d",
        "bytes": 2131074,
        "rows": 145184,
        "format": "parquet"
      }
    },
    "folds": {
      "1m": {
        "path": "data/research/v9_9/ml/refined_volnorm_strict_walk_forward/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2024-03-24/folds.parquet",
        "sha256": "673482f4c7ab3a26f0d3a214265303afadf5ca509b9c1de1109dfadb56ad6f40",
        "bytes": 16273146,
        "rows": 2201760,
        "format": "parquet"
      },
      "5m": {
        "path": "data/research/v9_9/ml/refined_volnorm_strict_walk_forward/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2024-03-24/folds.parquet",
        "sha256": "ba71d90c82a71338cfe865dae676865749c4b205a204c3f200fd69fdf13699f1",
        "bytes": 1692139,
        "rows": 440352,
        "format": "parquet"
      },
      "15m": {
        "path": "data/research/v9_9/ml/refined_volnorm_strict_walk_forward/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2024-03-24/folds.parquet",
        "sha256": "f0453c9d89d6b3f32febd3d4044ebee4bff00c0595d7dda2622f0c1441f44783",
        "bytes": 563801,
        "rows": 146784,
        "format": "parquet"
      },
      "1h": {
        "path": "data/research/v9_9/ml/refined_volnorm_strict_walk_forward/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2024-03-24/folds.parquet",
        "sha256": "6431a66b9849ac18a16685323a1fd28e8e8ce94434699c3b7e8377c030f29c13",
        "bytes": 135834,
        "rows": 36696,
        "format": "parquet"
      }
    }
  }
}

```

## PASS - `python scripts/validate_refined_volnorm_strict_walk_forward_v9_9.py`
- Returncode : `0`.
- Duree secondes : `7.386`.
- Timestamp UTC : `2026-05-27T12:29:05Z`.

```text
es.parquet",
          "rows": 8805440,
          "sha256": "2737c5a52684cd9a91ae03fca33c728be14621948688174845ea854bce9f711c"
        },
        "5m": {
          "bytes": 34636950,
          "format": "parquet",
          "path": "data/research/v9_9/ml/refined_volnorm_strict_walk_forward/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2024-03-24/walk_forward_scores.parquet",
          "rows": 1759808,
          "sha256": "4a4751a9b6c04a9472a7e9464b1fc655a98712bae33fb4aef1fdaf69e4623c94"
        }
      }
    },
    "quality": {
      "15m": {
        "errors": [],
        "fold_role_counts": {
          "test": 14592,
          "train": 117504,
          "validation": 14688
        },
        "fold_temporal_order_valid": true,
        "folds_count": 5,
        "forbidden_feature_columns_present": [],
        "forbidden_output_columns_present": [],
        "no_shuffle_confirmed": true,
        "rows_embargoed": 50,
        "rows_excluded_invalid_label": 60,
        "rows_excluded_warmup": 60,
        "rows_purged": 50,
        "rows_total": 35136,
        "rows_used_for_ml": 146384,
        "timeframe": "15m",
        "warnings": []
      },
      "1h": {
        "errors": [],
        "fold_role_counts": {
          "test": 3648,
          "train": 29376,
          "validation": 3672
        },
        "fold_temporal_order_valid": true,
        "folds_count": 5,
        "forbidden_feature_columns_present": [],
        "forbidden_output_columns_present": [],
        "no_shuffle_confirmed": true,
        "rows_embargoed": 50,
        "rows_excluded_invalid_label": 60,
        "rows_excluded_warmup": 60,
        "rows_purged": 50,
        "rows_total": 8784,
        "rows_used_for_ml": 36296,
        "timeframe": "1h",
        "warnings": []
      },
      "1m": {
        "errors": [],
        "fold_role_counts": {
          "test": 218880,
          "train": 1762560,
          "validation": 220320
        },
        "fold_temporal_order_valid": true,
        "folds_count": 5,
        "forbidden_feature_columns_present": [],
        "forbidden_output_columns_present": [],
        "no_shuffle_confirmed": true,
        "rows_embargoed": 50,
        "rows_excluded_invalid_label": 60,
        "rows_excluded_warmup": 60,
        "rows_purged": 50,
        "rows_total": 527040,
        "rows_used_for_ml": 2201360,
        "timeframe": "1m",
        "warnings": []
      },
      "5m": {
        "errors": [],
        "fold_role_counts": {
          "test": 43776,
          "train": 352512,
          "validation": 44064
        },
        "fold_temporal_order_valid": true,
        "folds_count": 5,
        "forbidden_feature_columns_present": [],
        "forbidden_output_columns_present": [],
        "no_shuffle_confirmed": true,
        "rows_embargoed": 50,
        "rows_excluded_invalid_label": 60,
        "rows_excluded_warmup": 60,
        "rows_purged": 50,
        "rows_total": 105408,
        "rows_used_for_ml": 439952,
        "timeframe": "5m",
        "warnings": []
      }
    },
    "safety": {
      "api_key_used": false,
      "authentication_used": false,
      "backtest_enabled": false,
      "dataset_enabled": true,
      "execution_enabled": false,
      "labels_enabled": true,
      "ml_enabled": true,
      "orders_enabled": false,
      "paper_live_enabled": false,
      "persistent_model_created": false,
      "private_endpoint_used": false,
      "public_read_only": true,
      "strategy_enabled": false,
      "trading_enabled": false
    },
    "status": "PASS",
    "target_name": "up_down_flat_volnorm_h1",
    "version": "V9.9",
    "walk_forward_policy": {
      "embargo_bars": 5,
      "expanding_train": true,
      "grouping": "calendar_month",
      "initial_train_months": 6,
      "purge_bars": 5,
      "shuffle": false,
      "step_months": 1,
      "test_months": 1,
      "validation_months": 1
    },
    "walk_forward_run_id": "v9_9_20260527T122546Z_22caa318"
  }
}

```

## PASS - `PYTHONPATH=src python -m pytest -q tests/research/test_refined_volnorm_research_decision_gate_v9_10.py`
- Returncode : `0`.
- Duree secondes : `0.461`.
- Timestamp UTC : `2026-05-27T12:29:12Z`.

```text
..                                                                       [100%]
2 passed in 0.26s

```

## PASS - `PYTHONPATH=src python -m pytest -q tests/validation/test_refined_volnorm_research_decision_gate_v9_10_validator.py`
- Returncode : `0`.
- Duree secondes : `0.434`.
- Timestamp UTC : `2026-05-27T12:29:13Z`.

```text
...                                                                      [100%]
3 passed in 0.26s

```

## PASS - `python scripts/run_refined_volnorm_research_decision_gate_v9_10.py`
- Returncode : `0`.
- Duree secondes : `0.301`.
- Timestamp UTC : `2026-05-27T12:29:13Z`.

```text
{
  "version": "V9.10",
  "status": "PASS",
  "research_decision": "backtest_not_justified_refine_labels_again"
}

```

## PASS - `python scripts/validate_refined_volnorm_research_decision_gate_v9_10.py`
- Returncode : `0`.
- Duree secondes : `0.292`.
- Timestamp UTC : `2026-05-27T12:29:13Z`.

```text
ion_v9_4": {
        "path": "reports/research_decisions/refined_research_decision_gate_v9_4.json",
        "sha256": "22f9cc78c248fddd5e52f0f7f3363ca576c01869b52d880e1ab2de0cbf926506"
      },
      "labels_v9_6": {
        "path": "reports/labels/refined_volatility_normalized_labels_v9_6.json",
        "sha256": "7f70df1c78e5aff9388f6f3cb03205d8c70324100ed821c153293bc185d27b11"
      },
      "ml_v9_8": {
        "path": "reports/ml/refined_volnorm_labels_offline_ml_v9_8.json",
        "sha256": "2e2f666993ac80f34e8f706fdb9e0d41149da7d405b3da619f5916a5838bbc07"
      },
      "scores_v9_8": {
        "path": "reports/ml/refined_volnorm_labels_offline_scores_v9_8.json",
        "sha256": "847de49724105ba1b1d13270a3a812965348b39a86e495748789c69ecb1b12b2"
      },
      "walk_forward_scores_v9_9": {
        "path": "reports/ml/refined_volnorm_strict_walk_forward_scores_v9_9.json",
        "sha256": "17068093fd8b3a0dc67005a491ce38d422c7254e454af543256baed6d9c72fa0"
      },
      "walk_forward_v9_9": {
        "path": "reports/ml/refined_volnorm_strict_walk_forward_v9_9.json",
        "sha256": "625fb9ca91c8e1d0098f57dd664b0dd44cabc8b2d6537e3d370b8c2452ad278d"
      }
    },
    "label_quality_assessment": {
      "class_majority_over_70_timeframes": [],
      "decision": "label_factory_candidate_created_volatility_normalized",
      "flat_rate_1m": 0.4680234544005465,
      "label_quality_passed": true,
      "selected_multiplier": 0.5
    },
    "leakage_assessment": {
      "labels": {
        "causal_volatility_uses_only_past_and_current_closed_returns": true,
        "forbidden_features_present": [],
        "future_return_used_only_for_label": true,
        "label_available_ts_after_decision_ts_required": true,
        "label_columns_must_not_be_used_as_features": true,
        "passed": true
      },
      "ml": {
        "forbidden_feature_columns_present": [],
        "passed": true
      },
      "passed": true,
      "walk_forward": {
        "forbidden_feature_columns_present": [],
        "passed": true
      }
    },
    "limitations": [
      "V9.10 est un decision gate de recherche uniquement.",
      "V9.10 ne lance aucun backtest, ne produit aucune strategie, aucun signal actionnable et aucun ordre.",
      "Toute suite eventuelle doit etre une version separee et auditee."
    ],
    "metric_forbidden_scan": {
      "ml": {
        "forbidden_terms_present": [],
        "passed": true
      },
      "passed": true,
      "walk_forward": {
        "forbidden_terms_present": [],
        "passed": true
      }
    },
    "next_step_recommendation": "Revoir le design des labels ou les seuils avant toute idee de backtest.",
    "research_decision": "backtest_not_justified_refine_labels_again",
    "safety": {
      "api_key_used": false,
      "authentication_used": false,
      "backtest_enabled": false,
      "dataset_enabled": false,
      "execution_enabled": false,
      "labels_enabled": false,
      "ml_enabled": false,
      "orders_enabled": false,
      "paper_live_enabled": false,
      "persistent_model_created": false,
      "private_endpoint_used": false,
      "public_read_only": true,
      "strategy_enabled": false,
      "trading_enabled": false
    },
    "static_split_assessment_v9_8": {
      "best_learned_validation_test_macro_f1": 0.32134886880825075,
      "decision": "offline_ml_completed_but_close_to_shuffled_labels",
      "learned_models_clearly_useful": false,
      "no_clear_edge_vs_shuffled_labels_count": 14
    },
    "status": "PASS",
    "version": "V9.10",
    "walk_forward_assessment_v9_9": {
      "decision": "strict_walk_forward_completed_but_close_to_shuffled_labels",
      "no_clear_edge_vs_shuffled_labels_count": 76,
      "unstable_folds_count": 20,
      "walk_forward_clean_enough_for_backtest_candidate": false,
      "warnings_count": 0,
      "weak_folds_count": 22
    },
    "warnings": [
      "Des cas walk-forward restent trop proches des labels melanges."
    ]
  }
}

```

## PASS - `python scripts/release_audit_lite_zip_v9_6_to_v9_10.py`
- Returncode : `0`.
- Duree secondes : `4.217`.
- Timestamp UTC : `2026-05-27T12:31:23Z`.

```text
{
  "version_scope": "V9.6_to_V9.10",
  "zip_name": "projet-galapagos-v9.6-to-v9.10-audit-lite.zip",
  "zip_bytes": 2085833,
  "included_files": 1312,
  "samples_included": 20,
  "sidecars_created": false,
  "zip_fingerprints_created": false,
  "status": "PASS"
}

```

## PASS - `python scripts/audit_audit_lite_zip_v9_6_to_v9_10.py --zip projet-galapagos-v9.6-to-v9.10-audit-lite.zip`
- Returncode : `0`.
- Duree secondes : `0.632`.
- Timestamp UTC : `2026-05-27T12:31:27Z`.

```text
{
  "version_scope": "V9.6_to_V9.10",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.6-to-v9.10-audit-lite.zip",
  "passed": true,
  "errors": []
}

```

## PASS - `python scripts/smoke_audit_lite_zip_v9_6_to_v9_10.py --zip projet-galapagos-v9.6-to-v9.10-audit-lite.zip`
- Returncode : `0`.
- Duree secondes : `8.602`.
- Timestamp UTC : `2026-05-27T12:31:28Z`.

```text
{
  "version_scope": "V9.6_to_V9.10",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.6-to-v9.10-audit-lite.zip",
  "passed": true,
  "errors": [],
  "tests_inspectable_included": true,
  "full_tests_executed_in_smoke": false,
  "full_tests_note": "Les tests full V9.6-V9.10 sont inclus pour inspection; le smoke audit-lite sample-only execute collect-only et les controles de samples.",
  "sample_only_checks_executed": true,
  "sidecars_expected": false,
  "zip_fingerprints_expected": false
}

```
