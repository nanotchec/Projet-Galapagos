# V9.62 - Funding common window ML offline

V9.62 execute un diagnostic ML offline research-only comparant OHLCV + aggTrades exact sans funding et avec funding sur la meme fenetre commune.

- Decision : `funding_common_window_ml_completed_but_class_collapse`.
- Target : `up_down_flat_volnorm_h1_5y`.
- Modeles executes : `majority_class_baseline, random_seeded_baseline, logistic_regression, decision_tree_depth_2`.
- Qualite : `PASS`.
- Leakage guard : `PASS`.
- Clear improvements funding : `0`.
- No-clear vs shuffled labels : `28`.

## Synthese par timeframe
- `1m` : `2622715` lignes valides ML.
- `5m` : `524568` lignes valides ML.
- `15m` : `174816` lignes valides ML.
- `1h` : `43659` lignes valides ML.

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
- Aucun resultat actionnable.
