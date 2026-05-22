# État du Projet : V3.8 validée + candidat V3.9

- **Dernière version validée** : V3.8.
- **Versions antérieures validées** : V3.7, V3.6, V3.5.2, V3.4.1, V3.3.1, V3.2.1, V3.1.10, V3.0, V2.9.1, V2.8.4, V2.7.2, V2.6.2, V2.5.2, V2.4.8, V2.3.1.
- **Version candidate** : V3.9.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : 90-day offline ML research baselines.

## Dernière Couche Validée

- V3.8 assemble un dataset supervisé offline 90 jours à partir des features V3.6 et labels V3.7 validés.
- Fenêtre : 2024-01-01 au 2024-03-30 inclus.
- Row counts dataset V3.8 : 1m `129600`, 5m `25920`, 15m `8640`, 1h `2160`.
- Schéma dataset : `DATASET_COLUMNS_V3_8` strict.
- Splits temporels train / validation / test sans shuffle.
- Aucun ML V3.8, aucun modèle V3.8, aucun backtest, aucune stratégie, aucun signal de trading, aucun ordre et aucun trading réel.

## Candidat V3.9

- V3.9 entraîne uniquement des baselines ML offline simples sur le dataset V3.8 validé.
- Cible unique : `up_down_flat_h1`.
- Modèles autorisés : `majority_class_baseline`, `random_seeded_baseline`, `logistic_regression`, `decision_tree_depth_2`.
- Outputs scores V3.9 : 1m `518276`, 5m `103556`, 15m `34436`, 1h `8516` lignes.
- Schéma scores : `ML_SCORE_COLUMNS_V3_9` strict.
- Les scores sont nommés `research_*` et restent descriptifs, non actionnables.
- Aucun modèle persistant, aucun backtest, aucune stratégie, aucun signal de trading, aucun ordre et aucun trading réel.
- V3.9 reste candidate `pending_external_audit`.

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
- V3.9 reste non validée avant audit externe.
