# Commandes V9.22

Statut: PASS

## 1. `PYTHONPATH=src python -m pytest --collect-only -q`

- Statut: PASS
- Code retour: 0
- Duree: 4.952 s
- Debut UTC: 2026-05-27T21:52:40Z
- Fin UTC: 2026-05-27T21:52:45Z

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

## 2. `PYTHONPATH=src python -m pytest -q tests/data/test_aggtrades_post_v9_multi_batch_plan_v9_22.py`

- Statut: PASS
- Code retour: 0
- Duree: 0.518 s
- Debut UTC: 2026-05-27T21:52:45Z
- Fin UTC: 2026-05-27T21:52:46Z

```text
.....                                                                    [100%]
5 passed in 0.17s
```

## 3. `PYTHONPATH=src python -m pytest -q tests/validation/test_aggtrades_post_v9_multi_batch_plan_v9_22_validator.py`

- Statut: PASS
- Code retour: 0
- Duree: 0.543 s
- Debut UTC: 2026-05-27T21:52:46Z
- Fin UTC: 2026-05-27T21:52:46Z

```text
.......                                                                  [100%]
7 passed in 0.25s
```

## 4. `python scripts/run_aggtrades_post_v9_multi_batch_plan_v9_22.py`

- Statut: PASS
- Code retour: 0
- Duree: 0.116 s
- Debut UTC: 2026-05-27T21:52:46Z
- Fin UTC: 2026-05-27T21:52:46Z

```text
{
  "version": "V9.22",
  "status": "PASS",
  "mode": "plan-only",
  "decision": "multi_batch_completion_plan_ready_with_disk_warning",
  "current_coverage_start": "2024-05-05",
  "current_coverage_end": "2024-08-09",
  "days_covered": 97,
  "days_remaining": 634,
  "gaps_detected": [],
  "proposed_batches_count": 11,
  "estimated_remaining_rows": 742779184,
  "estimated_remaining_raw_bytes": 9507149536,
  "estimated_remaining_silver_bytes": 18689853376,
  "network_used": false,
  "new_data_downloaded": false,
  "ingestion_executed": false,
  "api_key_used": false,
  "private_endpoint_used": false,
  "exchange_auth_used": false,
  "websocket_live_used": false
}
```

## 5. `python scripts/validate_aggtrades_post_v9_multi_batch_plan_v9_22.py`

- Statut: PASS
- Code retour: 0
- Duree: 0.503 s
- Debut UTC: 2026-05-27T21:52:46Z
- Fin UTC: 2026-05-27T21:52:47Z

```text
{
  "version": "V9.22",
  "passed": true,
  "errors": []
}
```

## 6. `python scripts/release_audit_lite_zip_v9_22.py`

- Statut: PASS
- Code retour: 0
- Duree: 0.091 s
- Debut UTC: 2026-05-27T21:52:47Z
- Fin UTC: 2026-05-27T21:52:47Z

```text
{
  "version": "V9.22",
  "zip_name": "projet-galapagos-v9.22-audit-lite.zip",
  "zip_bytes_estimate": 259421,
  "zip_bytes_is_authoritative": false,
  "included_files": 54,
  "sidecars_created": false,
  "zip_fingerprints_created": false,
  "status": "PASS"
}
```

## 7. `python scripts/release_audit_lite_zip_v9_22.py`

- Statut: PASS
- Code retour: 0
- Duree: 0.143 s
- Debut UTC: 2026-05-27T21:52:47Z
- Fin UTC: 2026-05-27T21:52:47Z

```text
{
  "version": "V9.22",
  "zip_name": "projet-galapagos-v9.22-audit-lite.zip",
  "zip_bytes_estimate": 259657,
  "zip_bytes_is_authoritative": false,
  "included_files": 54,
  "sidecars_created": false,
  "zip_fingerprints_created": false,
  "status": "PASS"
}
```

## 8. `python scripts/audit_audit_lite_zip_v9_22.py --zip projet-galapagos-v9.22-audit-lite.zip`

- Statut: PASS
- Code retour: 0
- Duree: 0.121 s
- Debut UTC: 2026-05-27T21:52:47Z
- Fin UTC: 2026-05-27T21:52:47Z

```text
{
  "version": "V9.22",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.22-audit-lite.zip",
  "passed": true,
  "errors": []
}
```

## 9. `python scripts/smoke_audit_lite_zip_v9_22.py --zip projet-galapagos-v9.22-audit-lite.zip`

- Statut: PASS
- Code retour: 0
- Duree: 1.029 s
- Debut UTC: 2026-05-27T21:52:47Z
- Fin UTC: 2026-05-27T21:52:48Z

```text
{
  "version": "V9.22",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.22-audit-lite.zip",
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

## 10. `python scripts/release_audit_lite_zip_v9_22.py`

- Statut: PASS
- Code retour: 0
- Duree: 0.282 s
- Debut UTC: 2026-05-27T21:52:48Z
- Fin UTC: 2026-05-27T21:52:48Z

```text
{
  "version": "V9.22",
  "zip_name": "projet-galapagos-v9.22-audit-lite.zip",
  "zip_bytes_estimate": 260142,
  "zip_bytes_is_authoritative": false,
  "included_files": 54,
  "sidecars_created": false,
  "zip_fingerprints_created": false,
  "status": "PASS"
}
```

## 11. `python scripts/audit_audit_lite_zip_v9_22.py --zip projet-galapagos-v9.22-audit-lite.zip`

- Statut: PASS
- Code retour: 0
- Duree: 0.067 s
- Debut UTC: 2026-05-27T21:52:49Z
- Fin UTC: 2026-05-27T21:52:49Z

```text
{
  "version": "V9.22",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.22-audit-lite.zip",
  "passed": true,
  "errors": []
}
```

## 12. `python scripts/smoke_audit_lite_zip_v9_22.py --zip projet-galapagos-v9.22-audit-lite.zip`

- Statut: PASS
- Code retour: 0
- Duree: 1.045 s
- Debut UTC: 2026-05-27T21:52:49Z
- Fin UTC: 2026-05-27T21:52:50Z

```text
{
  "version": "V9.22",
  "zip": "/Users/lilianserre/Documents/projets/projet-galapagos/projet-galapagos-v9.22-audit-lite.zip",
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

