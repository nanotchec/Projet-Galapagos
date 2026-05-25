# Feature Store OHLCV + Trades V7.8

## Objectif

V7.8 produit uniquement des features causales de recherche OHLCV + aggTrades sur la fenetre bornee V7.7.

## Fenetre

- Fenetre : `2023-03-25` -> `2023-06-22`.
- Total jours : `90`.
- Convention bougie/trades : `[event_ts, next_event_ts), equivalent to [event_ts, close_ts] for millisecond klines`.
- Source trades : `aggTrades`.

## Outputs

- `1m` : `data/research/v7_8/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2023-06-22/features.parquet`, `129600` lignes, checksum `2dbff7dae24a1218dedac115aab2a77afb6693a34b8fa354d35a55c826be6cec`
- `5m` : `data/research/v7_8/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2023-06-22/features.parquet`, `25920` lignes, checksum `8b3ac366e5139f6404cf211265e70e01a5737a52bc2fb63fbd6e64ac5aceca30`
- `15m` : `data/research/v7_8/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2023-06-22/features.parquet`, `8640` lignes, checksum `842c24e7ceccfbabb5657a4eb1d7952e966049b2e46fe066446fd0504426b772`
- `1h` : `data/research/v7_8/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2023-06-22/features.parquet`, `2160` lignes, checksum `44a42982dd046ba2123af6c433e010ba292c4e165447f090e7defe063c2c482f`

## Qualite

- `1m` : warmup `60`, bougies sans trades `0`, diff volume mediane `0.0`, diff quote mediane `0.0`
- `5m` : warmup `60`, bougies sans trades `0`, diff volume mediane `0.0`, diff quote mediane `0.0`
- `15m` : warmup `60`, bougies sans trades `0`, diff volume mediane `0.0`, diff quote mediane `0.0`
- `1h` : warmup `60`, bougies sans trades `0`, diff volume mediane `0.0`, diff quote mediane `0.0`

## Limitations

- V7.8 produit uniquement des features causales OHLCV + aggTrades sur une fenetre bornee de 90 jours.
- V7.8 ne produit aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.

## Securite

V7.8 ne valide aucune strategie.
V7.8 ne produit aucun label.
V7.8 ne produit aucun dataset ML.
V7.8 ne produit aucun modele ML.
V7.8 ne produit aucun backtest.
V7.8 ne produit aucun signal de trading.
V7.8 ne produit aucun ordre.
V7.8 n'autorise aucun paper live.
V7.8 n'autorise aucun trading reel.
Les features trades sont des variables de recherche, pas des signaux.
