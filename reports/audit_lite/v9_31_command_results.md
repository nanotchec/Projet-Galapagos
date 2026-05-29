# Commandes V9.31

- Statut : `PASS`.
- Aucun sidecar et aucune empreinte ZIP.

- `python scripts/run_aggtrades_5y_extension_collection_v9_31.py` -> `0` (17797.112 s).
  - Note : Commande de collecte executee avant capture formelle; resultat reconstruit depuis le rapport global V9.31 sans relancer la collecte pour ne pas reecrire les metriques.
- `PYTHONPATH=src python -m pytest --collect-only -q` -> `0` (3.437 s).
- `PYTHONPATH=src python -m pytest -q tests/data/test_aggtrades_5y_extension_collection_v9_31.py` -> `0` (0.177 s).
- `PYTHONPATH=src python -m pytest -q tests/validation/test_aggtrades_5y_extension_collection_v9_31_validator.py` -> `0` (0.167 s).
- `PYTHONPATH=src python -m pytest -q tests/data/test_aggtrades_5y_extension_collection_v9_31.py tests/validation/test_aggtrades_5y_extension_collection_v9_31_validator.py` -> `0` (0.15 s).
- `python scripts/validate_aggtrades_5y_extension_collection_v9_31.py` -> `0` (0.298 s).
- `python scripts/release_audit_lite_zip_v9_31.py` -> `0` (0.25 s).
- `python scripts/audit_audit_lite_zip_v9_31.py --zip projet-galapagos-v9.31-audit-lite.zip` -> `0` (0.2 s).
- `python scripts/smoke_audit_lite_zip_v9_31.py --zip projet-galapagos-v9.31-audit-lite.zip` -> `0` (1.45 s).
