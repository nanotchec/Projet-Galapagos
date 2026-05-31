# Feature store combine OHLCV + aggTrades exactes 5Y V9.47

- Decision : `ohlcv_aggtrades_exact_5y_feature_store_created_with_warnings`.
- Recommandation : `V9.48 - Combined OHLCV + Exact AggTrades 5Y Feature Store Validation`.
- Fenetre : `2021-05-05` -> `2026-05-05`.
- Timeframes : `['1m', '5m', '15m', '1h']`.
- Row counts : `{'1m': 2630880, '5m': 526176, '15m': 175392, '1h': 43848}`.
- Colonnes base : `41`.
- Colonnes exactes : `56`.
- Colonnes combinees : `97`.
- Qualite : `PASS`.
- Coverage : `target_5y_combined_feature_window_complete`.
- Leakage guard : `PASS`.
- Forbidden columns scan : `PASS`.

## Garde-fous

- Feature-store-only.
- Aucun label, dataset supervise, ML, backtest, walk-forward, strategie ou signal.
- Aucun reseau, aucune cle API, aucun endpoint prive.
- Aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.
