# Multi-Day Causal Feature Store V3.0

## Objectif

V3.0 construit uniquement un feature store OHLCV causal multi-day sur BTCUSDT du 2024-01-15 au 2024-01-21, a partir des OHLCV multi-day V2.9 valides.

## Inputs

- Source : OHLCV V2.9 `data/research/v2_9/silver/ohlcv`
- Timeframes : `1m`, `5m`, `15m`, `1h`
- Run : `v3_0_20260520T224737Z_0e30f8d6`

## Outputs

- `1m` : `10080` lignes, `data/research/v3_0/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-15_2024-01-21/features.parquet`
- `5m` : `2016` lignes, `data/research/v3_0/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-15_2024-01-21/features.parquet`
- `15m` : `672` lignes, `data/research/v3_0/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-15_2024-01-21/features.parquet`
- `1h` : `168` lignes, `data/research/v3_0/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-15_2024-01-21/features.parquet`

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

Les premieres lignes de chaque timeframe restent marquees `warmup_row = true` lorsque les lags ou rolling windows critiques ne sont pas encore disponibles. Les NaN de warmup ne sont pas remplis artificiellement.

## Qualite par timeframe

- `1m` : warmup `30`, lignes apres warmup `10050`, erreurs `0`
- `5m` : warmup `30`, lignes apres warmup `1986`, erreurs `0`
- `15m` : warmup `30`, lignes apres warmup `642`, erreurs `0`
- `1h` : warmup `30`, lignes apres warmup `138`, erreurs `0`

## Limitations

- V3.0 produit uniquement des features OHLCV causales multi-day sur BTCUSDT 2024-01-15 a 2024-01-21 a partir des donnees V2.9 validees.
- V3.0 ne produit aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.

## Securite

- V3.0 ne valide aucune stratégie
- V3.0 ne produit aucun label
- V3.0 ne produit aucun dataset ML
- V3.0 ne produit aucun modèle ML
- V3.0 ne produit aucun backtest
- V3.0 ne produit aucun signal de trading
- V3.0 ne produit aucun ordre
- V3.0 n’autorise aucun paper live
- V3.0 n’autorise aucun trading réel

V3.0 reste `pending_external_audit`.
