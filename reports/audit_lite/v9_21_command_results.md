# Commandes V9.21

Statut: PASS

## 1. `PYTHONPATH=src python -m pytest --collect-only -q`

- Statut: PASS
- Code retour: 0
- Duree: 2.383 s
- Debut UTC: 2026-05-27T21:18:41Z
- Fin UTC: 2026-05-27T21:18:43Z

```text
tests/audit_lite/test_grouped_audit_lite_v9_0_to_v9_3_1.py::test_grouped_audit_lite_v9_0_to_v9_3_1_samples_are_self_contained
tests/audit_lite/test_grouped_audit_lite_v9_0_to_v9_3_1.py::test_grouped_audit_lite_v9_0_to_v9_3_1_sample_schemas_are_strict
tests/audit_lite/test_grouped_audit_lite_v9_0_to_v9_3_1.py::test_grouped_audit_lite_v9_0_to_v9_3_1_samples_exclude_forbidden_outputs
tests/audit_lite/test_grouped_audit_lite_v9_0_to_v9_3_1.py::test_grouped_audit_lite_v9_0_to_v9_3_1_claims_remain_false
tests/audit_lite/test_grouped_audit_lite_v9_0_to_v9_3_2.py::test_grouped_audit_lite_v9_0_to_v9_3_2_reports_are_scoped
tests/audit_lite/test_grouped_audit_lite_v9_0_to_v9_3_2.py::test_grouped_audit_lite_v9_0_to_v9_3_2_samples_are_self_contained
tests/audit_lite/test_grouped_audit_lite_v9_0_to_v9_3_2.py::test_grouped_audit_lite_v9_0_to_v9_3_2_sample_schemas_are_strict
tests/audit_lite/test_grouped_audit_lite_v9_0_to_v9_3_2.py::test_grouped_audit_lite_v9_0_to_v9_3_2_samples_exclude_forbidden_outputs
tests/audit_lite/test_grouped_audit_lite_v9_0_to_v9_3_2.py::test_grouped_audit_lite_v9_0_to_v9_3_2_claims_and_safety_remain_false
tests/audit_lite/test_grouped_audit_lite_v9_0_to_v9_3_2.py::test_grouped_audit_lite_v9_0_to_v9_3_2_inventory_excludes_forbidden_paths
tests/data/test_aggtrades_post_v9_batch_collection_v9_20.py::test_batch_window_is_limited_to_thirty_days_v9_20
tests/data/test_aggtrades_post_v9_batch_collection_v9_20.py::test_collect_mode_requires_explicit_download_limit_v9_20
tests/data/test_aggtrades_post_v9_batch_collection_v9_20.py::test_source_design_is_public_archive_without_auth_v9_20
tests/data/test_aggtrades_post_v9_batch_collection_v9_20.py::test_day_plan_detects_raw_and_silver_batch_outputs_v9_20
tests/data/test_aggtrades_post_v9_batch_collection_v9_20.py::test_validate_batch_day_accepts_small_valid_normalized_sample_v9_20
tests/data/test_aggtrades_post_v9_batch_collection_v9_20.py::test_validate_batch_day_rejects_duplicate_aggregate_trade_id_v9_20
tests/data/test_aggtrades_post_v9_batch_collection_v9_20.py::test_decision_success_requires_complete_quality_batch_v9_20
tests/data/test_aggtrades_post_v9_batch_collection_v9_20.py::test_safety_flags_for_collect_are_public_archive_only_v9_20
tests/data/test_aggtrades_post_v9_batch_collection_v9_20.py::test_collect_batch_refuses_unbounded_execution_v9_20
tests/data/test_aggtrades_post_v9_batch_collection_v9_20.py::test_collect_batch_skips_existing_complete_day_v9_20
tests/data/test_aggtrades_post_v9_batch_collection_v9_20.py::test_batch_summary_never_claims_full_future_coverage_v9_20
tests/data/test_aggtrades_post_v9_batch_expansion_v9_21.py::test_batch_window_is_limited_to_sixty_days_v9_21
tests/data/test_aggtrades_post_v9_batch_expansion_v9_21.py::test_collect_mode_requires_explicit_download_limit_v9_21
tests/data/test_aggtrades_post_v9_batch_expansion_v9_21.py::test_source_design_is_public_archive_without_auth_v9_21
tests/data/test_aggtrades_post_v9_batch_expansion_v9_21.py::test_day_plan_detects_raw_and_silver_batch_outputs_v9_21
tests/data/test_aggtrades_post_v9_batch_expansion_v9_21.py::test_validate_batch_day_accepts_small_valid_normalized_sample_v9_21
tests/data/test_aggtrades_post_v9_batch_expansion_v9_21.py::test_validate_batch_day_rejects_duplicate_aggregate_trade_id_v9_21
tests/data/test_aggtrades_post_v9_batch_expansion_v9_21.py::test_decision_success_requires_complete_quality_batch_v9_21
tests/data/test_aggtrades_post_v9_batch_expansion_v9_21.py::test_safety_flags_for_collect_are_public_archive_only_v9_21
tests/data/test_aggtrades_post_v9_batch_expansion_v9_21.py::test_collect_batch_refuses_unbounded_execution_v9_21
tests/data/test_aggtrades_post_v9_batch_expansion_v9_21.py::test_collect_batch_skips_existing_complete_day_v9_21
tests/data/test_aggtrades_post_v9_batch_expansion_v9_21.py::test_batch_summary_never_claims_full_future_coverage_v9_21
tests/data/test_aggtrades_post_v9_collection_v9_18.py::test_target_window_has_expected_day_count_v9_18
tests/data/test_ag
```

## 2. `PYTHONPATH=src python -m pytest -q tests/data/test_aggtrades_post_v9_batch_expansion_v9_21.py`

- Statut: PASS
- Code retour: 0
- Duree: 0.508 s
- Debut UTC: 2026-05-27T21:18:43Z
- Fin UTC: 2026-05-27T21:18:44Z

```text
...........                                                              [100%]
11 passed in 0.33s
```

## 3. `PYTHONPATH=src python -m pytest -q tests/validation/test_aggtrades_post_v9_batch_expansion_v9_21_validator.py`

- Statut: PASS
- Code retour: 0
- Duree: 0.17 s
- Debut UTC: 2026-05-27T21:18:44Z
- Fin UTC: 2026-05-27T21:18:44Z

```text
.........                                                                [100%]
9 passed in 0.03s
```

## 4. `python scripts/run_aggtrades_post_v9_batch_expansion_v9_21.py --mode collect --start-date 2024-06-11 --end-date 2024-08-09 --max-downloads 60`

- Statut: PASS
- Code retour: 0
- Duree: 711.123 s
- Debut UTC: 2026-05-27T21:18:44Z
- Fin UTC: 2026-05-27T21:30:35Z

```text
{
  "version": "V9.21",
  "status": "PASS",
  "mode": "collect",
  "decision": "aggtrades_post_v9_batch_expansion_success",
  "batch_start": "2024-06-11",
  "batch_end": "2024-08-09",
  "max_downloads": 60,
  "days_requested": 60,
  "days_attempted": 60,
  "days_downloaded": 60,
  "days_normalized": 60,
  "days_skipped_existing": 0,
  "days_complete": 60,
  "days_failed": 0,
  "total_rows": 79146750,
  "raw_bytes_total": 995768974,
  "silver_bytes_total": 1962969758,
  "runtime_seconds": 710.887,
  "cumulative_known_coverage_start": "2024-05-05",
  "cumulative_known_coverage_end": "2024-08-09",
  "network_used": true,
  "api_key_used": false,
  "private_endpoint_used": false,
  "exchange_auth_used": false,
  "websocket_live_used": false,
  "complete_collection_reached": false
}
```

## 5. `python scripts/validate_aggtrades_post_v9_batch_expansion_v9_21.py`

- Statut: PASS
- Code retour: 0
- Duree: 0.954 s
- Debut UTC: 2026-05-27T21:30:35Z
- Fin UTC: 2026-05-27T21:30:36Z

```text
{
  "version": "V9.21",
  "passed": true,
  "errors": []
}
```

## 6. `python scripts/release_audit_lite_zip_v9_21.py`

- Statut: PASS
- Code retour: 0
- Duree: 0.211 s
- Debut UTC: 2026-05-27T21:30:36Z
- Fin UTC: 2026-05-27T21:30:36Z

```text
{
  "version": "V9.21",
  "zip_name": "projet-galapagos-v9.21-audit-lite.zip",
  "zip_bytes_estimate": 255849,
  "zip_bytes_is_authoritative": false,
  "included_files": 51,
  "sidecars_created": false,
  "zip_fingerprints_created": false,
  "status": "PASS"
}
```

## 7. `python scripts/release_audit_lite_zip_v9_21.py`

- Statut: PASS
- Code retour: 0
- Duree: 0.222 s
- Debut UTC: 2026-05-27T21:30:36Z
- Fin UTC: 2026-05-27T21:30:37Z

```text
{
  "version": "V9.21",
  "zip_name": "projet-galapagos-v9.21-audit-lite.zip",
  "zip_bytes_estimate": 256094,
  "zip_bytes_is_authoritative": false,
  "included_files": 51,
  "sidecars_created": false,
  "zip_fingerprints_created": false,
  "status": "PASS"
}
```

## 8. `python scripts/audit_audit_lite_zip_v9_21.py --zip projet-galapagos-v9.21-audit-lite.zip`

- Statut: PASS
- Code retour: 0
- Duree: 0.082 s
- Debut UTC: 2026-05-27T21:30:37Z
- Fin UTC: 2026-05-27T21:30:37Z

```text
{
  "version": "V9.21",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.21-audit-lite.zip",
  "passed": true,
  "errors": []
}
```

## 9. `python scripts/smoke_audit_lite_zip_v9_21.py --zip projet-galapagos-v9.21-audit-lite.zip`

- Statut: PASS
- Code retour: 0
- Duree: 1.495 s
- Debut UTC: 2026-05-27T21:30:37Z
- Fin UTC: 2026-05-27T21:30:38Z

```text
{
  "version": "V9.21",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.21-audit-lite.zip",
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

## 10. `python scripts/release_audit_lite_zip_v9_21.py`

- Statut: PASS
- Code retour: 0
- Duree: 0.201 s
- Debut UTC: 2026-05-27T21:30:38Z
- Fin UTC: 2026-05-27T21:30:38Z

```text
{
  "version": "V9.21",
  "zip_name": "projet-galapagos-v9.21-audit-lite.zip",
  "zip_bytes_estimate": 256579,
  "zip_bytes_is_authoritative": false,
  "included_files": 51,
  "sidecars_created": false,
  "zip_fingerprints_created": false,
  "status": "PASS"
}
```

## 11. `python scripts/audit_audit_lite_zip_v9_21.py --zip projet-galapagos-v9.21-audit-lite.zip`

- Statut: PASS
- Code retour: 0
- Duree: 0.079 s
- Debut UTC: 2026-05-27T21:30:38Z
- Fin UTC: 2026-05-27T21:30:38Z

```text
{
  "version": "V9.21",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.21-audit-lite.zip",
  "passed": true,
  "errors": []
}
```

## 12. `python scripts/smoke_audit_lite_zip_v9_21.py --zip projet-galapagos-v9.21-audit-lite.zip`

- Statut: PASS
- Code retour: 0
- Duree: 1.337 s
- Debut UTC: 2026-05-27T21:30:39Z
- Fin UTC: 2026-05-27T21:30:40Z

```text
{
  "version": "V9.21",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.21-audit-lite.zip",
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

