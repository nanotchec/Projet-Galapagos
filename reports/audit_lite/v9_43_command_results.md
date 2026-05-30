# Commandes V9.43

- `git branch --show-current` -> `0`; main
- `git status --short --branch` -> `0`; initial clean before V9.43 edits: ## main...origin/main [ahead 12]
- `PYTHONPATH=src python -m pytest --collect-only -q` -> `0`; 5740 tests collected in 2.02s
- `PYTHONPATH=src python -m pytest -q tests/ml/test_ohlcv_aggtrades_5y_offline_ml_v9_43.py` -> `0`; 3 passed in 1.09s
- `PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_aggtrades_5y_offline_ml_v9_43_validator.py` -> `0`; 3 passed in 1.00s
- `python scripts/run_ohlcv_aggtrades_5y_offline_ml_v9_43.py` -> `0`; decision=offline_ml_5y_completed_but_close_to_shuffled_labels; quality_status=PASS; runtime_seconds=321.024704
- `python scripts/validate_ohlcv_aggtrades_5y_offline_ml_v9_43.py` -> `0`; passed=true; errors=[]
- `python scripts/release_audit_lite_zip_v9_43.py` -> `0`; status=PASS; included_files=46; zip=projet-galapagos-v9.43-audit-lite.zip
- `python scripts/audit_audit_lite_zip_v9_43.py --zip projet-galapagos-v9.43-audit-lite.zip` -> `0`; passed=true; errors=[]
- `python scripts/smoke_audit_lite_zip_v9_43.py --zip projet-galapagos-v9.43-audit-lite.zip` -> `0`; passed=true; errors=[]; full_dataset_required=false

- Aucun sidecar et aucune empreinte ZIP.
