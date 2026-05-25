# Feature Store OHLCV + Trades V7.2

## Objectif

V7.2 produit uniquement des features causales de recherche OHLCV + aggTrades sur la fenetre bornee V7.1.

## Fenetre

- Fenetre : `2023-03-25` -> `2023-04-23`.
- Total jours : `30`.
- Convention bougie/trades : `[event_ts, next_event_ts), equivalent to [event_ts, close_ts] for millisecond klines`.
- Source trades : `aggTrades`.

## Outputs

- `1m` : `data/research/v7_2/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2023-04-23/features.parquet`, `43200` lignes, checksum `3d868794252084bbce25b1f12a5f42dbb14b3ea19bd382d4fdc74080a3d374e4`
- `5m` : `data/research/v7_2/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2023-04-23/features.parquet`, `8640` lignes, checksum `2c216c4dddaaaf14d8f5d6881a4dfc5cead8c96ba97ba6746c2974c0dbecbd05`
- `15m` : `data/research/v7_2/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2023-04-23/features.parquet`, `2880` lignes, checksum `33302804c2debcda7e01f61f982c8d4c48a20e843b609aec2fdf5c772af7ed2f`
- `1h` : `data/research/v7_2/features/ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2023-04-23/features.parquet`, `720` lignes, checksum `ddd7ef3fab9f6d524eea6892378b0db7a5366c6dea46cf89bf7e8886bbaf7563`

## Qualite

- `1m` : warmup `60`, bougies sans trades `0`, diff volume mediane `0.0`, diff quote mediane `0.0`
- `5m` : warmup `60`, bougies sans trades `0`, diff volume mediane `0.0`, diff quote mediane `0.0`
- `15m` : warmup `60`, bougies sans trades `0`, diff volume mediane `0.0`, diff quote mediane `0.0`
- `1h` : warmup `60`, bougies sans trades `0`, diff volume mediane `0.0`, diff quote mediane `0.0`

## Limitations

- V7.2 produit uniquement des features causales OHLCV + aggTrades sur une fenetre bornee de 30 jours.
- V7.2 ne produit aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.

## Securite

V7.2 ne valide aucune strategie.
V7.2 ne produit aucun label.
V7.2 ne produit aucun dataset ML.
V7.2 ne produit aucun modele ML.
V7.2 ne produit aucun backtest.
V7.2 ne produit aucun signal de trading.
V7.2 ne produit aucun ordre.
V7.2 n'autorise aucun paper live.
V7.2 n'autorise aucun trading reel.
Les features trades sont des variables de recherche, pas des signaux.
