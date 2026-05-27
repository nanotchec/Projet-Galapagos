# Commandes V9.12

- `PYTHONPATH=src python -m pytest --collect-only -q` : `PASS` (returncode `0`, duree `1.971` s).
- `PYTHONPATH=src python -m pytest -q tests/labels/test_horizon_event_label_redesign_v9_12.py` : `PASS` (returncode `0`, duree `0.422` s).
- `PYTHONPATH=src python -m pytest -q tests/validation/test_horizon_event_label_redesign_v9_12_validator.py` : `PASS` (returncode `0`, duree `0.411` s).
- `python scripts/run_horizon_event_label_redesign_v9_12.py` : `PASS` (returncode `0`, duree `20.469` s).
- `python scripts/validate_horizon_event_label_redesign_v9_12.py` : `PASS` (returncode `0`, duree `0.553` s).
- `python scripts/release_audit_lite_zip_v9_12.py` : `PASS` (returncode `0`, duree `0.592` s).
- `python scripts/audit_audit_lite_zip_v9_12.py --zip projet-galapagos-v9.12-audit-lite.zip` : `PASS` (returncode `0`, duree `0.059` s).
- `python scripts/smoke_audit_lite_zip_v9_12.py --zip projet-galapagos-v9.12-audit-lite.zip` : `PASS` (returncode `0`, duree `1.745` s).
