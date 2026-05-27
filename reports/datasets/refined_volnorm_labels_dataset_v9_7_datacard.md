# V9.7 - Dataset raffine avec labels volatility-normalized

V9.7 assemble un dataset supervise offline. Il ne produit aucun ML, backtest, strategie, signal actionnable ou ordre.

- Decision : `dataset_created_with_volnorm_labels`.
- Cible : `up_down_flat_volnorm_h1`.

## Outputs

- `1m` : `data/research/v9_7/datasets/refined_volnorm_labels/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2024-03-24/dataset.parquet` avec `527040` lignes, labels valides `526980`.
- `5m` : `data/research/v9_7/datasets/refined_volnorm_labels/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2024-03-24/dataset.parquet` avec `105408` lignes, labels valides `105348`.
- `15m` : `data/research/v9_7/datasets/refined_volnorm_labels/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2024-03-24/dataset.parquet` avec `35136` lignes, labels valides `35076`.
- `1h` : `data/research/v9_7/datasets/refined_volnorm_labels/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2024-03-24/dataset.parquet` avec `8784` lignes, labels valides `8724`.

## Interdits maintenus

- Aucun backtest.
- Aucune strategie.
- Aucun signal actionnable.
- Aucun ordre.
- Aucun paper live.
- Aucun trading reel.
