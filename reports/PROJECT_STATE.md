# État du Projet : V4.5 validée + candidat V4.6

- **Dernière version validée** : V4.5.
- **Versions antérieures validées** : V4.5, V4.4, V4.3, V4.2, V4.1, V4.0.2, V4.0, V3.9, V3.8, V3.7, V3.6, V3.5.2, V3.4.1, V3.3.1, V3.2.1, V3.1.10, V3.0, V2.9.1, V2.8.4, V2.7.2, V2.6.2, V2.5.2, V2.4.8, V2.3.1.
- **Version candidate** : V4.6.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : baselines ML offline 1 an.

## Dernière Couche Validée

- V4.5 est validée par audit externe via audit-lite et attestation full locale.
- V4.5 assemble uniquement un dataset supervisé offline 1 an à partir des features V4.3 et labels V4.4 validés.
- Fenêtre : `2024-01-01` à `2024-12-31` inclus.
- Row counts datasets validés :
  - `1m` : 527040
  - `5m` : 105408
  - `15m` : 35136
  - `1h` : 8784
- Schéma strict : `DATASET_COLUMNS_V4_5`.
- Splits temporels validés : train, validation et test, sans shuffle.
- Aucun ML, modèle ML, backtest, stratégie, signal, ordre ou trading réel en V4.5.

## Candidat V4.6

- V4.6 entraîne uniquement des baselines ML offline simples sur le dataset V4.5 validé.
- Target unique : `up_down_flat_h1`.
- Modèles autorisés : `majority_class_baseline, random_seeded_baseline, logistic_regression, decision_tree_depth_2`.
- Features autorisées : `31` colonnes causales V4.3, sans `future_*`, `label_*`, `direction_*`, target ni split.
- Les scores sont écrits dans `data/research/v4_6/ml/offline_research` avec des colonnes `research_*`.
- Row counts scores :
  - `1m` : 2108036
  - `5m` : 421508
  - `15m` : 140420
  - `1h` : 35012
- V4.6 ne produit aucun modèle persistant, aucun backtest, aucune stratégie, aucun signal de trading et aucun ordre.
- V4.6 reste candidate `pending_external_audit`.

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
- V4.6 reste non validée avant audit externe.
