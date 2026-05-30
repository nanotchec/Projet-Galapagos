# Commandes V9.40

- `git branch --show-current` -> rc `0` ; main
- `git status --short --branch` -> rc `0` ; ## main...origin/main [ahead 9]
- `PYTHONPATH=src python -m pytest --collect-only -q` -> rc `0` ; 5721 tests collected in 2.17s
- `PYTHONPATH=src python -m pytest -q tests/labels/test_ohlcv_aggtrades_5y_label_factory_v9_40.py` -> rc `0` ; 3 passed in 0.27s
- `PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_aggtrades_5y_label_factory_v9_40_validator.py` -> rc `0` ; 4 passed in 0.28s
- `python scripts/run_ohlcv_aggtrades_5y_label_factory_v9_40.py` -> rc `0` ; PASS; decision=ohlcv_aggtrades_5y_labels_created_with_warnings; labels_created=true; selected_primary_label=up_down_flat_volnorm_h1_5y; runtime_seconds=56.083
- `python scripts/validate_ohlcv_aggtrades_5y_label_factory_v9_40.py` -> rc `0` ; PASS; errors=[]
- `python scripts/release_audit_lite_zip_v9_40.py` -> rc `0` ; PASS; included_files=44
- `python scripts/audit_audit_lite_zip_v9_40.py --zip projet-galapagos-v9.40-audit-lite.zip` -> rc `0` ; PASS; errors=[]
- `python scripts/smoke_audit_lite_zip_v9_40.py --zip projet-galapagos-v9.40-audit-lite.zip` -> rc `0` ; PASS; errors=[]; packaging_checks_passed=true
- Aucun sidecar et aucune empreinte ZIP.
