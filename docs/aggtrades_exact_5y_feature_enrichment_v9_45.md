# Enrichissement features exactes aggTrades V9.45

- Decision : `aggtrades_exact_5y_feature_enrichment_created_with_warnings`.
- Recommandation : `V9.46 - AggTrades Exact 5Y Feature Enrichment Validation`.
- Fenetre : `2021-05-05` -> `2026-05-05`.
- Timeframes : `['1m', '5m', '15m', '1h']`.
- Strategie : `parallel_daily_partitioned_aggtrades_scan_then_timeframe_concat`.
- Chunking : `read one daily silver parquet per worker; default bounded parallelism is 12 workers via GALAPAGOS_V9_45_WORKERS`.
- Feature columns : `56`.
- Row counts : `{'1m': 2630880, '5m': 526176, '15m': 175392, '1h': 43848}`.
- Qualite : `PASS`.
- Coverage : `target_5y_exact_feature_window_complete`.
- Leakage guard : `PASS`.
- Forbidden columns scan : `PASS`.

## Sorties

- `1m` : `/Users/lilianserre/Documents/projets/projet-galapagos/data/research/v9_45/features/aggtrades_exact_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2021-05-05_2026-05-05/features.parquet`.
- `5m` : `/Users/lilianserre/Documents/projets/projet-galapagos/data/research/v9_45/features/aggtrades_exact_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2021-05-05_2026-05-05/features.parquet`.
- `15m` : `/Users/lilianserre/Documents/projets/projet-galapagos/data/research/v9_45/features/aggtrades_exact_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2021-05-05_2026-05-05/features.parquet`.
- `1h` : `/Users/lilianserre/Documents/projets/projet-galapagos/data/research/v9_45/features/aggtrades_exact_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2021-05-05_2026-05-05/features.parquet`.

## Garde-fous

- Aucun trading.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucun walk-forward.
- Aucun ML.
- Aucun dataset supervise.
- Aucun label cree.
- Aucune strategie.
- Aucun signal actionnable.
- Aucun modele persistant.
- Aucun reseau.
- Aucun telechargement de nouvelles donnees.
- Aucune suppression destructive.
- Aucun sidecar et aucune empreinte ZIP.
