# Datacard V9.40 - Labels OHLCV + AggTrades 5Y

- Fenetre : `2021-05-05` -> `2026-05-05`.
- Timeframes : `1m, 5m, 15m, 1h`.
- Label principal candidat : `up_down_flat_volnorm_h1_5y`.
- Horizons produits : h4 volnorm, h1 volnorm, binaire directionnel h4.
- Volatilite causale : `rolling_volatility_60` issue de la feature store, disponible a `decision_ts`.
- `label_available_ts` est strictement posterieur a `decision_ts` pour les labels valides.
- Usage interdit dans V9.40 : dataset supervise, ML, walk-forward, backtest, strategie, signal, ordre.
