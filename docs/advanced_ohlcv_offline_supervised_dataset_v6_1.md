# Rapport qualite - V6.1 Dataset supervise offline advanced OHLCV

## Objectif

V6.1 assemble uniquement un dataset supervise offline en joignant les advanced OHLCV features V6.0 et les labels forward V5.2 deja valides sur la fenetre historique continue V5.0.
Cette preview ne fait aucun entrainement ML et ne produit aucun signal operationnel.

## Fenetre

- Debut : `2023-03-25`
- Fin : `2026-05-23`
- Nombre de jours : `1156`

## Inputs

- `1m` advanced features V6.0 : `data/research/v6_0/features/advanced_ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2026-05-23/features.parquet` (1664640 lignes)
- `1m` labels V5.2 : `data/research/v5_2/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2026-05-23/labels.parquet` (1664640 lignes)
- `5m` advanced features V6.0 : `data/research/v6_0/features/advanced_ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2026-05-23/features.parquet` (332928 lignes)
- `5m` labels V5.2 : `data/research/v5_2/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2026-05-23/labels.parquet` (332928 lignes)
- `15m` advanced features V6.0 : `data/research/v6_0/features/advanced_ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2026-05-23/features.parquet` (110976 lignes)
- `15m` labels V5.2 : `data/research/v5_2/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2026-05-23/labels.parquet` (110976 lignes)
- `1h` advanced features V6.0 : `data/research/v6_0/features/advanced_ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2026-05-23/features.parquet` (27744 lignes)
- `1h` labels V5.2 : `data/research/v5_2/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2026-05-23/labels.parquet` (27744 lignes)

## Outputs

- `1m` dataset : `data/research/v6_1/datasets/offline_supervised_advanced_ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2026-05-23/dataset.parquet` (1664640 lignes)
- `1m` splits : `data/research/v6_1/datasets/offline_supervised_advanced_ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2026-05-23/splits.parquet` (1664640 lignes)
  - splits : `{'train': 998784, 'validation': 332928, 'test': 332928}`
  - groupes walk-forward : `14`
  - warmup rows : `266`
  - tail rows : `5`
- `5m` dataset : `data/research/v6_1/datasets/offline_supervised_advanced_ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2026-05-23/dataset.parquet` (332928 lignes)
- `5m` splits : `data/research/v6_1/datasets/offline_supervised_advanced_ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2026-05-23/splits.parquet` (332928 lignes)
  - splits : `{'train': 199756, 'validation': 66585, 'test': 66587}`
  - groupes walk-forward : `14`
  - warmup rows : `239`
  - tail rows : `5`
- `15m` dataset : `data/research/v6_1/datasets/offline_supervised_advanced_ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2026-05-23/dataset.parquet` (110976 lignes)
- `15m` splits : `data/research/v6_1/datasets/offline_supervised_advanced_ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2026-05-23/splits.parquet` (110976 lignes)
  - splits : `{'train': 66585, 'validation': 22195, 'test': 22196}`
  - groupes walk-forward : `14`
  - warmup rows : `239`
  - tail rows : `5`
- `1h` dataset : `data/research/v6_1/datasets/offline_supervised_advanced_ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2026-05-23/dataset.parquet` (27744 lignes)
- `1h` splits : `data/research/v6_1/datasets/offline_supervised_advanced_ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2026-05-23/splits.parquet` (27744 lignes)
  - splits : `{'train': 16646, 'validation': 5548, 'test': 5550}`
  - groupes walk-forward : `14`
  - warmup rows : `239`
  - tail rows : `5`

## Schema

- Version schema : `V6.1`
- Nombre de colonnes dataset : `206`
- Nombre de colonnes advanced features : `158`
- Le schema est strictement ordonne et refuse toute colonne supplementaire.
- `macd_like_signal` est une feature technique MACD-like, pas un signal de trading.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Shuffle : false.
- Purge/embargo : `none_v6_1_preview`.
- Groupes walk-forward : `calendar_quarter`.

## Anti-leakage

- Les advanced features V6.0 et labels V5.2 restent des fichiers sources separes.
- Les hashes `source_features_sha256` et `source_labels_sha256` sont recalcules physiquement.
- `feature_available_ts <= decision_ts` est controle.
- `label_available_ts > decision_ts` est controle pour les labels valides.
- Les labels sont inclus uniquement dans un dataset offline V6.1, jamais comme decision en ligne.

## Limitations

- V6.1 assemble uniquement un dataset supervise offline a partir des advanced OHLCV features V6.0 et labels V5.2.
- V6.1 prepare des groupes walk-forward descriptifs mais ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

## Non-usage Warnings

- V6.1 ne valide aucune strategie.
- V6.1 ne produit aucun modele ML.
- V6.1 ne produit aucun backtest.
- V6.1 ne produit aucun signal de trading.
- V6.1 ne produit aucun ordre.
- V6.1 n'autorise aucun paper live.
- V6.1 n'autorise aucun trading reel.

