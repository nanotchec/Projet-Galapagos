# V9.51 - OHLCV + AggTrades 5Y ML offline

V9.51 execute un diagnostic ML offline research-only sur le dataset V9.49 valide par V9.50.

- Decision : `combined_features_5y_ml_completed_but_class_collapse`.
- Target : `up_down_flat_volnorm_h1_5y`.
- Features utilisees : `97`.
- Modeles executes : `majority_class_baseline, random_seeded_baseline, logistic_regression, decision_tree_depth_2`.
- Qualite : `PASS`.
- Leakage guard : `PASS`.
- No-clear vs shuffled labels : `10`.

## Synthese par timeframe
- `1m` : `2630395` lignes valides ML.
- `5m` : `526104` lignes valides ML.
- `15m` : `175328` lignes valides ML.
- `1h` : `43787` lignes valides ML.

## Garde-fous
- Aucun trading reel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucun walk-forward.
- Aucune strategie.
- Aucun signal actionnable.
- Aucun modele persistant.
- Aucun reseau et aucun telechargement.
