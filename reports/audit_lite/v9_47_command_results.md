# Commandes V9.47

- `git branch --show-current` -> `0` : main
- `git status --short --branch` -> `0` : ## main...origin/main [ahead 3]; V9.47 files in progress
- `PYTHONPATH=src python -m pytest --collect-only -q` -> `0` : 5769 tests collected in 2.23s
- `PYTHONPATH=src python -m pytest -q tests/features/test_ohlcv_aggtrades_exact_5y_feature_store_v9_47.py` -> `0` : 4 passed in 0.29s
- `PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_aggtrades_exact_5y_feature_store_v9_47_validator.py` -> `0` : 3 passed in 0.28s
- `python scripts/run_ohlcv_aggtrades_exact_5y_feature_store_v9_47.py` -> `0` : decision=ohlcv_aggtrades_exact_5y_feature_store_created_with_warnings; quality=PASS; coverage=target_5y_combined_feature_window_complete; rows 1m=2630880 5m=526176 15m=175392 1h=43848; runtime=13.309s
- `python scripts/validate_ohlcv_aggtrades_exact_5y_feature_store_v9_47.py` -> `0` : full-local validation passed; errors=[]
- `python scripts/release_audit_lite_zip_v9_47.py` -> `0` : ZIP created; included_files=49; sidecars_created=false; zip_fingerprints_created=false
- `python scripts/audit_audit_lite_zip_v9_47.py --zip projet-galapagos-v9.47-audit-lite.zip` -> `0` : audit passed; errors=[]
- `python scripts/smoke_audit_lite_zip_v9_47.py --zip projet-galapagos-v9.47-audit-lite.zip` -> `0` : smoke passed; packaging_checks=true; sample_checks=true; full_dataset_required=false

- Aucun sidecar et aucune empreinte ZIP.
