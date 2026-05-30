# Commandes V9.32

- Statut : `PASS`.
- `python scripts/run_aggtrades_5y_full_coverage_validation_v9_32.py` -> `0` (2886.616 s).
  - Note : Commande executee avant reprise apres interruption; resultat lu depuis le rapport V9.32 produit par le script sans relancer la validation exhaustive.
- `PYTHONPATH=src python -m pytest --collect-only -q` -> `0` (2.866 s).
- `PYTHONPATH=src python -m pytest -q tests/data/test_aggtrades_5y_full_coverage_validation_v9_32.py` -> `0` (0.2 s).
- `PYTHONPATH=src python -m pytest -q tests/validation/test_aggtrades_5y_full_coverage_validation_v9_32_validator.py` -> `0` (0.191 s).
- `python scripts/validate_aggtrades_5y_full_coverage_validation_v9_32.py` -> `0` (0.339 s).
- `python scripts/release_audit_lite_zip_v9_32.py` -> `0` (0.106 s).
- `python scripts/audit_audit_lite_zip_v9_32.py --zip projet-galapagos-v9.32-audit-lite.zip` -> `1` (0.049 s).
- `python scripts/release_audit_lite_zip_v9_32.py` -> `0` (0.135 s).
- `python scripts/audit_audit_lite_zip_v9_32.py --zip projet-galapagos-v9.32-audit-lite.zip` -> `0` (0.056 s).
- `python scripts/smoke_audit_lite_zip_v9_32.py --zip projet-galapagos-v9.32-audit-lite.zip` -> `1` (0.88 s).
- `python scripts/release_audit_lite_zip_v9_32.py` -> `0` (0.168 s).
- `python scripts/audit_audit_lite_zip_v9_32.py --zip projet-galapagos-v9.32-audit-lite.zip` -> `0` (0.047 s).
- `python scripts/smoke_audit_lite_zip_v9_32.py --zip projet-galapagos-v9.32-audit-lite.zip` -> `0` (0.713 s).
- Aucun sidecar et aucune empreinte ZIP.
