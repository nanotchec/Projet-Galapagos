# Commandes V9.35

- `git branch --show-current` -> returncode `0` ; main
- `git status --short --branch` -> returncode `0` ; ## main...origin/main [ahead 4]
- `PYTHONPATH=src python -m pytest --collect-only -q` -> returncode `0` ; 5668 tests collected in 2.20s
- `PYTHONPATH=src python -m pytest -q tests/data/test_ohlcv_from_aggtrades_5y_v9_35.py` -> returncode `0` ; 5 passed in 0.60s
- `PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_from_aggtrades_5y_v9_35_validator.py` -> returncode `0` ; 6 passed in 0.28s
- `python scripts/run_ohlcv_from_aggtrades_5y_v9_35.py` -> returncode `0` ; PASS, decision=ohlcv_from_aggtrades_5y_derivation_complete_with_warnings, row_counts 1m=2630880 5m=526176 15m=175392 1h=43848
- `python scripts/validate_ohlcv_from_aggtrades_5y_v9_35.py` -> returncode `0` ; PASS, errors=[], quality_status=PASS
- `python scripts/release_audit_lite_zip_v9_35.py` -> returncode `0` ; PASS, included_files=47
- `python scripts/audit_audit_lite_zip_v9_35.py --zip projet-galapagos-v9.35-audit-lite.zip` -> returncode `0` ; PASS, errors=[]
- `python scripts/smoke_audit_lite_zip_v9_35.py --zip projet-galapagos-v9.35-audit-lite.zip` -> returncode `0` ; PASS, errors=[]

- Aucun sidecar et aucune empreinte ZIP.
