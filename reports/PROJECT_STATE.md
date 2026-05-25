# Etat du Projet : V8.4 validee + candidat V8.5

- **Derniere version validee** : V8.4.
- **Version candidate** : V8.5.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : OHLCV + public trades offline ML research baselines.

## Candidat V8.5

- Fenetre V8.4 utilisee : `2023-03-25` -> `2024-03-24`.
- Nombre de jours : `366`.
- Row counts scores : `{'1m': 2107920, '5m': 421392, '15m': 140304, '1h': 34896}`.
- Schema : `ML_SCORE_COLUMNS_V8_5`.
- Cible : `up_down_flat_h1`.
- Feature columns ML : `71`.
- Modeles offline autorises : `['majority_class_baseline', 'random_seeded_baseline', 'logistic_regression', 'decision_tree_depth_2']`.
- Metriques walk-forward : descriptives uniquement, pas un backtest.
- Comparaisons V8.5 vs V8.0/V7.4/V6.2/V5.4 : descriptives uniquement, non actionnables et non directement comparables si les fenetres different.
- V8.5 reste candidate `pending_external_audit`.

## Clause De Securite

- Aucun trading reel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucune strategie.
- Aucun signal de trading.
- Aucun modele persistant.
- Aucune API privee.
- Aucune cle API.
- V8.5 reste non validee avant audit externe.
