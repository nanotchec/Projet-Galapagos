# Rapport qualite - V7.9 Dataset supervise offline OHLCV + trades

## Objectif

V7.9 assemble uniquement un dataset supervise offline multi-source en joignant les features causales OHLCV + aggTrades V7.8 et les labels forward V5.2 filtres sur la meme fenetre de 90 jours.
Cette preview ne fait aucun entrainement ML et ne produit aucune sortie operationnelle.

## Fenetre

- Debut : `2023-03-25`
- Fin : `2023-06-22`
- Nombre de jours : `90`

## Inputs

- `1m` features OHLCV+trades V7.8 : `data/research/v7_8/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2023-06-22/features.parquet` (129600 lignes)
- `1m` labels V5.2 filtres : `129600` lignes
- `5m` features OHLCV+trades V7.8 : `data/research/v7_8/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2023-06-22/features.parquet` (25920 lignes)
- `5m` labels V5.2 filtres : `25920` lignes
- `15m` features OHLCV+trades V7.8 : `data/research/v7_8/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2023-06-22/features.parquet` (8640 lignes)
- `15m` labels V5.2 filtres : `8640` lignes
- `1h` features OHLCV+trades V7.8 : `data/research/v7_8/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2023-06-22/features.parquet` (2160 lignes)
- `1h` labels V5.2 filtres : `2160` lignes

## Outputs

- `1m` dataset : `data/research/v7_9/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2023-06-22/dataset.parquet` (129600 lignes)
- `1m` splits : `data/research/v7_9/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2023-06-22/splits.parquet` (129600 lignes)
  - splits : `{'train': 77760, 'validation': 25920, 'test': 25920}`
  - groupes walk-forward : `{'wf_2023_03_partial': 10080, 'wf_2023_04': 43200, 'wf_2023_05': 44640, 'wf_2023_06_partial': 31680}`
  - warmup rows : `60`
  - tail rows : `0`
- `5m` dataset : `data/research/v7_9/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2023-06-22/dataset.parquet` (25920 lignes)
- `5m` splits : `data/research/v7_9/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2023-06-22/splits.parquet` (25920 lignes)
  - splits : `{'train': 15552, 'validation': 5184, 'test': 5184}`
  - groupes walk-forward : `{'wf_2023_03_partial': 2016, 'wf_2023_04': 8640, 'wf_2023_05': 8928, 'wf_2023_06_partial': 6336}`
  - warmup rows : `60`
  - tail rows : `0`
- `15m` dataset : `data/research/v7_9/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2023-06-22/dataset.parquet` (8640 lignes)
- `15m` splits : `data/research/v7_9/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2023-06-22/splits.parquet` (8640 lignes)
  - splits : `{'train': 5184, 'validation': 1728, 'test': 1728}`
  - groupes walk-forward : `{'wf_2023_03_partial': 672, 'wf_2023_04': 2880, 'wf_2023_05': 2976, 'wf_2023_06_partial': 2112}`
  - warmup rows : `60`
  - tail rows : `0`
- `1h` dataset : `data/research/v7_9/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2023-06-22/dataset.parquet` (2160 lignes)
- `1h` splits : `data/research/v7_9/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2023-06-22/splits.parquet` (2160 lignes)
  - splits : `{'train': 1296, 'validation': 432, 'test': 432}`
  - groupes walk-forward : `{'wf_2023_03_partial': 168, 'wf_2023_04': 720, 'wf_2023_05': 744, 'wf_2023_06_partial': 528}`
  - warmup rows : `60`
  - tail rows : `0`

## Schema

- Version schema : `DATASET_COLUMNS_V7_9`
- Nombre de colonnes dataset : `119`
- Nombre de colonnes features OHLCV+trades : `74`
- Le schema est strictement ordonne et refuse toute colonne supplementaire.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Shuffle : false.
- Purge/embargo : `none_v7_9_preview`.
- Groupes walk-forward : groupes calendaires mensuels descriptifs.

## Anti-leakage

- Les features V7.8 et labels V5.2 restent des fichiers sources separes.
- Les hashes `source_features_sha256` et `source_labels_sha256` sont recalcules physiquement.
- `feature_available_ts <= decision_ts` est controle.
- `label_available_ts > decision_ts` est controle pour les labels valides.
- Les labels sont inclus uniquement dans un dataset offline V7.9, jamais comme decision en ligne.

## Limitations

- V7.9 assemble uniquement un dataset supervise offline OHLCV + aggTrades sur une fenetre bornee de 90 jours.
- V7.9 ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

## Non-usage Warnings

- V7.9 ne valide aucune strategie.
- V7.9 ne produit aucun modele ML.
- V7.9 ne produit aucun backtest.
- V7.9 ne produit aucun signal de trading.
- V7.9 ne produit aucun ordre.
- V7.9 n'autorise aucun paper live.
- V7.9 n'autorise aucun trading reel.
