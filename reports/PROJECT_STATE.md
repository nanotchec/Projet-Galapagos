# Etat du Projet : V7.9 validee + candidat V8.0

- **Derniere version validee** : V7.9.
- **Version candidate** : V8.0.
- **Statut candidate** : `pending_external_audit`.
- **Direction** : OHLCV + public trades 90-day ML offline and robustness.

## Candidat V8.0

- Fenetre : `2023-03-25` -> `2023-06-22`.
- Nombre de jours : `90`.
- Feature columns count : `71`.
- Analyses : `['baseline_delta', 'feature_leakage_scan', 'label_shuffle_falsification', 'metric_forbidden_scan', 'ohlcv_trades_90d_vs_references_comparison', 'split_stability', 'timeframe_stability', 'walk_forward_stability']`.
- Warnings descriptifs : `8`.
- V8.0 reste candidate `pending_external_audit`.

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
- V8.0 reste non validee avant audit externe.
