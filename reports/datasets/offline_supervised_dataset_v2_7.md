# Rapport qualite - V2.7 Offline Supervised Dataset

## Objectif

V2.7 assemble un dataset supervise offline en joignant les features causales V2.5 et les labels forward V2.6 deja valides.
Cette version ne fait aucune estimation de modele et ne produit aucun signal operationnel.

## Inputs

- `1m` features : `data/gold/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/year=2024/month=01/features-2024-01-15.parquet` (1440 lignes)
- `1m` labels : `data/gold/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/year=2024/month=01/labels-2024-01-15.parquet` (1440 lignes)
- `5m` features : `data/gold/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/year=2024/month=01/features-2024-01-15.parquet` (288 lignes)
- `5m` labels : `data/gold/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/year=2024/month=01/labels-2024-01-15.parquet` (288 lignes)
- `15m` features : `data/gold/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/year=2024/month=01/features-2024-01-15.parquet` (96 lignes)
- `15m` labels : `data/gold/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/year=2024/month=01/labels-2024-01-15.parquet` (96 lignes)
- `1h` features : `data/gold/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/year=2024/month=01/features-2024-01-15.parquet` (24 lignes)
- `1h` labels : `data/gold/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/year=2024/month=01/labels-2024-01-15.parquet` (24 lignes)

## Outputs

- `1m` dataset : `data/gold/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/year=2024/month=01/dataset-2024-01-15.parquet` (1440 lignes)
- `1m` splits : `data/gold/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/year=2024/month=01/splits-2024-01-15.parquet` (1440 lignes)
  - splits : `{'train': 864, 'validation': 288, 'test': 288}`
  - tail rows : `5`
- `5m` dataset : `data/gold/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/year=2024/month=01/dataset-2024-01-15.parquet` (288 lignes)
- `5m` splits : `data/gold/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/year=2024/month=01/splits-2024-01-15.parquet` (288 lignes)
  - splits : `{'train': 172, 'validation': 57, 'test': 59}`
  - tail rows : `5`
- `15m` dataset : `data/gold/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/year=2024/month=01/dataset-2024-01-15.parquet` (96 lignes)
- `15m` splits : `data/gold/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/year=2024/month=01/splits-2024-01-15.parquet` (96 lignes)
  - splits : `{'train': 57, 'validation': 19, 'test': 20}`
  - tail rows : `5`
- `1h` dataset : `data/gold/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/year=2024/month=01/dataset-2024-01-15.parquet` (24 lignes)
- `1h` splits : `data/gold/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/year=2024/month=01/splits-2024-01-15.parquet` (24 lignes)
  - splits : `{'train': 14, 'validation': 4, 'test': 6}`
  - tail rows : `5`

## Schema

- Version schema : `V2.7`
- Nombre de colonnes : `76`
- Le schema est strictement ordonne et refuse toute colonne supplementaire.

## Split Policy

- Train : 60 %
- Validation : 20 %
- Test : 20 %
- Shuffle : false
- Purge/embargo : `none_v2_7_preview`

## Anti-leakage

- Les features et labels restent des fichiers sources separes.
- Les hashes source_features_sha256 et source_labels_sha256 sont recalcules physiquement.
- `feature_available_ts <= decision_ts` est controle.
- `label_available_ts > decision_ts` est controle pour les labels valides.

## Limitations

- V2.7 assemble uniquement un dataset supervise offline a partir des features V2.5 et labels V2.6 valides sur BTCUSDT 2024-01-15.
- V2.7 ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

## Securite

- V2.7 ne valide aucune strategie.
- V2.7 ne produit aucun modele ML.
- V2.7 ne produit aucun backtest.
- V2.7 ne produit aucun signal de trading.
- V2.7 ne produit aucun ordre.
- V2.7 n'autorise aucun paper live.
- V2.7 n'autorise aucun trading reel.
