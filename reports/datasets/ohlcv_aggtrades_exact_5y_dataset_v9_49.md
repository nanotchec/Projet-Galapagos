# V9.49 - OHLCV + AggTrades 5Y Dataset

## Resume
- Decision V9.49 : `combined_features_5y_dataset_created`.
- Recommandation suivante : `V9.50 - Combined Features 5Y Dataset Validation`.
- Dataset cree : `True`.
- Target : `up_down_flat_volnorm_h1_5y`.
- Qualite : `PASS`.
- Couverture : `target_5y_dataset_window_complete`.
- Leakage guard : `PASS`.
- Forbidden columns scan : `PASS`.

## Readiness
- Features combinees V9.47/V9.48 : `True`.
- Labels V9.40 : `True`.

## Lignes par timeframe
- `1m` : rows `2630880`, valides `2630395`, invalides `485`.
- `5m` : rows `526176`, valides `526104`, invalides `72`.
- `15m` : rows `175392`, valides `175328`, invalides `64`.
- `1h` : rows `43848`, valides `43787`, invalides `61`.

## Splits
- Les splits sont inclus dans `dataset.parquet`.
- Split temporel sans shuffle : train 60 %, validation 20 %, test 20 %.
- `walk_forward_group = calendar_month`; `purge_embargo_group = none_v9_49_preview`.

## Garde-fous
- Aucun ML, walk-forward, backtest, strategie, signal actionnable ou ordre.
- Aucun reseau, telechargement, suppression destructive, sidecar ou empreinte ZIP.
