# Attestation full locale V5.0

- Scope : `full_local`
- Validation full locale remplacee par audit-lite : `false`
- Aucun trading, aucun backtest, aucun ordre.

## Commandes executees

- `python scripts/discover_max_history_public_market_data_v5_0.py` : PASS
- `python scripts/run_max_history_public_market_data_v5_0.py --no-network --skip-project-state-check` : PASS
- `python scripts/validate_max_history_public_market_data_v5_0.py` : PASS
- `python -m pytest -q tests/data/test_max_history_public_market_data_v5_0.py` : PASS
- `python -m pytest -q tests/validation/test_max_history_public_market_data_v5_0_validator.py` : PASS
- `python scripts/release_audit_lite_zip_v5_0.py` : PASS
- `python scripts/audit_audit_lite_zip_v5_0.py --zip projet-galapagos-v5.0-audit-lite.zip` : PASS
- `python scripts/smoke_audit_lite_zip_v5_0.py --zip projet-galapagos-v5.0-audit-lite.zip` : PASS
- `python -m pytest --collect-only -q` : PASS

## Outputs OHLCV complets

- 15m: `110976` lignes, checksum `24467f2873703b9ed69212d1dfe7722f1ee35bfcb2377267db95b2fa935428c0`
- 1h: `27744` lignes, checksum `20d44dbb8df47f09bed816dba3a5c458971e6ce8ead5f13d8e455053357780b1`
- 1m: `1664640` lignes, checksum `aa833956e85e6d92d1881366924c2ede1a935df26dfa3d35a7ec32c7b84682b2`
- 5m: `332928` lignes, checksum `7eaed34863699dcb73c30fb83722bdc5ac1b15cb6c43b0c2a6027a0826d5e363`
