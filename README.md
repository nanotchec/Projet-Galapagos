# Projet Galapagos

- Derniere version validee : V9.42.
- Candidate : V9.43, ML offline OHLCV + aggTrades 5Y.
- Decision : offline_ml_5y_completed_but_close_to_shuffled_labels.
- ML offline execute sans modele persistant.
- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, reseau, telechargement, API privee ou cle API.

## V9.44 - 5Y ML Diagnostic / Feature & Label Review

- Diagnostic-only sur les sorties V9.43.
- Decision : `feature_enrichment_before_more_ml`.
- Recommandation : `V9.45 - AggTrades Exact Feature Enrichment`.
- Aucun reseau, aucun telechargement, aucun backtest, aucun walk-forward, aucune strategie, aucun signal actionnable.

## V9.45 - AggTrades Exact Feature Enrichment

- Decision : `aggtrades_exact_5y_feature_enrichment_partial`.
- Recommandation : `V9.46 - Exact Feature Enrichment Correction`.
- Feature-enrichment-only : aucun label, dataset supervise, ML, backtest, walk-forward, strategie ou signal.

## V9.46 - AggTrades Exact Feature Enrichment Validation

- Decision : `aggtrades_exact_5y_feature_enrichment_validated_with_non_blocking_warnings`.
- Recommandation : `V9.47 - Combine Base + Exact AggTrades Feature Store`.
- Validation-only : aucun feature store combine, label, dataset supervise, ML, backtest, walk-forward, strategie ou signal.
