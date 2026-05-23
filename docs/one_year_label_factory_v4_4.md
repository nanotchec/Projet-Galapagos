# One-Year Clean Forward Label Factory V4.4

## Objectif

V4.4 construit uniquement des labels forward 1 an sur BTCUSDT du 2024-01-01 au 2024-12-31, a partir des OHLCV V4.2 valides.

## Inputs

- Source : OHLCV V4.2 `data/research/v4_2/silver/ohlcv`
- Timeframes : `1m`, `5m`, `15m`, `1h`
- Run : `v4_4_20260523T011106Z_914b02ec`

## Outputs

- `1m` : `527040` lignes, `data/research/v4_4/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-01_2024-12-31/labels.parquet`
- `5m` : `105408` lignes, `data/research/v4_4/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-01_2024-12-31/labels.parquet`
- `15m` : `35136` lignes, `data/research/v4_4/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-01_2024-12-31/labels.parquet`
- `1h` : `8784` lignes, `data/research/v4_4/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-01_2024-12-31/labels.parquet`

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

- Les labels regardent le futur uniquement dans la couche labels separee V4.4.
- Aucune jointure features + labels n'est produite.
- Aucun label n'est ecrit dans `data/research/v4_3/features`.
- Aucun dataset ML V4.4 n'est produit.
- Les dernieres lignes sans futur suffisant restent marquees invalides par horizon et `tail_row = true`.

## Qualite par timeframe

- `1m` : tail rows `5`, h1 `527039`, h3 `527037`, h5 `527035`, erreurs `0`
- `5m` : tail rows `5`, h1 `105407`, h3 `105405`, h5 `105403`, erreurs `0`
- `15m` : tail rows `5`, h1 `35135`, h3 `35133`, h5 `35131`, erreurs `0`
- `1h` : tail rows `5`, h1 `8783`, h3 `8781`, h5 `8779`, erreurs `0`

## Limitations

- V4.4 produit uniquement des labels forward 1 an separes sur BTCUSDT 2024-01-01 a 2024-12-31 a partir des donnees OHLCV V4.2 validees.
- V4.4 ne produit aucun dataset ML, aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

## Securite

- V4.4 ne valide aucune stratégie
- V4.4 ne produit aucun dataset ML
- V4.4 ne produit aucun modèle ML
- V4.4 ne produit aucun backtest
- V4.4 ne produit aucun signal de trading
- V4.4 ne produit aucun ordre
- V4.4 n’autorise aucun paper live
- V4.4 n’autorise aucun trading réel

V4.4 reste `pending_external_audit`.
