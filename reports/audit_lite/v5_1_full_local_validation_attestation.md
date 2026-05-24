# Attestation full locale V5.1

- Scope : `full_local`
- Validation full locale remplacee par audit-lite : `false`
- Aucun trading, aucun backtest, aucun ordre.

## Commandes executees

- `python scripts/run_max_history_causal_feature_store_v5_1.py` : PASS
- `python scripts/validate_max_history_causal_feature_store_v5_1.py` : PASS
- `python -m pytest -q tests/features/test_max_history_causal_features_v5_1.py` : PASS
- `python -m pytest -q tests/validation/test_max_history_causal_feature_store_v5_1_validator.py` : PASS
- `python scripts/release_audit_lite_zip_v5_1.py` : PASS
- `python scripts/audit_audit_lite_zip_v5_1.py --zip projet-galapagos-v5.1-audit-lite.zip` : PASS
- `python scripts/smoke_audit_lite_zip_v5_1.py --zip projet-galapagos-v5.1-audit-lite.zip` : PASS
- `python -m pytest --collect-only -q` : PASS

## Outputs features complets

- 15m: `110976` lignes, checksum `d7433a329049b276a8718decd0a66ba091e2387015a2fdf821b9db6d36fb48a0`
- 1h: `27744` lignes, checksum `7fcc0f902d25743a6451132d54f91d6a9bea6e33cf53953c728415bcaaea9660`
- 1m: `1664640` lignes, checksum `3cd1fff75176ea91908f499aa5abf215afe2663fc25c7a0829eab2981ba0f377`
- 5m: `332928` lignes, checksum `70160b3d534de5af7274ee8750bbecfac9c2da1c0d5fda4888f449f913036ac9`
