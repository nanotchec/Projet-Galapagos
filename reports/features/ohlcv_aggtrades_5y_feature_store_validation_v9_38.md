# V9.38 - Validation Feature Store OHLCV + AggTrades 5Y

## Resume
- Decision V9.38 : `ohlcv_aggtrades_5y_feature_store_validated_with_non_blocking_warnings`.
- Recommandation suivante : `V9.39 - OHLCV + AggTrades 5Y Dataset`.
- Couverture : `target_5y_feature_window_complete`.
- Schema : `PASS`.
- Qualite : `PASS`.
- Leakage guard : `PASS`.
- Row counts : `{'1m': 2630880, '5m': 526176, '15m': 175392, '1h': 43848}`.
- Feature columns count : `41`.

## Zero-trade buckets
- Statut : `PASS`.
- Counts : `{'1m': 542, '5m': 108, '15m': 36, '1h': 8}`.

## Limitations
- V9.38 confirme que V9.37 ne rescane pas directement les 3.2B lignes aggTrades.
- median_trade_size exact, large_trade_count exact et buyer_maker_count exact restent absents, non bloquants pour le dataset V9.39.

## Garde-fous
- Validation-only : aucun label, dataset supervise, ML, walk-forward, backtest, strategie, signal ou ordre.
- Aucun reseau, aucun telechargement, aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.
