# Commandes V9.30

- `PYTHONPATH=src python -m pytest --collect-only -q` -> `PASS` (5604 tests collected in 2.49s)
- `PYTHONPATH=src python -m pytest -q tests/data/test_aggtrades_5y_extension_plan_v9_30.py` -> `PASS` (6 passed in 0.08s)
- `PYTHONPATH=src python -m pytest -q tests/validation/test_aggtrades_5y_extension_plan_v9_30_validator.py` -> `PASS` (5 passed in 0.03s)
- `python scripts/run_aggtrades_5y_extension_plan_v9_30.py` -> `PASS` (decision=aggtrades_5y_extension_plan_ready; extension_days_needed=1096; network_used=false; ingestion_executed=false)
- `python scripts/validate_aggtrades_5y_extension_plan_v9_30.py` -> `PASS` (V9.30 validator PASS; errors=[])
- `python scripts/release_audit_lite_zip_v9_30.py` -> `PASS` (ZIP projet-galapagos-v9.30-audit-lite.zip created; included_files=61; latest zip_bytes_estimate=195632)
- `python scripts/audit_audit_lite_zip_v9_30.py --zip projet-galapagos-v9.30-audit-lite.zip` -> `PASS` (zip audit passed; errors=[])
- `python scripts/smoke_audit_lite_zip_v9_30.py --zip projet-galapagos-v9.30-audit-lite.zip` -> `PASS` (zip smoke passed; errors=[]; import/pytest/audit timeouts enforced)

- Aucun sidecar et aucune empreinte ZIP.
