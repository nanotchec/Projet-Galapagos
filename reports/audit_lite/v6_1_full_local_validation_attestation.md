# Attestation full locale V6.1

- Scope : `full_local`
- Validation full locale remplacee par audit-lite : `false`
- Aucun ML, aucun modele, aucun trading, aucun backtest, aucun ordre.

## Commandes executees

- `python scripts/run_advanced_ohlcv_offline_supervised_dataset_v6_1.py` : PASS
- `python scripts/validate_advanced_ohlcv_offline_supervised_dataset_v6_1.py` : PASS
- `python -m pytest -q tests/datasets/test_advanced_ohlcv_offline_supervised_dataset_v6_1.py` : PASS
- `python -m pytest -q tests/validation/test_advanced_ohlcv_offline_supervised_dataset_v6_1_validator.py` : PASS
- `python scripts/release_audit_lite_zip_v6_1.py` : PASS
- `python scripts/audit_audit_lite_zip_v6_1.py --zip projet-galapagos-v6.1-audit-lite.zip` : PASS
- `python scripts/smoke_audit_lite_zip_v6_1.py --zip projet-galapagos-v6.1-audit-lite.zip` : PASS
- `python -m pytest --collect-only -q` : PASS

## Datasets complets

- 15m: `110976` lignes, checksum `6dc8276c2dd048ed35ef59b70805f6368f2f9e24215b226706ab9b63c4838206`
- 1h: `27744` lignes, checksum `2f9f8160bade7ed02d928de8cd2027362885d29e605b95a1dc626ceb7510c6a4`
- 1m: `1664640` lignes, checksum `c8fe6be68d1190510ca2067b33be704761123f836300693f4cde796e89690c10`
- 5m: `332928` lignes, checksum `acfc22e1d2a178afec58ee4c3be39048d1277aa6fb7df14f02e8e5f09d95089a`

## Splits complets

- 15m: `110976` lignes, checksum `e5cf9d57d7b290f72484f32a6f1465650c44180a617ec831475272b0a3965eb4`
- 1h: `27744` lignes, checksum `52dde880b3c22a437384bd8a926cd14a4a645692ba8cd9254cdd7c190ef6504a`
- 1m: `1664640` lignes, checksum `69242ae552e31418419603df2bee682813be624f2143ed351f6017e64c911061`
- 5m: `332928` lignes, checksum `2a6901333590bc8ab4b62e91636f6979cddc290a6beb341b833cfcc68aa91419`
