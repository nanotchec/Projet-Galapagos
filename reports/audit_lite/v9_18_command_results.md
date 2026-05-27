# Resultats des commandes V9.18

## PYTHONPATH=src python -m pytest --collect-only -q
- Statut : `PASS`.
- Returncode : `0`.
- Duree : `2.828` secondes.
- Timestamp UTC : `2026-05-27T18:54:39Z`.

## PYTHONPATH=src python -m pytest -q tests/data/test_aggtrades_post_v9_collection_v9_18.py
- Statut : `PASS`.
- Returncode : `0`.
- Duree : `0.187` secondes.
- Timestamp UTC : `2026-05-27T18:54:42Z`.

## PYTHONPATH=src python -m pytest -q tests/validation/test_aggtrades_post_v9_collection_v9_18_validator.py
- Statut : `PASS`.
- Returncode : `0`.
- Duree : `0.185` secondes.
- Timestamp UTC : `2026-05-27T18:54:42Z`.

## python scripts/run_aggtrades_post_v9_collection_v9_18.py --mode dry-run
- Statut : `PASS`.
- Returncode : `0`.
- Duree : `0.072` secondes.
- Timestamp UTC : `2026-05-27T18:54:42Z`.

## python scripts/validate_aggtrades_post_v9_collection_v9_18.py
- Statut : `PASS`.
- Returncode : `0`.
- Duree : `0.459` secondes.
- Timestamp UTC : `2026-05-27T18:54:43Z`.

## python scripts/release_audit_lite_zip_v9_18.py
- Statut : `PASS`.
- Returncode : `0`.
- Duree : `0.533` secondes.
- Timestamp UTC : `2026-05-27T18:54:43Z`.

## python scripts/audit_audit_lite_zip_v9_18.py --zip projet-galapagos-v9.18-audit-lite.zip
- Statut : `PASS`.
- Returncode : `0`.
- Duree : `0.05` secondes.
- Timestamp UTC : `2026-05-27T18:54:44Z`.

## python scripts/smoke_audit_lite_zip_v9_18.py --zip projet-galapagos-v9.18-audit-lite.zip
- Statut : `PASS`.
- Returncode : `0`.
- Duree : `0.547` secondes.
- Timestamp UTC : `2026-05-27T18:54:44Z`.

Mode execute : `dry-run`. Aucune collecte, aucun reseau, aucun telechargement, aucune ingestion, aucun sidecar et aucune empreinte ZIP n'ont ete crees par V9.18.
