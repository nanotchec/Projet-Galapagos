# Attestation full locale V5.3

- Scope : `full_local`
- Validation full locale remplacee par audit-lite : `false`
- Aucun trading, aucun ML, aucun backtest, aucun ordre.

## Commandes executees

- `python scripts/run_max_history_offline_supervised_dataset_v5_3.py` : PASS
- `python scripts/validate_max_history_offline_supervised_dataset_v5_3.py` : PASS
- `python -m pytest -q tests/datasets/test_max_history_offline_supervised_dataset_v5_3.py` : PASS
- `python -m pytest -q tests/validation/test_max_history_offline_supervised_dataset_v5_3_validator.py` : PASS
- `python scripts/release_audit_lite_zip_v5_3.py` : PASS
- `python scripts/audit_audit_lite_zip_v5_3.py --zip projet-galapagos-v5.3-audit-lite.zip` : PASS
- `python scripts/smoke_audit_lite_zip_v5_3.py --zip projet-galapagos-v5.3-audit-lite.zip` : PASS
- `python -m pytest --collect-only -q` : PASS

## Outputs datasets complets

- 15m: `110976` lignes, checksum `5bd202626b814ee82542f707d1c820d3e5e26e9ed73cd2ccc3eba9dff408b7fa`
- 1h: `27744` lignes, checksum `bfea4d768bcfaeefe8d0b5eb3fa9b3265667be5e06e389b192ee8fece19c1a86`
- 1m: `1664640` lignes, checksum `0e1d7acf60a8d5893c68659e2d008a5debdbdbf9017d56236ff3babbc14fb39a`
- 5m: `332928` lignes, checksum `f63ca0bc69f066577a706a0dc4edbd01c26f1c011e98979af6d9c1836d1187c5`
