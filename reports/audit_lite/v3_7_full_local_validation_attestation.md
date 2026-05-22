# Attestation validation full locale V3.7

Cette attestation compacte resume une validation full locale executee sur le projet complet. Le ZIP audit-lite reste un artefact transmissible et ne remplace pas la validation full locale.

## Commandes executees

- `python scripts/run_expanded_label_factory_v3_7.py` : rc `0`, duree `4.542` s
- `python scripts/validate_expanded_label_factory_v3_7.py` : rc `0`, duree `4.039` s
- `python -m pytest -q tests/labels/test_expanded_forward_labels_v3_7.py` : rc `0`, duree `0.638` s
- `python -m pytest -q tests/validation/test_expanded_label_factory_v3_7_validator.py` : rc `0`, duree `18.867` s
- `python scripts/release_audit_lite_zip_v3_7.py` : rc `0`, duree `0.74` s
- `python scripts/audit_audit_lite_zip_v3_7.py --zip projet-galapagos-v3.7-audit-lite.zip` : rc `0`, duree `0.371` s
- `python scripts/smoke_audit_lite_zip_v3_7.py --zip projet-galapagos-v3.7-audit-lite.zip` : rc `0`, duree `0.394` s
- `python -m pytest --collect-only -q` : rc `0`, duree `2.203` s

## Fichiers labels complets V3.7

- `15m` : `8640` lignes, `1339681` octets, sha256 `bd378f40cd0cf43286c9470c966b8ce1d828930e667643f51a09c719050d4ece`, `2024-01-01T00:00:00Z` -> `2024-03-30T23:45:00Z`
- `1h` : `2160` lignes, `343079` octets, sha256 `e953e79d32f4f1197bdc3d78d28519c8cd54283fa823451f27e437f2db07acf1`, `2024-01-01T00:00:00Z` -> `2024-03-30T23:00:00Z`
- `1m` : `129600` lignes, `19903565` octets, sha256 `7a10dd6c3042db580d706044a8064535c69edd71d3635363547725184d569a42`, `2024-01-01T00:00:00Z` -> `2024-03-30T23:59:00Z`
- `5m` : `25920` lignes, `3962525` octets, sha256 `c25b7e8efd4c26ed9fe284b08d680f71f214df6db72f2d88d9da4c97989b470c`, `2024-01-01T00:00:00Z` -> `2024-03-30T23:55:00Z`

## Checksums rapports

- Manifest : `2d6bcd9e77bb4c89c7a12f575d2759f4db27585691450c21cf7c69a526cbbc58`
- Rapport : `2d6bcd9e77bb4c89c7a12f575d2759f4db27585691450c21cf7c69a526cbbc58`
- ZIP audit-lite initial : `a480edb08403af6d2dfaf11e7f67777c0a574c525e72a8a55932eaff19e1426b`

## Resultats

- Tests passes : `True`
- Validateur full passe : `True`
- Audit audit-lite passe : `True`
- Smoke audit-lite passe : `True`

## Securite

- Aucun trading cree.
- Aucun backtest cree.
- Aucune strategie creee.
- Aucun ordre cree.
- Les validateurs full ne sont pas relaches.
