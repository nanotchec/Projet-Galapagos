# Etat du Projet : V6.1 validee + candidat V6.2

- **Derniere version validee** : V6.1.
- **Version candidate** : V6.2.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : max historical offline ML with advanced OHLCV features.

## Candidat V6.2

- Fenetre V5.0 utilisee : `2023-03-25` -> `2026-05-23`.
- Nombre de jours : `1156`.
- Row counts scores : `{'1m': 6657492, '5m': 1330752, '15m': 442944, '1h': 110016}`.
- Schema : `ML_SCORE_COLUMNS_V6_2`.
- Cible : `up_down_flat_h1`.
- Advanced feature columns : `158`.
- Modeles offline autorises : `['majority_class_baseline', 'random_seeded_baseline', 'logistic_regression', 'decision_tree_depth_2']`.
- Metriques walk-forward : descriptives uniquement, pas un backtest.
- Comparaison V6.2 vs V5.4 : descriptive uniquement, non actionnable.
- V6.2 reste candidate `pending_external_audit`.

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
- V6.2 reste non validee avant audit externe.
