# Commandes V9.33

- `PYTHONPATH=src python -m pytest --collect-only -q` -> `0` : 5639 tests collected in 2.18s
- `PYTHONPATH=src python -m pytest -q tests/features/test_ohlcv_aggtrades_5y_feature_store_v9_33.py` -> `0` : 4 passed in 0.29s
- `PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_aggtrades_5y_feature_store_v9_33_validator.py` -> `0` : 4 passed in 0.35s
- `python scripts/run_ohlcv_aggtrades_5y_feature_store_v9_33.py` -> `0` : decision=ohlcv_5y_extension_required_before_feature_store; ohlcv_5y_ready=false; aggtrades_5y_ready=true; feature_store_created=false; quality_status=NOT_CREATED
- `python scripts/validate_ohlcv_aggtrades_5y_feature_store_v9_33.py` -> `0` : PASS; errors=[]
- `python scripts/release_audit_lite_zip_v9_33.py` -> `0` : PASS; included_files=41; zip_bytes_estimate=70740
- `python scripts/audit_audit_lite_zip_v9_33.py --zip projet-galapagos-v9.33-audit-lite.zip` -> `0` : PASS; errors=[]
- `python scripts/smoke_audit_lite_zip_v9_33.py --zip projet-galapagos-v9.33-audit-lite.zip` -> `0` : PASS; errors=[]

Aucun sidecar et aucune empreinte ZIP.
