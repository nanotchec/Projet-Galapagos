# Rapport qualite - V4.5 Dataset supervise offline 1 an

## Objectif

V4.5 assemble un dataset supervise offline 1 an en joignant les features causales V4.3 et les labels forward V4.4 deja valides.
Cette preview ne fait aucun entrainement ML et ne produit aucun signal operationnel.

## Inputs

- `1m` features V4.3 : `data/research/v4_3/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-01_2024-12-31/features.parquet` (527040 lignes)
- `1m` labels V4.4 : `data/research/v4_4/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-01_2024-12-31/labels.parquet` (527040 lignes)
- `5m` features V4.3 : `data/research/v4_3/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-01_2024-12-31/features.parquet` (105408 lignes)
- `5m` labels V4.4 : `data/research/v4_4/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-01_2024-12-31/labels.parquet` (105408 lignes)
- `15m` features V4.3 : `data/research/v4_3/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-01_2024-12-31/features.parquet` (35136 lignes)
- `15m` labels V4.4 : `data/research/v4_4/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-01_2024-12-31/labels.parquet` (35136 lignes)
- `1h` features V4.3 : `data/research/v4_3/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-01_2024-12-31/features.parquet` (8784 lignes)
- `1h` labels V4.4 : `data/research/v4_4/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-01_2024-12-31/labels.parquet` (8784 lignes)

## Outputs

- `1m` dataset : `data/research/v4_5/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-01_2024-12-31/dataset.parquet` (527040 lignes)
- `1m` splits : `data/research/v4_5/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-01_2024-12-31/splits.parquet` (527040 lignes)
  - splits : `{'train': 316224, 'validation': 105408, 'test': 105408}`
  - warmup rows : `30`
  - tail rows : `5`
- `5m` dataset : `data/research/v4_5/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-01_2024-12-31/dataset.parquet` (105408 lignes)
- `5m` splits : `data/research/v4_5/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-01_2024-12-31/splits.parquet` (105408 lignes)
  - splits : `{'train': 63244, 'validation': 21082, 'test': 21082}`
  - warmup rows : `30`
  - tail rows : `5`
- `15m` dataset : `data/research/v4_5/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-01_2024-12-31/dataset.parquet` (35136 lignes)
- `15m` splits : `data/research/v4_5/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-01_2024-12-31/splits.parquet` (35136 lignes)
  - splits : `{'train': 21081, 'validation': 7027, 'test': 7028}`
  - warmup rows : `30`
  - tail rows : `5`
- `1h` dataset : `data/research/v4_5/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-01_2024-12-31/dataset.parquet` (8784 lignes)
- `1h` splits : `data/research/v4_5/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-01_2024-12-31/splits.parquet` (8784 lignes)
  - splits : `{'train': 5270, 'validation': 1757, 'test': 1757}`
  - warmup rows : `30`
  - tail rows : `5`

## Schema

- Version schema : `V4.5`
- Nombre de colonnes : `76`
- Le schema est strictement ordonne et refuse toute colonne supplementaire.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Shuffle : false.
- Purge/embargo : `none_v4_5_preview`.

## Anti-leakage

- Les features V4.3 et labels V4.4 restent des fichiers sources separes.
- Les hashes `source_features_sha256` et `source_labels_sha256` sont recalcules physiquement.
- `feature_available_ts <= decision_ts` est controle.
- `label_available_ts > decision_ts` est controle pour les labels valides.
- Les labels sont inclus uniquement dans un dataset offline V4.5, jamais comme decision en ligne.

## Limitations

- V4.5 assemble uniquement un dataset supervise offline 1 an a partir des features V4.3 et labels V4.4 valides.
- V4.5 ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

## Non-usage Warnings

- V4.5 ne valide aucune strategie.
- V4.5 ne produit aucun modele ML.
- V4.5 ne produit aucun backtest.
- V4.5 ne produit aucun signal de trading.
- V4.5 ne produit aucun ordre.
- V4.5 n'autorise aucun paper live.
- V4.5 n'autorise aucun trading reel.
