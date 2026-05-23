# Attestation full locale V4.5

- Scope : `full_local`
- Validation full locale remplacee par audit-lite : `false`
- Aucun trading, aucun backtest, aucun ordre.

## Commandes executees

- `python scripts/run_one_year_offline_supervised_dataset_v4_5.py` : PASS, 19.64s
- `python scripts/validate_one_year_offline_supervised_dataset_v4_5.py` : PASS, 6.93s
- `python -m pytest -q tests/datasets/test_one_year_offline_supervised_dataset_v4_5.py` : PASS, 1.1s
- `python -m pytest -q tests/validation/test_one_year_offline_supervised_dataset_v4_5_validator.py` : PASS, 14.75s
- `python scripts/release_audit_lite_zip_v4_5.py` : PASS, 1.73s
- `python scripts/audit_audit_lite_zip_v4_5.py --zip projet-galapagos-v4.5-audit-lite.zip` : PASS, 0.37s
- `python scripts/smoke_audit_lite_zip_v4_5.py --zip projet-galapagos-v4.5-audit-lite.zip` : PASS, 0.71s
- `python -m pytest --collect-only -q` : PASS, 2.65s

## Outputs datasets complets

- `15m` : `35136` lignes, checksum `6d8aecfcfd8d47a550cc7b2ab7075e8eb7086682072842226c9a690ee8c790fc`
- `1h` : `8784` lignes, checksum `35593d36097855dcc567a2789b16f34bb0e6aa920f547eec5376a2ed2d32ebce`
- `1m` : `527040` lignes, checksum `79c0b4eee6c7b24b49a2c8d219e98660859595ef96d5a6786fd4354f5869aae5`
- `5m` : `105408` lignes, checksum `f8ab01c296deab838e140893d387458ddc4b371dcd787573792fef9a8a04735a`
