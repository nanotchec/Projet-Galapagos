# Commandes V9.38

- `PYTHONPATH=src python -m pytest --collect-only -q` -> `0` ; 5703 tests collected in 2.29s
- `PYTHONPATH=src python -m pytest -q tests/features/test_ohlcv_aggtrades_5y_feature_store_validation_v9_38.py` -> `0` ; 6 passed in 0.33s
- `PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_aggtrades_5y_feature_store_validation_v9_38_validator.py` -> `0` ; 6 passed in 0.29s
- `python scripts/run_ohlcv_aggtrades_5y_feature_store_validation_v9_38.py` -> `0` ; PASS; decision=ohlcv_aggtrades_5y_feature_store_validated_with_non_blocking_warnings; runtime_seconds=6.93
- `python scripts/validate_ohlcv_aggtrades_5y_feature_store_validation_v9_38.py` -> `0` ; PASS; errors=[]
- `python scripts/release_audit_lite_zip_v9_38.py` -> `0` ; PASS; included_files=44
- `python scripts/audit_audit_lite_zip_v9_38.py --zip projet-galapagos-v9.38-audit-lite.zip` -> `0` ; PASS; errors=[]
- `python scripts/smoke_audit_lite_zip_v9_38.py --zip projet-galapagos-v9.38-audit-lite.zip` -> `0` ; PASS; errors=[]; parquet_engine_available=true

- Aucun sidecar et aucune empreinte ZIP.
