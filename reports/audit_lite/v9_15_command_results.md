# Commandes V9.15

- `PYTHONPATH=src python -m pytest --collect-only -q` : `PASS` (1.835s, rc=0).
- `PYTHONPATH=src python -m pytest -q tests/research/test_derivatives_data_extension_readiness_v9_15.py` : `PASS` (0.165s, rc=0).
- `PYTHONPATH=src python -m pytest -q tests/validation/test_derivatives_data_extension_readiness_v9_15_validator.py` : `PASS` (0.152s, rc=0).
- `python scripts/run_derivatives_data_extension_readiness_v9_15.py` : `PASS` (0.03s, rc=0).
- `python scripts/validate_derivatives_data_extension_readiness_v9_15.py` : `PASS` (0.211s, rc=0).
- `python scripts/release_audit_lite_zip_v9_15.py` : `PASS` (0.044s, rc=0).
- `python scripts/audit_audit_lite_zip_v9_15.py --zip projet-galapagos-v9.15-audit-lite.zip` : `PASS` (0.038s, rc=0).
- `python scripts/smoke_audit_lite_zip_v9_15.py --zip projet-galapagos-v9.15-audit-lite.zip` : `PASS` (0.419s, rc=0).
