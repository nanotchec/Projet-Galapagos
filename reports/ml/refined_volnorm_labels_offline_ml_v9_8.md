# V9.8 - ML offline avec labels volatility-normalized

V9.8 entraine des baselines ML offline simples. Les scores sont descriptifs, non actionnables et sans backtest.

- Decision : `offline_ml_completed_but_close_to_shuffled_labels`.
- Cible : `up_down_flat_volnorm_h1`.
- Features : `18`.

## Outputs
- `1m` : `data/research/v9_8/ml/refined_volnorm_labels/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2024-03-24/ml-scores.parquet` (2107920 lignes).
- `5m` : `data/research/v9_8/ml/refined_volnorm_labels/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2024-03-24/ml-scores.parquet` (421392 lignes).
- `15m` : `data/research/v9_8/ml/refined_volnorm_labels/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2024-03-24/ml-scores.parquet` (140304 lignes).
- `1h` : `data/research/v9_8/ml/refined_volnorm_labels/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2024-03-24/ml-scores.parquet` (34896 lignes).

## Interdits maintenus

- Aucun backtest.
- Aucune strategie.
- Aucun signal actionnable.
- Aucun ordre.
- Aucun modele persistant.
- Aucun trading reel.
