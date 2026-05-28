# Commandes V9.28

- `PYTHONPATH=src python -m pytest --collect-only -q` -> `PASS` (5582 tests collected in 2.33s).
- `PYTHONPATH=src python -m pytest -q tests/data/test_aggtrades_post_v9_bad_day_repair_v9_28.py` -> `PASS` (6 passed in 0.31s).
- `PYTHONPATH=src python -m pytest -q tests/validation/test_aggtrades_post_v9_bad_day_repair_v9_28_validator.py` -> `PASS` (5 passed in 0.03s).
- `python scripts/run_aggtrades_post_v9_bad_day_repair_v9_28.py` -> `PASS` (bad_day_repaired_and_remaining_window_completed; repair_applied=true; coverage 2024-05-05 -> 2026-05-05).
- `python scripts/validate_aggtrades_post_v9_bad_day_repair_v9_28.py` -> `PASS` (passed=true; errors=[]).
- `python scripts/release_audit_lite_zip_v9_28.py` -> `PASS` (created projet-galapagos-v9.28-audit-lite.zip; included_files=58; no sidecars; no ZIP fingerprints).
- `python scripts/audit_audit_lite_zip_v9_28.py --zip projet-galapagos-v9.28-audit-lite.zip` -> `PASS` (passed=true; errors=[]).
- `python scripts/smoke_audit_lite_zip_v9_28.py --zip projet-galapagos-v9.28-audit-lite.zip` -> `PASS` (passed=true; errors=[]; import/pytest/audit timeouts enforced).

- Aucun sidecar et aucune empreinte ZIP.
