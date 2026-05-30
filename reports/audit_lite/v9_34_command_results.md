# Commandes V9.34

- `PYTHONPATH=src python -m pytest --collect-only -q` -> `0` : 5649 tests collected in 2.25s
- `PYTHONPATH=src python -m pytest -q tests/data/test_ohlcv_5y_extension_v9_34.py` -> `0` : 5 passed in 0.31s
- `PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_5y_extension_v9_34_validator.py` -> `0` : 5 passed in 0.26s
- `python scripts/run_ohlcv_5y_extension_v9_34.py` -> `1` : decision=ohlcv_5y_extension_failed_quality; failed_day=2021-08-13; timeframe=1m; rows=1170 expected=1440; gap_count=1; days_normalized=39; days_skipped_existing=61
- `python scripts/validate_ohlcv_5y_extension_v9_34.py` -> `0` : PASS; decision=ohlcv_5y_extension_failed_quality; errors=[]
- `python scripts/release_audit_lite_zip_v9_34.py` -> `0` : PASS; included_files=47; zip_bytes_estimate=146014
- `python scripts/audit_audit_lite_zip_v9_34.py --zip projet-galapagos-v9.34-audit-lite.zip` -> `1` : Initial audit failed because command_results did not yet include release command; fixed and rerun.
- `PYTHONPATH=src python -m pytest -q tests/data/test_ohlcv_5y_extension_v9_34.py tests/validation/test_ohlcv_5y_extension_v9_34_validator.py` -> `0` : 10 passed in 0.32s after audit-lite dependency fix
- `python scripts/smoke_audit_lite_zip_v9_34.py --zip projet-galapagos-v9.34-audit-lite.zip` -> `1` : Initial smoke failed because audit-lite ZIP missed imported OHLCV helper dependencies; fixed and rerun.
- `python scripts/release_audit_lite_zip_v9_34.py` -> `0` : PASS; included_files=50; zip_bytes_estimate=151126 after dependency fix
- `python scripts/audit_audit_lite_zip_v9_34.py --zip projet-galapagos-v9.34-audit-lite.zip` -> `0` : PASS; errors=[]
- `python scripts/smoke_audit_lite_zip_v9_34.py --zip projet-galapagos-v9.34-audit-lite.zip` -> `0` : PASS; errors=[]

Aucun sidecar et aucune empreinte ZIP.
