# Max Historical Clean Forward Label Factory V5.2

## Objectif

V5.2 construit uniquement des labels forward sur la fenetre historique continue validee par V5.0 : `2023-03-25` -> `2026-05-23`, soit `1156` jours.

## Inputs

- Source : OHLCV V5.0 `reports/manifests/max_history_public_market_data_v5_0_manifest.json`
- Timeframes : `1m`, `5m`, `15m`, `1h`
- Run : `v5_2_20260524T163028Z_089b9163`

## Outputs

- `1m` : `1664640` lignes, `data/research/v5_2/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2026-05-23/labels.parquet`
- `5m` : `332928` lignes, `data/research/v5_2/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2026-05-23/labels.parquet`
- `15m` : `110976` lignes, `data/research/v5_2/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2026-05-23/labels.parquet`
- `1h` : `27744` lignes, `data/research/v5_2/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2026-05-23/labels.parquet`

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

- Les labels regardent le futur uniquement dans la couche labels separee V5.2.
- Aucune jointure features + labels n'est produite.
- Aucun label n'est ecrit dans `data/research/v5_1/features`.
- Aucun dataset ML V5.2 n'est produit.
- Les dernieres lignes sans futur suffisant restent marquees invalides par horizon et `tail_row = true`.

## Qualite par timeframe

- `1m` : tail rows `5`, h1 `1664639`, h3 `1664637`, h5 `1664635`, erreurs `0`
- `5m` : tail rows `5`, h1 `332927`, h3 `332925`, h5 `332923`, erreurs `0`
- `15m` : tail rows `5`, h1 `110975`, h3 `110973`, h5 `110971`, erreurs `0`
- `1h` : tail rows `5`, h1 `27743`, h3 `27741`, h5 `27739`, erreurs `0`

## Limitations

- V5.2 produit uniquement des labels forward sur la fenetre historique continue validee par V5.0.
- V5.2 ne produit aucun dataset ML, aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

## Securite

- V5.2 ne valide aucune stratégie
- V5.2 ne produit aucun dataset ML
- V5.2 ne produit aucun modèle ML
- V5.2 ne produit aucun backtest
- V5.2 ne produit aucun signal de trading
- V5.2 ne produit aucun ordre
- V5.2 n’autorise aucun paper live
- V5.2 n’autorise aucun trading réel

V5.2 reste `pending_external_audit`.
