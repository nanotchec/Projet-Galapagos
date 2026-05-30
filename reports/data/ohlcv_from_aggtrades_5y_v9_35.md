# V9.35 - OHLCV From AggTrades 5Y Derivation

## Resume
- Decision V9.35 : `ohlcv_from_aggtrades_5y_derivation_complete_with_warnings`.
- Recommandation suivante : `V9.36 - OHLCV From AggTrades 5Y Coverage Validation`.
- Qualite : `PASS`.
- Couverture : `target_5y_window_complete`.
- Timeframes produits : `['1m', '5m', '15m', '1h']`.
- Row counts : `{'1m': 2630880, '5m': 526176, '15m': 175392, '1h': 43848}`.
- Buckets zero-trade remplis causalement : `{'1m': 542, '5m': 108, '15m': 36, '1h': 8}`.

## Methode
- Les bougies 1m sont derivees directement depuis les aggTrades silver valides V9.32, ordonnes par `event_ts` puis `aggregate_trade_id`.
- Les bougies 5m/15m/1h sont derivees par resampling deterministe du 1m derive.
- `decision_ts` et `available_ts` sont fixes a `close_ts`, sans donnees futures.
- `ohlcv_source_type = derived_from_aggtrades` distingue explicitement cette base des klines Binance.

## Parite Binance
- Statut parite : `PASS`.
- Warnings : `[]`.

## Garde-fous
- Aucun reseau, aucun telechargement, aucun feature store combine, aucun label, dataset supervise, ML, walk-forward, backtest, strategie, signal ou ordre.
- Aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.
