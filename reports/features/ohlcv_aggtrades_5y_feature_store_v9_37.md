# V9.37 - OHLCV + AggTrades 5Y Feature Store

## Resume
- Decision V9.37 : `ohlcv_aggtrades_5y_feature_store_created_with_warnings`.
- Recommandation suivante : `V9.38 - OHLCV + AggTrades 5Y Feature Store Validation`.
- Timeframes produits : `['1m', '5m', '15m', '1h']`.
- Row counts : `{'1m': 2630880, '5m': 526176, '15m': 175392, '1h': 43848}`.
- Feature columns count : `41`.
- Qualite : `PASS`.
- Couverture : `target_5y_feature_window_complete`.
- Warnings : `['median_trade_size exact, large_trade_count exact et buyer_maker_count exact non inclus car V9.37 evite un scan direct massif des aggTrades.', '1m: 60 warmup rows avec nulls attendus', '5m: 60 warmup rows avec nulls attendus', '15m: 60 warmup rows avec nulls attendus', '1h: 60 warmup rows avec nulls attendus', '1m: 542 zero-trade buckets conserves comme flags causaux', '5m: 108 zero-trade buckets conserves comme flags causaux', '15m: 36 zero-trade buckets conserves comme flags causaux', '1h: 8 zero-trade buckets conserves comme flags causaux']`.

## Sources
- OHLCV 5Y derivee depuis aggTrades V9.35, validee V9.36.
- AggTrades 5Y valides V9.32.
- Les features aggTrades V9.37 utilisent les agregats aggTrades deja materialises dans l'OHLCV derivee.

## Garde-fous
- Aucun label, dataset supervise, ML, walk-forward, backtest, strategie, signal ou ordre.
- Aucun reseau, aucun telechargement, aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.
