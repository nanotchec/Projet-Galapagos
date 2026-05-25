# Rapport qualite - V7.3 Dataset supervise offline OHLCV + trades

## Objectif

V7.3 assemble uniquement un dataset supervise offline multi-source en joignant les features causales OHLCV + aggTrades V7.2 et les labels forward V5.2 filtres sur la meme fenetre de 30 jours.
Cette preview ne fait aucun entrainement ML et ne produit aucun signal operationnel.

## Fenetre

- Debut : `2023-03-25`
- Fin : `2023-04-23`
- Nombre de jours : `30`

## Inputs

- `1m` features OHLCV+trades V7.2 : `data/research/v7_2/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2023-04-23/features.parquet` (43200 lignes)
- `1m` labels V5.2 filtres : `43200` lignes
- `5m` features OHLCV+trades V7.2 : `data/research/v7_2/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2023-04-23/features.parquet` (8640 lignes)
- `5m` labels V5.2 filtres : `8640` lignes
- `15m` features OHLCV+trades V7.2 : `data/research/v7_2/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2023-04-23/features.parquet` (2880 lignes)
- `15m` labels V5.2 filtres : `2880` lignes
- `1h` features OHLCV+trades V7.2 : `data/research/v7_2/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2023-04-23/features.parquet` (720 lignes)
- `1h` labels V5.2 filtres : `720` lignes

## Outputs

- `1m` dataset : `data/research/v7_3/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2023-04-23/dataset.parquet` (43200 lignes)
- `1m` splits : `data/research/v7_3/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2023-04-23/splits.parquet` (43200 lignes)
  - splits : `{'train': 25920, 'validation': 8640, 'test': 8640}`
  - groupes walk-forward : `{'wf_window_01': 10080, 'wf_window_02': 10080, 'wf_window_03': 10080, 'wf_window_04': 10080, 'wf_window_05_partial': 2880}`
  - warmup rows : `60`
  - tail rows : `0`
- `5m` dataset : `data/research/v7_3/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2023-04-23/dataset.parquet` (8640 lignes)
- `5m` splits : `data/research/v7_3/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2023-04-23/splits.parquet` (8640 lignes)
  - splits : `{'train': 5184, 'validation': 1728, 'test': 1728}`
  - groupes walk-forward : `{'wf_window_01': 2016, 'wf_window_02': 2016, 'wf_window_03': 2016, 'wf_window_04': 2016, 'wf_window_05_partial': 576}`
  - warmup rows : `60`
  - tail rows : `0`
- `15m` dataset : `data/research/v7_3/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2023-04-23/dataset.parquet` (2880 lignes)
- `15m` splits : `data/research/v7_3/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2023-04-23/splits.parquet` (2880 lignes)
  - splits : `{'train': 1728, 'validation': 576, 'test': 576}`
  - groupes walk-forward : `{'wf_window_01': 672, 'wf_window_02': 672, 'wf_window_03': 672, 'wf_window_04': 672, 'wf_window_05_partial': 192}`
  - warmup rows : `60`
  - tail rows : `0`
- `1h` dataset : `data/research/v7_3/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2023-04-23/dataset.parquet` (720 lignes)
- `1h` splits : `data/research/v7_3/datasets/offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2023-04-23/splits.parquet` (720 lignes)
  - splits : `{'train': 432, 'validation': 144, 'test': 144}`
  - groupes walk-forward : `{'wf_window_01': 168, 'wf_window_02': 168, 'wf_window_03': 168, 'wf_window_04': 168, 'wf_window_05_partial': 48}`
  - warmup rows : `60`
  - tail rows : `0`

## Schema

- Version schema : `DATASET_COLUMNS_V7_3`
- Nombre de colonnes dataset : `119`
- Nombre de colonnes features OHLCV+trades : `74`
- Le schema est strictement ordonne et refuse toute colonne supplementaire.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Shuffle : false.
- Purge/embargo : `none_v7_3_preview`.
- Groupes walk-forward : fenetres descriptives de 7 jours.

## Anti-leakage

- Les features V7.2 et labels V5.2 restent des fichiers sources separes.
- Les hashes `source_features_sha256` et `source_labels_sha256` sont recalcules physiquement.
- `feature_available_ts <= decision_ts` est controle.
- `label_available_ts > decision_ts` est controle pour les labels valides.
- Les labels sont inclus uniquement dans un dataset offline V7.3, jamais comme decision en ligne.

## Limitations

- V7.3 assemble uniquement un dataset supervise offline OHLCV + aggTrades sur une fenetre bornee de 30 jours.
- V7.3 ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

## Non-usage Warnings

- V7.3 ne valide aucune strategie.
- V7.3 ne produit aucun modele ML.
- V7.3 ne produit aucun backtest.
- V7.3 ne produit aucun signal de trading.
- V7.3 ne produit aucun ordre.
- V7.3 n'autorise aucun paper live.
- V7.3 n'autorise aucun trading reel.

