# V9.36 - OHLCV From AggTrades 5Y Coverage Validation

## Resume
- Decision V9.36 : `ohlcv_from_aggtrades_5y_validation_pass_with_non_blocking_warnings`.
- Recommandation suivante : `V9.37 - OHLCV + AggTrades 5Y Feature Store`.
- Couverture : `target_5y_window_complete`.
- Qualite : `PASS`.
- Parite Binance : `PASS`.
- Warnings : `['1m: 542 zero-trade buckets non bloquants', '5m: 108 zero-trade buckets non bloquants', '15m: 36 zero-trade buckets non bloquants', '1h: 8 zero-trade buckets non bloquants']`.

## Validation
- Les 4 timeframes derives 1m/5m/15m/1h couvrent 2021-05-05 -> 2026-05-05.
- Les invariants OHLCV, timestamps, colonnes interdites et lineage sont controles.
- Les buckets zero-trade sont verifies comme non bloquants si OHLC=previous close, volume=0, trades_count=0, sans futur.

## Garde-fous
- Aucun reseau, aucun telechargement, aucun feature store combine, aucun label, dataset supervise, ML, walk-forward, backtest, strategie, signal ou ordre.
- Aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.
