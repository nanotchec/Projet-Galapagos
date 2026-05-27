# V9.13 - H4 label candidate offline ML diagnostic

V9.13 entraine des baselines ML offline simples pour diagnostiquer le label h4. Les scores sont descriptifs, non actionnables et sans backtest.

- Decision ML : `h4_offline_ml_completed_but_close_to_shuffled_labels`.
- Decision globale : `h4_candidate_not_ready_refine_labels_again`.
- Target : `up_down_flat_volnorm_h4`.
- Features : `18`.

## Comparaison V9.8
- V9.8 no-clear shuffle : `14`.
- V9.13 no-clear shuffle : `14`.
- Distance shuffled amelioree : `True`.

## Outputs
- `1m` : `data/research/v9_13/ml/h4_label_candidate/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2024-03-24/ml-scores.parquet` (2106000 lignes).
- `5m` : `data/research/v9_13/ml/h4_label_candidate/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2024-03-24/ml-scores.parquet` (421008 lignes).
- `15m` : `data/research/v9_13/ml/h4_label_candidate/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2024-03-24/ml-scores.parquet` (140176 lignes).
- `1h` : `data/research/v9_13/ml/h4_label_candidate/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2024-03-24/ml-scores.parquet` (34864 lignes).

## Interdits maintenus
- Aucun backtest.
- Aucune strategie.
- Aucun signal actionnable.
- Aucun ordre.
- Aucun modele persistant.
- Aucun trading reel.
