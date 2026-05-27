# Resultats des commandes V9.19

## PYTHONPATH=src python -m pytest --collect-only -q
- Statut : `PASS`.
- Returncode : `0`.
- Duree secondes : `2.622`.
- Timestamp UTC : `2026-05-27T20:08:07Z`.

## PYTHONPATH=src python -m pytest -q tests/data/test_aggtrades_post_v9_pilot_collection_v9_19.py
- Statut : `PASS`.
- Returncode : `0`.
- Duree secondes : `0.472`.
- Timestamp UTC : `2026-05-27T20:08:10Z`.

## PYTHONPATH=src python -m pytest -q tests/validation/test_aggtrades_post_v9_pilot_collection_v9_19_validator.py
- Statut : `PASS`.
- Returncode : `0`.
- Duree secondes : `0.167`.
- Timestamp UTC : `2026-05-27T20:08:10Z`.

## python scripts/run_aggtrades_post_v9_pilot_collection_v9_19.py --mode collect --start-date 2024-05-05 --end-date 2024-05-11 --max-downloads 7
- Statut : `PASS`.
- Returncode : `0`.
- Duree secondes : `69.524`.
- Timestamp UTC : `2026-05-27T20:06:49Z`.

## python scripts/validate_aggtrades_post_v9_pilot_collection_v9_19.py
- Statut : `PASS`.
- Returncode : `0`.
- Duree secondes : `0.248`.
- Timestamp UTC : `2026-05-27T20:08:10Z`.

## python scripts/release_audit_lite_zip_v9_19.py
- Statut : `PASS`.
- Returncode : `0`.
- Duree secondes : `0.549`.
- Timestamp UTC : `2026-05-27T20:08:11Z`.

## python scripts/audit_audit_lite_zip_v9_19.py --zip projet-galapagos-v9.19-audit-lite.zip
- Statut : `PASS`.
- Returncode : `0`.
- Duree secondes : `0.049`.
- Timestamp UTC : `2026-05-27T20:09:04Z`.

## python scripts/smoke_audit_lite_zip_v9_19.py --zip projet-galapagos-v9.19-audit-lite.zip
- Statut : `PASS`.
- Returncode : `0`.
- Duree secondes : `1.264`.
- Timestamp UTC : `2026-05-27T20:09:04Z`.

La collecte reseau est strictement limitee a `data.binance.vision` et au pilot 7 jours. Aucun sidecar ni empreinte ZIP.
