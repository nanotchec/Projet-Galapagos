# État du Projet : V3.9 validée + candidat V4.0

- **Dernière version validée** : V3.9.
- **Versions antérieures validées** : V3.8, V3.7, V3.6, V3.5.2, V3.4.1, V3.3.1, V3.2.1, V3.1.10, V3.0, V2.9.1, V2.8.4, V2.7.2, V2.6.2, V2.5.2, V2.4.8, V2.3.1.
- **Version candidate** : V4.0.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : 90-day ML robustness and falsification audit.

## Dernière Couche Validée

- V3.9 entraîne uniquement des baselines ML offline simples sur le dataset V3.8 validé.
- Cible unique : `up_down_flat_h1`.
- Modèles autorisés : `majority_class_baseline`, `random_seeded_baseline`, `logistic_regression`, `decision_tree_depth_2`.
- Scores nommés `research_*`.
- Métriques descriptives uniquement.
- Aucun backtest, aucune stratégie, aucun signal de trading, aucun ordre et aucun trading réel.

## Candidat V4.0

- V4.0 audite uniquement la robustesse descriptive et la falsification des résultats ML offline V3.9.
- Analyses produites : `baseline_delta`, `split_stability`, `timeframe_stability`, `label_shuffle_falsification`, `feature_leakage_scan`, `metric_forbidden_scan`.
- V4.0 ne produit aucun Parquet score, aucun modèle persistant, aucun backtest, aucune stratégie, aucun signal de trading, aucun ordre et aucun trading réel.
- V4.0 ne déclare aucune robustesse exploitable et ne valide aucune stratégie.
- V4.0 reste candidate `pending_external_audit`.

## Clause De Sécurité

- Aucun trading réel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucune stratégie.
- Aucun signal de trading.
- Aucun modèle persistant.
- Aucune API privée.
- Aucune clé API.
- V4.0 reste non validée avant audit externe.
