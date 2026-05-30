# Commandes V9.41

- `git branch --show-current` -> `main` (returncode `0`).
- `git status --short --branch` -> `## main...origin/main [ahead 10]` (returncode `0`).
- `PYTHONPATH=src python -m pytest --collect-only -q` -> `5727 tests collected in 2.91s` (returncode `0`).
- `PYTHONPATH=src python -m pytest -q tests/datasets/test_ohlcv_aggtrades_5y_dataset_v9_41.py` -> `3 passed in 0.42s` (returncode `0`).
- `PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_aggtrades_5y_dataset_v9_41_validator.py` -> `3 passed in 0.42s` (returncode `0`).
- `python scripts/run_ohlcv_aggtrades_5y_dataset_v9_41.py` -> `dataset_created=true; decision=ohlcv_aggtrades_5y_dataset_created; leakage_guard=PASS; quality_status=PASS; runtime_seconds=21.838` (returncode `0`).
- `python scripts/validate_ohlcv_aggtrades_5y_dataset_v9_41.py` -> `PASS; errors=[]; dataset_created=true` (returncode `0`).
- `python scripts/release_audit_lite_zip_v9_41.py` -> `PASS; included_files=46; no sidecars; no zip fingerprints` (returncode `0`).
- `python scripts/audit_audit_lite_zip_v9_41.py --zip projet-galapagos-v9.41-audit-lite.zip` -> `PASS; errors=[]` (returncode `0`).
- `python scripts/smoke_audit_lite_zip_v9_41.py --zip projet-galapagos-v9.41-audit-lite.zip` -> `PASS; errors=[]; packaging_checks_passed=true; parquet_checks_required=true` (returncode `0`).
- Aucun sidecar et aucune empreinte ZIP.
