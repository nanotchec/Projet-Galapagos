# Rapport qualite V9.1 - Dataset supervise raffine OHLCV + trades

V9.1 assemble uniquement un dataset supervise offline a partir des features raffinees V9.0 et des labels V5.2 filtres sur la meme fenetre.
V9.1 ne valide aucune strategie, ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

## Fenetre

- Debut : `2023-03-25`.
- Fin : `2024-03-24`.
- Total jours : `366`.

## Sorties

### 1m

- Dataset : `data/research/v9_1/datasets/refined_offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2024-03-24/dataset.parquet`.
- Rows : `527040`.
- Split counts : `{'train': 316224, 'validation': 105408, 'test': 105408}`.
- Warmup rows : `60`.
- Tail rows : `0`.
- Errors : `[]`.
- Warnings : `[]`.

### 5m

- Dataset : `data/research/v9_1/datasets/refined_offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2024-03-24/dataset.parquet`.
- Rows : `105408`.
- Split counts : `{'train': 63244, 'validation': 21082, 'test': 21082}`.
- Warmup rows : `60`.
- Tail rows : `0`.
- Errors : `[]`.
- Warnings : `[]`.

### 15m

- Dataset : `data/research/v9_1/datasets/refined_offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2024-03-24/dataset.parquet`.
- Rows : `35136`.
- Split counts : `{'train': 21081, 'validation': 7027, 'test': 7028}`.
- Warmup rows : `60`.
- Tail rows : `0`.
- Errors : `[]`.
- Warnings : `[]`.

### 1h

- Dataset : `data/research/v9_1/datasets/refined_offline_supervised_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2024-03-24/dataset.parquet`.
- Rows : `8784`.
- Split counts : `{'train': 5270, 'validation': 1757, 'test': 1757}`.
- Warmup rows : `60`.
- Tail rows : `0`.
- Errors : `[]`.
- Warnings : `[]`.

## Interdits maintenus

- Aucun backtest.
- Aucune strategie.
- Aucun signal de trading.
- Aucun ordre.
- Aucun paper live.
- Aucun trading reel.

V9.1 reste une etape de dataset offline non validee avant audit externe.
