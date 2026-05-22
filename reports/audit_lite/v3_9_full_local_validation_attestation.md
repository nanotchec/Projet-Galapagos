# Attestation full locale V3.9

- Version : `V3.9`
- Scope : `full_local`
- Validation full locale : `true`
- Audit-lite ne remplace pas la validation full locale : `true`
- Aucun trading, aucun backtest, aucun ordre, aucun modele persistant.

## Commandes executees

- `python scripts/run_expanded_offline_ml_research_v3_9.py` : code `0`, `16.77` s
- `python scripts/validate_expanded_offline_ml_research_v3_9.py` : code `0`, `10.3` s
- `python -m pytest -q tests/ml/test_expanded_offline_ml_research_v3_9.py` : code `0`, `1.51` s
- `python -m pytest -q tests/validation/test_expanded_offline_ml_research_v3_9_validator.py` : code `0`, `11.07` s
- `python scripts/release_audit_lite_zip_v3_9.py` : code `0`, `1.09` s
- `python scripts/audit_audit_lite_zip_v3_9.py --zip projet-galapagos-v3.9-audit-lite.zip` : code `0`, `0.4` s
- `python scripts/smoke_audit_lite_zip_v3_9.py --zip projet-galapagos-v3.9-audit-lite.zip` : code `0`, `1.17` s
- `python -m pytest --collect-only -q` : code `0`, `1.98` s

## Outputs scores full

- `1m` : `data/research/v3_9/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-01_2024-03-30/ml-scores.parquet` sha256 `5e85abab4c5a9fd4eac63ecbb894df62fd297e81bc74e500486373512a91464a`, `518276` lignes, `12178699` octets
- `5m` : `data/research/v3_9/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-01_2024-03-30/ml-scores.parquet` sha256 `114862fd5e691d703b541eb2e763650f79481e09e356661a8910ac5ecb89e51a`, `103556` lignes, `2346348` octets
- `15m` : `data/research/v3_9/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-01_2024-03-30/ml-scores.parquet` sha256 `aeb19f7b14c0c58c966f6f358aca5858a8c7d2d0a8e484a5991d2e7c632021a6`, `34436` lignes, `790585` octets
- `1h` : `data/research/v3_9/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-01_2024-03-30/ml-scores.parquet` sha256 `1840b25ed16e218214e3a8264b4c1218e36815787f8beefd0af4ca830c9c00cb`, `8516` lignes, `181762` octets
