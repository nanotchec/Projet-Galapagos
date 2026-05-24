# État du Projet : V4.6 validée + candidat V4.7

- **Dernière version validée** : V4.6.
- **Versions antérieures validées** : V4.6, V4.5, V4.4, V4.3, V4.2, V4.1, V4.0.2, V4.0, V3.9, V3.8, V3.7, V3.6, V3.5.2, V3.4.1, V3.3.1, V3.2.1, V3.1.10, V3.0, V2.9.1, V2.8.4, V2.7.2, V2.6.2, V2.5.2, V2.4.8, V2.3.1.
- **Version candidate** : V4.7.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : audit robustesse et falsification ML 1 an.

## Dernière Couche Validée

- V4.6 est validée par audit externe via audit-lite et attestation full locale.
- V4.6 entraîne uniquement des baselines ML offline simples sur le dataset supervisé 1 an V4.5 validé.
- Cible unique : `up_down_flat_h1`.
- Modèles autorisés : `majority_class_baseline`, `random_seeded_baseline`, `logistic_regression`, `decision_tree_depth_2`.
- Scores nommés `research_*` uniquement.
- Row counts scores validés :
  - `1m` : 2108036
  - `5m` : 421508
  - `15m` : 140420
  - `1h` : 35012
- Aucun backtest, aucune stratégie, aucun signal, aucun ordre, aucun trading réel et aucun modèle persistant en V4.6.

## Candidat V4.7

- V4.7 audite uniquement la robustesse descriptive et la falsification des résultats ML offline V4.6 sur 1 an.
- Analyses produites : `baseline_delta, split_stability, timeframe_stability, label_shuffle_falsification, feature_leakage_scan, metric_forbidden_scan`.
- Warnings descriptifs : `8`.
- `robust_edge_claimed` : `false`.
- `strategy_validated` : `false`.
- `backtest_performed` : `false`.
- `actionable_signal_produced` : `false`.
- Le scan de fuite features ne détecte aucune feature interdite.
- Le scan des métriques ne détecte aucun Sharpe, drawdown, PnL, equity curve, win rate trading ou profit factor.
- V4.7 ne crée aucun score Parquet, aucun modèle, aucun backtest, aucune stratégie, aucun signal de trading et aucun ordre.
- V4.7 reste candidate `pending_external_audit`.

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
- V4.7 reste non validée avant audit externe.
