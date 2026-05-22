# Rapport qualite - V3.8 Dataset supervise offline 90 jours

## Objectif

V3.8 assemble un dataset supervise offline 90 jours en joignant les features causales V3.6 et les labels forward V3.7 deja valides.
Cette preview ne fait aucun entrainement ML et ne produit aucun signal operationnel.

## Inputs

- `1m` features V3.6 : `data/research/v3_6/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-01_2024-03-30/features.parquet` (129600 lignes)
- `1m` labels V3.7 : `data/research/v3_7/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-01_2024-03-30/labels.parquet` (129600 lignes)
- `5m` features V3.6 : `data/research/v3_6/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-01_2024-03-30/features.parquet` (25920 lignes)
- `5m` labels V3.7 : `data/research/v3_7/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-01_2024-03-30/labels.parquet` (25920 lignes)
- `15m` features V3.6 : `data/research/v3_6/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-01_2024-03-30/features.parquet` (8640 lignes)
- `15m` labels V3.7 : `data/research/v3_7/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-01_2024-03-30/labels.parquet` (8640 lignes)
- `1h` features V3.6 : `data/research/v3_6/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-01_2024-03-30/features.parquet` (2160 lignes)
- `1h` labels V3.7 : `data/research/v3_7/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-01_2024-03-30/labels.parquet` (2160 lignes)

## Outputs

- `1m` dataset : `data/research/v3_8/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-01_2024-03-30/dataset.parquet` (129600 lignes)
- `1m` splits : `data/research/v3_8/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-01_2024-03-30/splits.parquet` (129600 lignes)
  - splits : `{'train': 77760, 'validation': 25920, 'test': 25920}`
  - warmup rows : `30`
  - tail rows : `5`
- `5m` dataset : `data/research/v3_8/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-01_2024-03-30/dataset.parquet` (25920 lignes)
- `5m` splits : `data/research/v3_8/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-01_2024-03-30/splits.parquet` (25920 lignes)
  - splits : `{'train': 15552, 'validation': 5184, 'test': 5184}`
  - warmup rows : `30`
  - tail rows : `5`
- `15m` dataset : `data/research/v3_8/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-01_2024-03-30/dataset.parquet` (8640 lignes)
- `15m` splits : `data/research/v3_8/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-01_2024-03-30/splits.parquet` (8640 lignes)
  - splits : `{'train': 5184, 'validation': 1728, 'test': 1728}`
  - warmup rows : `30`
  - tail rows : `5`
- `1h` dataset : `data/research/v3_8/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-01_2024-03-30/dataset.parquet` (2160 lignes)
- `1h` splits : `data/research/v3_8/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-01_2024-03-30/splits.parquet` (2160 lignes)
  - splits : `{'train': 1296, 'validation': 432, 'test': 432}`
  - warmup rows : `30`
  - tail rows : `5`

## Schema

- Version schema : `V3.8`
- Nombre de colonnes : `76`
- Le schema est strictement ordonne et refuse toute colonne supplementaire.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Shuffle : false.
- Purge/embargo : `none_v3_8_preview`.

## Anti-leakage

- Les features V3.6 et labels V3.7 restent des fichiers sources separes.
- Les hashes `source_features_sha256` et `source_labels_sha256` sont recalcules physiquement.
- `feature_available_ts <= decision_ts` est controle.
- `label_available_ts > decision_ts` est controle pour les labels valides.
- Les labels sont inclus uniquement dans un dataset offline V3.8, jamais comme decision en ligne.

## Limitations

- V3.8 assemble uniquement un dataset supervise offline 90 jours a partir des features V3.6 et labels V3.7 valides.
- V3.8 ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

## Non-usage Warnings

- V3.8 ne valide aucune strategie.
- V3.8 ne produit aucun modele ML.
- V3.8 ne produit aucun backtest.
- V3.8 ne produit aucun signal de trading.
- V3.8 ne produit aucun ordre.
- V3.8 n'autorise aucun paper live.
- V3.8 n'autorise aucun trading reel.

