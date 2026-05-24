# Attestation full locale V6.0

- Scope : `full_local`
- Validation full locale remplacee par audit-lite : `false`
- Aucun trading, aucun backtest, aucun ordre.

## Commandes executees

- `python scripts/run_advanced_ohlcv_feature_store_v6_0.py` : PASS
- `python scripts/validate_advanced_ohlcv_feature_store_v6_0.py` : PASS
- `python -m pytest -q tests/features/test_advanced_ohlcv_features_v6_0.py` : PASS
- `python -m pytest -q tests/validation/test_advanced_ohlcv_feature_store_v6_0_validator.py` : PASS
- `python scripts/release_audit_lite_zip_v6_0.py` : PASS
- `python scripts/audit_audit_lite_zip_v6_0.py --zip projet-galapagos-v6.0-audit-lite.zip` : PASS
- `python scripts/smoke_audit_lite_zip_v6_0.py --zip projet-galapagos-v6.0-audit-lite.zip` : PASS
- `python -m pytest --collect-only -q` : PASS

## Outputs features complets

- 15m: `110976` lignes, checksum `448944dcef0f3b5979ba3fae23a68027ebf1db06de0ee8a25665556504d95262`
- 1h: `27744` lignes, checksum `3e169626dbaf155751e1a42629d4b32de9dcfcd98d36edbc42332f879329f6df`
- 1m: `1664640` lignes, checksum `8fd91f7aba3f66546dcdeaaec8d69a93401f697fd77b573cefab6e976078d14a`
- 5m: `332928` lignes, checksum `b2a6e7f7c636d3715a914c7c00531b6ac1b0e2649fac6b119c2d3504518e73a9`
