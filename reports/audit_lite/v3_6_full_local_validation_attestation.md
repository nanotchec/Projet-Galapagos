# Attestation validation full locale V3.6

Cette attestation compacte resume une validation full locale executee sur le projet complet. Le ZIP audit-lite reste un artefact transmissible et ne remplace pas la validation full locale.

## Commandes executees

- `python scripts/run_expanded_causal_feature_store_v3_6.py` : rc `0`, duree `2.82` s
- `python scripts/validate_expanded_causal_feature_store_v3_6.py` : rc `0`, duree `0.889` s
- `python -m pytest -q tests/features/test_expanded_causal_features_v3_6.py` : rc `0`, duree `0.654` s
- `python -m pytest -q tests/validation/test_expanded_causal_feature_store_v3_6_validator.py` : rc `0`, duree `2.166` s
- `python scripts/release_audit_lite_zip_v3_6.py` : rc `0`, duree `0.676` s
- `python scripts/audit_audit_lite_zip_v3_6.py --zip projet-galapagos-v3.6-audit-lite.zip` : rc `0`, duree `0.401` s
- `python scripts/smoke_audit_lite_zip_v3_6.py --zip projet-galapagos-v3.6-audit-lite.zip` : rc `0`, duree `0.434` s
- `python -m pytest --collect-only -q` : rc `0`, duree `2.14` s

## Fichiers features complets V3.6

- `15m` : `8640` lignes, `2401445` octets, sha256 `686a88848abc11697585380cc30cb75a7d919d2e4233d92b7f143e411996a8ca`, `2024-01-01T00:00:00Z` -> `2024-03-30T23:45:00Z`
- `1h` : `2160` lignes, `615274` octets, sha256 `935054e4ab575c15b9b7105af5c36edb974b191204d2b4b14f1994e5b3ea987e`, `2024-01-01T00:00:00Z` -> `2024-03-30T23:00:00Z`
- `1m` : `129600` lignes, `34478157` octets, sha256 `b67f5b563d0d7a1300aa956af2ecae9616f7c5d74550c0ed75ad332809167136`, `2024-01-01T00:00:00Z` -> `2024-03-30T23:59:00Z`
- `5m` : `25920` lignes, `7049909` octets, sha256 `89479d3014e538f502ab11fa3c888d116af986e678d389f2f0ed3b18d430fac7`, `2024-01-01T00:00:00Z` -> `2024-03-30T23:55:00Z`

## Checksums rapports

- Manifest : `94cdde40762d61be59f84f25683cb5d09e6ab438fdb8fc553e9a5fa2c563be92`
- Rapport : `94cdde40762d61be59f84f25683cb5d09e6ab438fdb8fc553e9a5fa2c563be92`
- ZIP audit-lite : `79f303f7ad7cbe91a15aec8c2b5bffd631763d71c6f8071828e01b8107b24245`

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
