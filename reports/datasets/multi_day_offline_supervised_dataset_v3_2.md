# Rapport qualite - V3.2 Dataset supervise offline multi-day

## Objectif

V3.2 assemble un dataset supervise offline multi-day en joignant les features causales V3.0 et les labels forward V3.1 deja valides.
Cette preview ne fait aucun entrainement ML et ne produit aucun signal operationnel.

## Inputs

- `1m` features V3.0 : `data/research/v3_0/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-15_2024-01-21/features.parquet` (10080 lignes)
- `1m` labels V3.1 : `data/research/v3_1/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-15_2024-01-21/labels.parquet` (10080 lignes)
- `5m` features V3.0 : `data/research/v3_0/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-15_2024-01-21/features.parquet` (2016 lignes)
- `5m` labels V3.1 : `data/research/v3_1/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-15_2024-01-21/labels.parquet` (2016 lignes)
- `15m` features V3.0 : `data/research/v3_0/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-15_2024-01-21/features.parquet` (672 lignes)
- `15m` labels V3.1 : `data/research/v3_1/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-15_2024-01-21/labels.parquet` (672 lignes)
- `1h` features V3.0 : `data/research/v3_0/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-15_2024-01-21/features.parquet` (168 lignes)
- `1h` labels V3.1 : `data/research/v3_1/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-15_2024-01-21/labels.parquet` (168 lignes)

## Outputs

- `1m` dataset : `data/research/v3_2/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-15_2024-01-21/dataset.parquet` (10080 lignes)
- `1m` splits : `data/research/v3_2/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-15_2024-01-21/splits.parquet` (10080 lignes)
  - splits : `{'train': 6048, 'validation': 2016, 'test': 2016}`
  - tail rows : `5`
- `5m` dataset : `data/research/v3_2/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-15_2024-01-21/dataset.parquet` (2016 lignes)
- `5m` splits : `data/research/v3_2/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-15_2024-01-21/splits.parquet` (2016 lignes)
  - splits : `{'train': 1209, 'validation': 403, 'test': 404}`
  - tail rows : `5`
- `15m` dataset : `data/research/v3_2/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-15_2024-01-21/dataset.parquet` (672 lignes)
- `15m` splits : `data/research/v3_2/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-15_2024-01-21/splits.parquet` (672 lignes)
  - splits : `{'train': 403, 'validation': 134, 'test': 135}`
  - tail rows : `5`
- `1h` dataset : `data/research/v3_2/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-15_2024-01-21/dataset.parquet` (168 lignes)
- `1h` splits : `data/research/v3_2/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-15_2024-01-21/splits.parquet` (168 lignes)
  - splits : `{'train': 100, 'validation': 33, 'test': 35}`
  - tail rows : `5`

## Schema

- Version schema : `V3.2`
- Nombre de colonnes : `76`
- Le schema est strictement ordonne et refuse toute colonne supplementaire.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Shuffle : false.
- Purge/embargo : `none_v3_2_preview`.

## Anti-leakage

- Les features V3.0 et labels V3.1 restent des fichiers sources separes.
- Les hashes source_features_sha256 et source_labels_sha256 sont recalcules physiquement.
- `feature_available_ts <= decision_ts` est controle.
- `label_available_ts > decision_ts` est controle pour les labels valides.
- Les labels sont inclus uniquement dans un dataset offline V3.2, jamais comme decision en ligne.

## Limitations

- V3.2 assemble uniquement un dataset supervise offline multi-day a partir des features V3.0 et labels V3.1 valides sur BTCUSDT 2024-01-15 a 2024-01-21.
- V3.2 ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

## Non-usage Warnings

- V3.2 ne valide aucune strategie.
- V3.2 ne produit aucun modele ML.
- V3.2 ne produit aucun backtest.
- V3.2 ne produit aucun signal de trading.
- V3.2 ne produit aucun ordre.
- V3.2 n'autorise aucun paper live.
- V3.2 n'autorise aucun trading reel.
