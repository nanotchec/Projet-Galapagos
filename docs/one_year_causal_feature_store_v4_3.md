# One-Year Causal Feature Store V4.3

## Objectif

V4.3 construit uniquement un feature store OHLCV causal 1 an sur BTCUSDT du 2024-01-01 au 2024-12-31, a partir des OHLCV V4.2 valides.

## Inputs

- Source : OHLCV V4.2 `data/research/v4_2/silver/ohlcv`
- Timeframes : `1m`, `5m`, `15m`, `1h`
- Run : `v4_3_20260522T233930Z_627dcaa9`

## Outputs

- `1m` : `527040` lignes, `data/research/v4_3/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-01_2024-12-31/features.parquet`
- `5m` : `105408` lignes, `data/research/v4_3/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-01_2024-12-31/features.parquet`
- `15m` : `35136` lignes, `data/research/v4_3/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-01_2024-12-31/features.parquet`
- `1h` : `8784` lignes, `data/research/v4_3/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-01_2024-12-31/features.parquet`

## Features calculees

- `source`
- `venue`
- `market_type`
- `symbol`
- `timeframe`
- `event_ts`
- `close_ts`
- `available_ts`
- `decision_ts`
- `feature_available_ts`
- `ingested_at_ts`
- `feature_run_id`
- `source_ohlcv_sha256`
- `feature_schema_version`
- `close_lag_1`
- `return_1`
- `log_return_1`
- `return_3`
- `log_return_3`
- `return_5`
- `log_return_5`
- `rolling_vol_5`
- `rolling_vol_15`
- `rolling_vol_30`
- `candle_range`
- `candle_body`
- `upper_wick`
- `lower_wick`
- `close_position_in_range`
- `volume_lag_1`
- `volume_return_1`
- `rolling_volume_mean_5`
- `rolling_volume_mean_15`
- `rolling_volume_zscore_15`
- `sma_5`
- `sma_15`
- `sma_30`
- `close_to_sma_5`
- `close_to_sma_15`
- `close_to_sma_30`
- `hour_utc`
- `day_of_week_utc`
- `is_weekend_utc`
- `warmup_row`
- `feature_null_count`
- `feature_error_count`

## Regles causales

- Les lags et rolling windows utilisent uniquement les observations passees ou courantes.
- Aucun `future_return`, label, target, prediction, signal, order, pnl ou backtest n'est produit.
- `feature_available_ts = available_ts` pour cette preview.
- `decision_ts >= feature_available_ts` est verifie physiquement.

## Warmup

Les 30 premieres lignes de chaque timeframe restent marquees `warmup_row = true` lorsque les lags ou rolling windows critiques ne sont pas encore disponibles. Les NaN de warmup ne sont pas remplis artificiellement.

## Qualite par timeframe

- `1m` : warmup `30`, lignes apres warmup `527010`, erreurs `0`
- `5m` : warmup `30`, lignes apres warmup `105378`, erreurs `0`
- `15m` : warmup `30`, lignes apres warmup `35106`, erreurs `0`
- `1h` : warmup `30`, lignes apres warmup `8754`, erreurs `0`

## Limitations

- V4.3 produit uniquement des features OHLCV causales sur BTCUSDT 2024-01-01 a 2024-12-31 a partir des donnees V4.2 validees.
- V4.3 ne produit aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.

## Securite

- V4.3 ne valide aucune stratégie
- V4.3 ne produit aucun label
- V4.3 ne produit aucun dataset ML
- V4.3 ne produit aucun modèle ML
- V4.3 ne produit aucun backtest
- V4.3 ne produit aucun signal de trading
- V4.3 ne produit aucun ordre
- V4.3 n’autorise aucun paper live
- V4.3 n’autorise aucun trading réel

V4.3 reste `pending_external_audit`.
