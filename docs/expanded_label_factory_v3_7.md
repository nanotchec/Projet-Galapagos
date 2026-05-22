# Expanded Clean Forward Label Factory V3.7

## Objectif

V3.7 construit uniquement des labels forward 90 jours sur BTCUSDT du 2024-01-01 au 2024-03-30, a partir des OHLCV V3.5 valides.

## Inputs

- Source : OHLCV V3.5 `data/research/v3_5/silver/ohlcv`
- Timeframes : `1m`, `5m`, `15m`, `1h`
- Run : `v3_7_20260522T132344Z_71604810`

## Outputs

- `1m` : `129600` lignes, `data/research/v3_7/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-01_2024-03-30/labels.parquet`
- `5m` : `25920` lignes, `data/research/v3_7/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-01_2024-03-30/labels.parquet`
- `15m` : `8640` lignes, `data/research/v3_7/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-01_2024-03-30/labels.parquet`
- `1h` : `2160` lignes, `data/research/v3_7/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-01_2024-03-30/labels.parquet`

## Horizons et threshold

- Horizons : `[1, 3, 5]`
- Threshold fixe : `0.0005`

## Definition des labels

- `future_close_h` = `close.shift(-h)`.
- `future_simple_return_h` = `future_close_h / close - 1`.
- `future_log_return_h` = `log(future_close_h / close)`.
- `direction_h` vaut `1`, `-1` ou `0` selon le signe du log return.
- `up_down_flat_h` vaut `UP`, `DOWN` ou `FLAT` avec le threshold fixe.
- `label_available_ts` est strictement posterieur a `decision_ts` pour les lignes avec au moins un label valide.

## Colonnes

- `source`
- `venue`
- `market_type`
- `symbol`
- `timeframe`
- `event_ts`
- `close_ts`
- `available_ts`
- `decision_ts`
- `label_available_ts`
- `label_run_id`
- `source_ohlcv_sha256`
- `label_schema_version`
- `future_close_h1`
- `future_log_return_h1`
- `future_simple_return_h1`
- `direction_h1`
- `up_down_flat_h1`
- `label_end_ts_h1`
- `label_valid_h1`
- `future_close_h3`
- `future_log_return_h3`
- `future_simple_return_h3`
- `direction_h3`
- `up_down_flat_h3`
- `label_end_ts_h3`
- `label_valid_h3`
- `future_close_h5`
- `future_log_return_h5`
- `future_simple_return_h5`
- `direction_h5`
- `up_down_flat_h5`
- `label_end_ts_h5`
- `label_valid_h5`
- `label_null_count`
- `label_error_count`
- `tail_row`

## Regles anti-leakage

- Les labels regardent le futur uniquement dans la couche labels separee V3.7.
- Aucune jointure features + labels n'est produite.
- Aucun label n'est ecrit dans `data/research/v3_6/features`.
- Aucun dataset ML V3.7 n'est produit.
- Les dernieres lignes sans futur suffisant restent marquees invalides par horizon et `tail_row = true`.

## Qualite par timeframe

- `1m` : tail rows `5`, h1 `129599`, h3 `129597`, h5 `129595`, erreurs `0`
- `5m` : tail rows `5`, h1 `25919`, h3 `25917`, h5 `25915`, erreurs `0`
- `15m` : tail rows `5`, h1 `8639`, h3 `8637`, h5 `8635`, erreurs `0`
- `1h` : tail rows `5`, h1 `2159`, h3 `2157`, h5 `2155`, erreurs `0`

## Limitations

- V3.7 produit uniquement des labels forward 90 jours separes sur BTCUSDT 2024-01-01 a 2024-03-30 a partir des donnees OHLCV V3.5 validees.
- V3.7 ne produit aucun dataset ML, aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

## Securite

- V3.7 ne valide aucune stratégie
- V3.7 ne produit aucun dataset ML
- V3.7 ne produit aucun modèle ML
- V3.7 ne produit aucun backtest
- V3.7 ne produit aucun signal de trading
- V3.7 ne produit aucun ordre
- V3.7 n’autorise aucun paper live
- V3.7 n’autorise aucun trading réel

V3.7 reste `pending_external_audit`.
