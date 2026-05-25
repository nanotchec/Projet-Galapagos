# Rapport qualite - V8.4 Dataset supervise offline OHLCV + trades

## Objectif

V8.4 assemble uniquement un dataset supervise offline multi-source en joignant les features causales OHLCV + aggTrades V8.3 et les labels forward V5.2 filtres sur la meme fenetre d'environ 1 an.
Cette preview ne fait aucun entrainement ML et ne produit aucune sortie operationnelle.

## Fenetre

- Debut : `2023-03-25`
- Fin : `2024-03-24`
- Nombre de jours : `366`

## Inputs

- `1m` features OHLCV+trades V8.3 : `data/research/v8_3/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2024-03-24/features.parquet` (527040 lignes)
- `1m` labels V5.2 filtres : `527040` lignes
- `5m` features OHLCV+trades V8.3 : `data/research/v8_3/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2024-03-24/features.parquet` (105408 lignes)
- `5m` labels V5.2 filtres : `105408` lignes
- `15m` features OHLCV+trades V8.3 : `data/research/v8_3/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2024-03-24/features.parquet` (35136 lignes)
- `15m` labels V5.2 filtres : `35136` lignes
- `1h` features OHLCV+trades V8.3 : `data/research/v8_3/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2024-03-24/features.parquet` (8784 lignes)
- `1h` labels V5.2 filtres : `8784` lignes

## Outputs

- `1m` dataset : `data/research/v8_4/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2024-03-24/dataset.parquet` (527040 lignes)
- `1m` splits : `data/research/v8_4/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2024-03-24/splits.parquet` (527040 lignes)
  - splits : `{'train': 316224, 'validation': 105408, 'test': 105408}`
  - groupes walk-forward : `{'wf_2023_03_partial': 10080, 'wf_2023_04': 43200, 'wf_2023_05': 44640, 'wf_2023_06': 43200, 'wf_2023_07': 44640, 'wf_2023_08': 44640, 'wf_2023_09': 43200, 'wf_2023_10': 44640, 'wf_2023_11': 43200, 'wf_2023_12': 44640, 'wf_2024_01': 44640, 'wf_2024_02': 41760, 'wf_2024_03_partial': 34560}`
  - warmup rows : `60`
  - tail rows : `0`
- `5m` dataset : `data/research/v8_4/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2024-03-24/dataset.parquet` (105408 lignes)
- `5m` splits : `data/research/v8_4/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2024-03-24/splits.parquet` (105408 lignes)
  - splits : `{'train': 63244, 'validation': 21082, 'test': 21082}`
  - groupes walk-forward : `{'wf_2023_03_partial': 2016, 'wf_2023_04': 8640, 'wf_2023_05': 8928, 'wf_2023_06': 8640, 'wf_2023_07': 8928, 'wf_2023_08': 8928, 'wf_2023_09': 8640, 'wf_2023_10': 8928, 'wf_2023_11': 8640, 'wf_2023_12': 8928, 'wf_2024_01': 8928, 'wf_2024_02': 8352, 'wf_2024_03_partial': 6912}`
  - warmup rows : `60`
  - tail rows : `0`
- `15m` dataset : `data/research/v8_4/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2024-03-24/dataset.parquet` (35136 lignes)
- `15m` splits : `data/research/v8_4/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2024-03-24/splits.parquet` (35136 lignes)
  - splits : `{'train': 21081, 'validation': 7027, 'test': 7028}`
  - groupes walk-forward : `{'wf_2023_03_partial': 672, 'wf_2023_04': 2880, 'wf_2023_05': 2976, 'wf_2023_06': 2880, 'wf_2023_07': 2976, 'wf_2023_08': 2976, 'wf_2023_09': 2880, 'wf_2023_10': 2976, 'wf_2023_11': 2880, 'wf_2023_12': 2976, 'wf_2024_01': 2976, 'wf_2024_02': 2784, 'wf_2024_03_partial': 2304}`
  - warmup rows : `60`
  - tail rows : `0`
- `1h` dataset : `data/research/v8_4/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2024-03-24/dataset.parquet` (8784 lignes)
- `1h` splits : `data/research/v8_4/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2024-03-24/splits.parquet` (8784 lignes)
  - splits : `{'train': 5270, 'validation': 1757, 'test': 1757}`
  - groupes walk-forward : `{'wf_2023_03_partial': 168, 'wf_2023_04': 720, 'wf_2023_05': 744, 'wf_2023_06': 720, 'wf_2023_07': 744, 'wf_2023_08': 744, 'wf_2023_09': 720, 'wf_2023_10': 744, 'wf_2023_11': 720, 'wf_2023_12': 744, 'wf_2024_01': 744, 'wf_2024_02': 696, 'wf_2024_03_partial': 576}`
  - warmup rows : `60`
  - tail rows : `0`

## Schema

- Version schema : `DATASET_COLUMNS_V8_4`
- Nombre de colonnes dataset : `119`
- Nombre de colonnes features OHLCV+trades : `74`
- Le schema est strictement ordonne et refuse toute colonne supplementaire.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Shuffle : false.
- Purge/embargo : `none_v8_4_preview`.
- Groupes walk-forward : groupes calendaires mensuels descriptifs.

## Anti-leakage

- Les features V8.3 et labels V5.2 restent des fichiers sources separes.
- Les hashes `source_features_sha256` et `source_labels_sha256` sont recalcules physiquement.
- `feature_available_ts <= decision_ts` est controle.
- `label_available_ts > decision_ts` est controle pour les labels valides.
- Les labels sont inclus uniquement dans un dataset offline V8.4, jamais comme decision en ligne.

## Limitations

- V8.4 assemble uniquement un dataset supervise offline OHLCV + aggTrades sur une fenetre d'environ 1 an.
- V8.4 ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

## Non-usage Warnings

- V8.4 ne valide aucune strategie.
- V8.4 ne produit aucun modele ML.
- V8.4 ne produit aucun backtest.
- V8.4 ne produit aucun signal de trading.
- V8.4 ne produit aucun ordre.
- V8.4 n'autorise aucun paper live.
- V8.4 n'autorise aucun trading reel.
