# Etat du Projet : V7.3 validee + candidat V7.4

- **Derniere version validee** : V7.3.
- **Version candidate** : V7.4.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : OHLCV + public trades offline ML research baselines.

## Candidat V7.4

- Fenetre V7.3 utilisee : `2023-03-25` -> `2023-04-23`.
- Nombre de jours : `30`.
- Row counts scores : `{'1m': 172560, '5m': 34320, '15m': 11280, '1h': 2640}`.
- Schema : `ML_SCORE_COLUMNS_V7_4`.
- Cible : `up_down_flat_h1`.
- Feature columns ML : `71`.
- Modeles offline autorises : `['majority_class_baseline', 'random_seeded_baseline', 'logistic_regression', 'decision_tree_depth_2']`.
- Metriques walk-forward : descriptives uniquement, pas un backtest.
- Comparaisons V7.4 vs V6.2/V5.4 : descriptives uniquement, non actionnables et non directement comparables si les fenetres different.
- V7.4 reste candidate `pending_external_audit`.

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
- V7.4 reste non validee avant audit externe.
