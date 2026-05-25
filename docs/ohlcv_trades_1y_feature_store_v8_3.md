# Feature Store OHLCV + Trades V8.3

## Objectif

V8.3 produit uniquement des features causales de recherche OHLCV + aggTrades sur la fenetre bornee V8.2.

## Fenetre

- Fenetre : `2023-03-25` -> `2024-03-24`.
- Total jours : `366`.
- Convention bougie/trades : `[event_ts, next_event_ts), equivalent to [event_ts, close_ts] for millisecond klines`.
- Source trades : `aggTrades`.

## Outputs

- `1m` : `data/research/v8_3/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2024-03-24/features.parquet`, `527040` lignes, checksum `3f2b83a9650e639da3d6fc21eab7b943fea25c57f423f966c7a1f98369de6fbe`
- `5m` : `data/research/v8_3/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2024-03-24/features.parquet`, `105408` lignes, checksum `1b2a6e5b1da051bb7bd366c42de7e7bfecbbd767b068190aeb99672bd9c0db95`
- `15m` : `data/research/v8_3/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2024-03-24/features.parquet`, `35136` lignes, checksum `e852aa57bc5dafeff062b94b2e89e0ee8dcf1e4a18395015d90e90b427bddcae`
- `1h` : `data/research/v8_3/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2024-03-24/features.parquet`, `8784` lignes, checksum `7cc77b76aaeefa0777dea8994d964f5699dbf87159693015d9f21de43d71d7a9`

## Qualite

- `1m` : warmup `60`, bougies sans trades `0`, diff volume mediane `0.0`, diff quote mediane `0.0`
- `5m` : warmup `60`, bougies sans trades `0`, diff volume mediane `0.0`, diff quote mediane `0.0`
- `15m` : warmup `60`, bougies sans trades `0`, diff volume mediane `0.0`, diff quote mediane `0.0`
- `1h` : warmup `60`, bougies sans trades `0`, diff volume mediane `0.0`, diff quote mediane `0.0`

## Limitations

- V8.3 produit uniquement des features causales OHLCV + aggTrades sur une fenetre d'environ 1 an.
- V8.3 ne produit aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.

## Securite

V8.3 ne valide aucune strategie.
V8.3 ne produit aucun label.
V8.3 ne produit aucun dataset ML.
V8.3 ne produit aucun modele ML.
V8.3 ne produit aucun backtest.
V8.3 ne produit aucun signal de trading.
V8.3 ne produit aucun ordre.
V8.3 n'autorise aucun paper live.
V8.3 n'autorise aucun trading reel.
Les features trades sont des variables de recherche, pas des signaux.
