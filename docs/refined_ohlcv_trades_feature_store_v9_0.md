# Refined OHLCV + trades feature store V9.0

V9.0 produit une feature store raffinee a partir de V8.3 et de la selection V8.9.

- Selected features : `18`.
- Fenetre : `2023-03-25` -> `2024-03-24`.

## Outputs

- `1m` : `527040` lignes, `data/research/v9_0/features/refined_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2024-03-24/features.parquet`.
- `5m` : `105408` lignes, `data/research/v9_0/features/refined_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2024-03-24/features.parquet`.
- `15m` : `35136` lignes, `data/research/v9_0/features/refined_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2024-03-24/features.parquet`.
- `1h` : `8784` lignes, `data/research/v9_0/features/refined_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2024-03-24/features.parquet`.

## Securite

- V9.0 ne produit aucun label.
- V9.0 ne produit aucun dataset ML.
- V9.0 ne produit aucun modele ML.
- V9.0 ne produit aucun backtest.
- V9.0 ne produit aucune strategie.
- V9.0 ne produit aucun signal de trading.
- V9.0 ne produit aucun ordre.
- V9.0 n'autorise aucun paper live ni trading reel.
