# Rapport qualite - V5.3 Dataset supervise offline historique max

## Objectif

V5.3 assemble uniquement un dataset supervise offline en joignant les features causales V5.1 et les labels forward V5.2 deja valides sur la fenetre historique continue V5.0.
Cette preview ne fait aucun entrainement ML et ne produit aucun signal operationnel.

## Fenetre

- Debut : `2023-03-25`
- Fin : `2026-05-23`
- Nombre de jours : `1156`

## Inputs

- `1m` features V5.1 : `data/research/v5_1/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2026-05-23/features.parquet` (1664640 lignes)
- `1m` labels V5.2 : `data/research/v5_2/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2026-05-23/labels.parquet` (1664640 lignes)
- `5m` features V5.1 : `data/research/v5_1/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2026-05-23/features.parquet` (332928 lignes)
- `5m` labels V5.2 : `data/research/v5_2/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2026-05-23/labels.parquet` (332928 lignes)
- `15m` features V5.1 : `data/research/v5_1/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2026-05-23/features.parquet` (110976 lignes)
- `15m` labels V5.2 : `data/research/v5_2/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2026-05-23/labels.parquet` (110976 lignes)
- `1h` features V5.1 : `data/research/v5_1/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2026-05-23/features.parquet` (27744 lignes)
- `1h` labels V5.2 : `data/research/v5_2/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2026-05-23/labels.parquet` (27744 lignes)

## Outputs

- `1m` dataset : `data/research/v5_3/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2026-05-23/dataset.parquet` (1664640 lignes)
- `1m` splits : `data/research/v5_3/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2026-05-23/splits.parquet` (1664640 lignes)
  - splits : `{'train': 998784, 'validation': 332928, 'test': 332928}`
  - groupes walk-forward : `14`
  - warmup rows : `30`
  - tail rows : `5`
- `5m` dataset : `data/research/v5_3/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2026-05-23/dataset.parquet` (332928 lignes)
- `5m` splits : `data/research/v5_3/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2026-05-23/splits.parquet` (332928 lignes)
  - splits : `{'train': 199756, 'validation': 66585, 'test': 66587}`
  - groupes walk-forward : `14`
  - warmup rows : `30`
  - tail rows : `5`
- `15m` dataset : `data/research/v5_3/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2026-05-23/dataset.parquet` (110976 lignes)
- `15m` splits : `data/research/v5_3/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2026-05-23/splits.parquet` (110976 lignes)
  - splits : `{'train': 66585, 'validation': 22195, 'test': 22196}`
  - groupes walk-forward : `14`
  - warmup rows : `30`
  - tail rows : `5`
- `1h` dataset : `data/research/v5_3/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2026-05-23/dataset.parquet` (27744 lignes)
- `1h` splits : `data/research/v5_3/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2026-05-23/splits.parquet` (27744 lignes)
  - splits : `{'train': 16646, 'validation': 5548, 'test': 5550}`
  - groupes walk-forward : `14`
  - warmup rows : `30`
  - tail rows : `5`

## Schema

- Version schema : `V5.3`
- Nombre de colonnes dataset : `76`
- Le schema est strictement ordonne et refuse toute colonne supplementaire.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Shuffle : false.
- Purge/embargo : `none_v5_3_preview`.
- Groupes walk-forward : `calendar_quarter`.

## Anti-leakage

- Les features V5.1 et labels V5.2 restent des fichiers sources separes.
- Les hashes `source_features_sha256` et `source_labels_sha256` sont recalcules physiquement.
- `feature_available_ts <= decision_ts` est controle.
- `label_available_ts > decision_ts` est controle pour les labels valides.
- Les labels sont inclus uniquement dans un dataset offline V5.3, jamais comme decision en ligne.

## Limitations

- V5.3 assemble uniquement un dataset supervise offline sur la fenetre historique continue validee par V5.0.
- V5.3 prepare des groupes walk-forward descriptifs mais ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

## Non-usage Warnings

- V5.3 ne valide aucune strategie.
- V5.3 ne produit aucun modele ML.
- V5.3 ne produit aucun backtest.
- V5.3 ne produit aucun signal de trading.
- V5.3 ne produit aucun ordre.
- V5.3 n'autorise aucun paper live.
- V5.3 n'autorise aucun trading reel.

