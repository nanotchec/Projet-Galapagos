# Commandes V9.34.1

- `PYTHONPATH=src python -m pytest --collect-only -q` -> returncode `0` ; 5657 tests collected in 2.31s
- `PYTHONPATH=src python -m pytest -q tests/data/test_ohlcv_5y_extension_correction_v9_34_1.py` -> returncode `0` ; 3 passed in 0.38s
- `PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_5y_extension_correction_v9_34_1_validator.py` -> returncode `0` ; 5 passed in 0.28s
- `python scripts/run_ohlcv_5y_extension_correction_v9_34_1.py` -> returncode `1` ; controlled source failure: public redownload for 2021-08-13 1m still has 1170 rows and one timestamp gap; no broad collection resumed
- `python scripts/validate_ohlcv_5y_extension_correction_v9_34_1.py` -> returncode `0` ; PASS, errors=[], decision=ohlcv_5y_extension_failed_source_issue
- `python scripts/release_audit_lite_zip_v9_34_1.py` -> returncode `0` ; PASS, included_files=51, zip_bytes_estimate=84890 before final audit report refresh
- `python scripts/audit_audit_lite_zip_v9_34_1.py --zip projet-galapagos-v9.34.1-audit-lite.zip` -> returncode `0` ; PASS, errors=[]
- `python scripts/smoke_audit_lite_zip_v9_34_1.py --zip projet-galapagos-v9.34.1-audit-lite.zip` -> returncode `0` ; PASS, errors=[]

- Le returncode `1` de `run_ohlcv_5y_extension_correction_v9_34_1.py` correspond a un arret fonctionnel controle sur source publique incomplete, valide par le validator.
- Aucun sidecar et aucune empreinte ZIP.
