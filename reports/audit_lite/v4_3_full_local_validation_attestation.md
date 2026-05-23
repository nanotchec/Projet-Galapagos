# Attestation full locale V4.3

- Scope : `full_local`
- Validation full locale remplacee par audit-lite : `false`
- Aucun trading, aucun backtest, aucun ordre.

## Commandes executees

- `python scripts/run_one_year_causal_feature_store_v4_3.py` : PASS, 7.41s
- `python scripts/validate_one_year_causal_feature_store_v4_3.py` : PASS, 1.5s
- `python -m pytest -q tests/features/test_one_year_causal_features_v4_3.py` : PASS, 1.07s
- `python -m pytest -q tests/validation/test_one_year_causal_feature_store_v4_3_validator.py` : PASS, 5.96s
- `python scripts/release_audit_lite_zip_v4_3.py` : PASS, 1.41s
- `python scripts/audit_audit_lite_zip_v4_3.py --zip projet-galapagos-v4.3-audit-lite.zip` : PASS, 0.47s
- `python scripts/smoke_audit_lite_zip_v4_3.py --zip projet-galapagos-v4.3-audit-lite.zip` : PASS, 0.88s
- `python -m pytest --collect-only -q` : PASS, 3.36s

## Outputs features complets

- `15m` : `35136` lignes, checksum `88b0c26a3ed045e60bc50e30a1e94bd2ee88130aeab4dd0589993ce0e96f7fb5`
- `1h` : `8784` lignes, checksum `197cc03e8bc72dda5c09689472be0f9a456b05d57db794694e0fd2143bab4e14`
- `1m` : `527040` lignes, checksum `7dfd42e24c286efcde36f912a532a58a45f6fb8daf040b00edbe3cd071463bd0`
- `5m` : `105408` lignes, checksum `025ae8a987aee1af89d45fd774097000b84a79b357d625ad509699bbe7d9a7d9`
