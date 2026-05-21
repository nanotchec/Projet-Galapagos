# État du Projet : V3.2.1 validée + candidat V3.3

- **Dernière version validée** : V3.2.1.
- **Versions antérieures validées** : V3.1.10, V3.0, V2.9.1, V2.8.4, V2.7.2, V2.6.2, V2.5.2, V2.4.8, V2.3.1.
- **Version candidate** : V3.3.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : multi-day offline ML research baselines.

## Candidat V3.3

- V3.3 entraîne uniquement des baselines ML offline simples sur le dataset supervisé multi-day V3.2.1.
- Target unique : `up_down_flat_h1`.
- Modèles autorisés : `majority_class_baseline`, `random_seeded_baseline`, `logistic_regression`, `decision_tree_depth_2`.
- Scores research V3.3 : 1m `40196`, 5m `7940`, 15m `2564`, 1h `548`.
- Les features autorisées sont uniquement les features causales V3.0 présentes dans le dataset V3.2.
- Les métriques sont descriptives et non actionnables.
- Aucun modèle persistant n’est écrit.
- V3.3 ne produit aucun backtest, aucune stratégie, aucun signal de trading, aucun ordre et aucun trading réel.
- V3.3 reste candidate `pending_external_audit`.

## Clause De Sécurité

- Aucun trading réel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucune stratégie.
- Aucun modèle persistant.
- Aucune API privée.
- Aucune clé API.
- V3.3 reste non validée avant audit externe.
