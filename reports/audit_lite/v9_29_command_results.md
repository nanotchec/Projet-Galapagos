# Commandes V9.29

- `PYTHONPATH=src python -m pytest --collect-only -q` -> `PASS` (5593 tests collected in 2.53s)
- `PYTHONPATH=src python -m pytest -q tests/data/test_aggtrades_post_v9_full_coverage_validation_v9_29.py` -> `PASS` (6 passed in 0.03s)
- `PYTHONPATH=src python -m pytest -q tests/validation/test_aggtrades_post_v9_full_coverage_validation_v9_29_validator.py` -> `PASS` (5 passed in 0.03s)
- `python scripts/run_aggtrades_post_v9_full_coverage_validation_v9_29.py` -> `PASS` (decision=aggtrades_full_coverage_validated_with_non_blocking_warnings; days_complete=731; days_missing=0; days_failed=0; global_duplicate_count=0; global_invalid_rows=0; network_used=false; runtime_seconds=761.688)
- `python scripts/validate_aggtrades_post_v9_full_coverage_validation_v9_29.py` -> `PASS` (V9.29 validator PASS; errors=[])
- `python scripts/release_audit_lite_zip_v9_29.py` -> `PASS` (ZIP projet-galapagos-v9.29-audit-lite.zip created; included_files=58; latest zip_bytes_estimate=190758)
- `python scripts/audit_audit_lite_zip_v9_29.py --zip projet-galapagos-v9.29-audit-lite.zip` -> `PASS` (zip audit passed; errors=[])
- `python scripts/smoke_audit_lite_zip_v9_29.py --zip projet-galapagos-v9.29-audit-lite.zip` -> `PASS` (zip smoke passed; errors=[]; import/pytest/audit timeouts enforced)

- Aucun sidecar et aucune empreinte ZIP.
