# V9.42 - OHLCV + AggTrades 5Y Dataset Validation

## Resume
- Mode : `full-local`.
- Decision V9.42 : `ohlcv_aggtrades_5y_dataset_validated`.
- Recommandation suivante : `V9.43 - OHLCV + AggTrades 5Y ML Offline`.
- Couverture : `target_5y_dataset_window_complete`.
- Schema : `PASS`.
- Qualite : `PASS`.
- Leakage guard : `PASS`.
- Forbidden columns scan : `PASS`.

## Counts
- `1m` : rows `2630880`, valides `2630395`, invalides `485`.
- `5m` : rows `526176`, valides `526104`, invalides `72`.
- `15m` : rows `175392`, valides `175328`, invalides `64`.
- `1h` : rows `43848`, valides `43787`, invalides `61`.

## Audit-lite
- Le mode audit-lite ne requiert pas les Parquets full.
- Les petits samples auditables sont separes des datasets full.

## Garde-fous
- Aucun ML, walk-forward, backtest, strategie, signal actionnable ou ordre.
- Aucun reseau, telechargement, suppression destructive, sidecar ou empreinte ZIP.
