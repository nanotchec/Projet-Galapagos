# Commandes V9.42

- `git branch --show-current` -> `main` (returncode `0`).
- `git status --short --branch` -> `## main...origin/main [ahead 11]` (returncode `0`).
- `PYTHONPATH=src python -m pytest --collect-only -q` -> `5734 tests collected in 2.49s` (returncode `0`).
- `PYTHONPATH=src python -m pytest -q tests/datasets/test_ohlcv_aggtrades_5y_dataset_validation_v9_42.py` -> `4 passed in 0.37s` (returncode `0`).
- `PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_aggtrades_5y_dataset_validation_v9_42_validator.py` -> `3 passed in 0.38s` (returncode `0`).
- `python scripts/run_ohlcv_aggtrades_5y_dataset_validation_v9_42.py` -> `PASS; mode=full-local; decision=ohlcv_aggtrades_5y_dataset_validated; coverage/schema/quality/leakage=PASS; warnings=[]; runtime_seconds=30.571` (returncode `0`).
- `python scripts/validate_ohlcv_aggtrades_5y_dataset_validation_v9_42.py` -> `PASS; errors=[]; validation_mode=full-local` (returncode `0`).
- `python scripts/release_audit_lite_zip_v9_42.py` -> `PASS; included_files=47; no sidecars; no zip fingerprints` (returncode `0`).
- `python scripts/audit_audit_lite_zip_v9_42.py --zip projet-galapagos-v9.42-audit-lite.zip` -> `PASS; errors=[]` (returncode `0`).
- `python scripts/smoke_audit_lite_zip_v9_42.py --zip projet-galapagos-v9.42-audit-lite.zip` -> `PASS; errors=[]; packaging_checks_passed=true; parquet_checks_required=true` (returncode `0`).
- Aucun sidecar et aucune empreinte ZIP.
