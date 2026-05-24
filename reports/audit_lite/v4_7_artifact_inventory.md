# Inventaire audit-lite V4.7

Ce rapport decrit les artefacts lourds exclus du ZIP `audit-lite`.

- Raw zips exclus : `True`
- Parquet complets exclus : `4`
- Validation full locale remplacee : `false`
- Note : `audit-lite does not replace full local validation`

## Parquet scores exclus

- `15m` : `data/research/v4_6/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-01_2024-12-31/ml-scores.parquet` (140420 lignes)
- `1h` : `data/research/v4_6/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-01_2024-12-31/ml-scores.parquet` (35012 lignes)
- `1m` : `data/research/v4_6/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-01_2024-12-31/ml-scores.parquet` (2108036 lignes)
- `5m` : `data/research/v4_6/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-01_2024-12-31/ml-scores.parquet` (421508 lignes)

## Garantie de scope

Les validateurs de production ne sont pas relaches. Le ZIP audit-lite sert a transmettre le code, les rapports, les manifests, les checksums et l'attestation full locale. Il ne pretend pas revalider physiquement les 1 an sans les donnees completes locales.
