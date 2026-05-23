# Attestation full locale V4.2

- Scope : `full_local`
- Validation full locale remplacee par audit-lite : `false`
- Aucun trading, aucun backtest, aucun ordre.

## Commandes executees

- `python scripts/run_one_year_public_market_data_v4_2.py --no-network --skip-project-state-check` : PASS
- `python scripts/validate_one_year_public_market_data_v4_2.py` : PASS
- `python -m pytest -q tests/data/test_one_year_public_market_data_v4_2.py` : PASS
- `python -m pytest -q tests/validation/test_one_year_public_market_data_v4_2_validator.py` : PASS
- `python scripts/release_audit_lite_zip_v4_2.py` : PASS
- `python scripts/audit_audit_lite_zip_v4_2.py --zip projet-galapagos-v4.2-audit-lite.zip` : PASS
- `python scripts/smoke_audit_lite_zip_v4_2.py --zip projet-galapagos-v4.2-audit-lite.zip` : PASS
- `python -m pytest --collect-only -q` : PASS

## Outputs OHLCV complets

- 15m: `35136` lignes, checksum `92d2eaa6d75b08be0f13cc2b3fd5f1b73a36ba394f5fae16fa5906e37907fdef`
- 1h: `8784` lignes, checksum `cc2ed4e04ce9efc499831d55584b948a2dd990443d3be9614de27c3a671fd4e0`
- 1m: `527040` lignes, checksum `9ca673ee5b8f8e496ac76defddbf5f92924087cb9a7d8c11d33753edf052e156`
- 5m: `105408` lignes, checksum `91914c5d6b7e475d36145d1156c5a3d07fa60e7c5de26d3ce432551d1fff3091`
