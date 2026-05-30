# Commandes V9.37

- `git branch --show-current` -> `0`
- `git status --short --branch` -> `0`
- `PYTHONPATH=src python -m pytest --collect-only -q` -> `0`
- `PYTHONPATH=src python -m pytest -q tests/features/test_ohlcv_aggtrades_5y_feature_store_v9_37.py` -> `0`
- `PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_aggtrades_5y_feature_store_v9_37_validator.py` -> `0`
- `python scripts/run_ohlcv_aggtrades_5y_feature_store_v9_37.py` -> `0`
- `python scripts/validate_ohlcv_aggtrades_5y_feature_store_v9_37.py` -> `0`
- `python scripts/release_audit_lite_zip_v9_37.py` -> `0`
- `python scripts/audit_audit_lite_zip_v9_37.py --zip projet-galapagos-v9.37-audit-lite.zip` -> `0`
- `python scripts/smoke_audit_lite_zip_v9_37.py --zip projet-galapagos-v9.37-audit-lite.zip` -> `0`

- Aucun sidecar et aucune empreinte ZIP.
