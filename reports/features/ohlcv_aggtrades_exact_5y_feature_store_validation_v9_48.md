# V9.48 - Validation feature store combine 5Y

- Decision : `combined_feature_store_validated_with_warnings`.
- Recommandation : `V9.49 - Combined Features 5Y Dataset`.
- Qualite : `PASS`.
- Coverage : `target_5y_combined_feature_window_complete`.
- Leakage guard : `PASS`.
- Colonnes combinees : `97`.
- Row counts : `{'1m': 2630880, '5m': 526176, '15m': 175392, '1h': 43848}`.

Aucun label, dataset supervise, ML, backtest, walk-forward, strategie ou signal n'est cree.

## Warnings
- 15m: warmup rows contain documented rolling-window nulls
- 1h: warmup rows contain documented rolling-window nulls
- 1m: warmup rows contain documented rolling-window nulls
- 5m: warmup rows contain documented rolling-window nulls
